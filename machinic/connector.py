#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import zerorpc
import types
import importlib
from lings.routeling import add_route,find_route
from cmd2 import Cmd
import argparse
import sys
import copy
from functools import wraps,partialmethod
import uuid
import os
from logzero import logger
import attr
import consul
import inspect
import logzero
import textwrap
try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    print(ex)

def add_self(f):
    """Add a wrapper to accept self for nonbound functions
    """
    @wraps(f)
    def wrapped(self, *f_args, **f_kwargs):
        print(inspect.getfullargspec(f))
        return f(*f_args,**f_kwargs)
    return wrapped


def wrap(to_wrap):
    """dynamically add attributes to class instance to expose for rpc
    """
    rpcw = RpcWrapper()
    for f in to_wrap:
        print("adding ",f)
        # Problem: function signature is not correct
        # zerorpc shows only: [{'name': 'self'}]
        # wrapt module may be solution instead of wraps
        setattr(rpcw, f, types.MethodType(add_self(globals()[f]), rpcw ))

    return rpcw

class RpcWrapper(object):
    """Container object for zerorpc, services(functions) are provided
    as a list and dynamically added.
    """

class CmdLineApp(Cmd):
    """Given a host and port attempts to connect as client to zerorpc
    server. On connection gets list of remote services and dynamically
    generates attributes to allow tab completion.
    """
    def __init__(self, host,port):
        #disable,otherwise argparse parsers in main() will interact poorly
        self.allow_cli_args = False
        self.redirector = '--->'
        self.allow_redirection = False
        self.host = host
        self.port = port
        zc = zerorpc.Client()
        zc.connect("tcp://{}:{}".format(self.host,self.port))
        self.client = zc
        #get list of available services from zerorpc
        results = zc._zerorpc_inspect()
        print(results)

        for method in results['methods'].keys():
            #create a method to enable tab completion and pass in method name
            #for rpc call since cmd2 will chomp first string
            f = partialmethod(self._generic,method)
            #setattr(CmdLineApp,'do_'+method,f)
            setattr(CmdLineApp,'do_'+method, f)            
        Cmd.__init__(self)

    def _generic(self,arg,method,*args):
        #TODO arg is being replaced by self due to partial
        print(self,arg,method,args)
        #cmd was sending an empty arg ('',)
        #which was causing signature errors for rpc function
        args = list(filter(None, args))
        print(self,arg,method,args)
        #args not being correctly parsed?
        #all are being passed as stirng in list
        try:
            args=args[0].split(" ")
        except:
            pass
        print(self,arg,method,args)
        result = getattr(self.client, method)(*args)
        print(result)

def cmdline_repl(host,port):
    """REPL interface to tools using cmd2

        Args:
            host(str): host address of servre for client
            port(str): port of server for client
    """
    c = CmdLineApp(host,port)
    c.cmdloop()

@attr.s
class ServiceLookup():
    service =  attr.ib()
    ip = attr.ib()
    port = attr.ib()
    errors = attr.ib(default=attr.Factory(list))

    @property
    def pretty(self):
        """return ip:port for templates
        """
        return "{ip}:{port}".format(ip=self.ip,port=self.port)

def list_services(service_name=None,return_format='stdout'):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    if service_name is None:
        if return_format == 'stdout':
            for k in services.keys():
                print("{}\t{}\t{}".format(services[k]['Service'].ljust(15),services[k]['Address'],services[k]['Port']))
        elif return_format == list:
            service_objs = []
            for k in services.keys():
                service_objs.append(ServiceLookup(services[k]['Service'],services[k]['Address'],services[k]['Port']))
            return service_objs
    else:
        for k in services.keys():
            if services[k]['Service'] == service_name:
                return ServiceLookup(services[k]['Service'],services[k]['Address'],services[k]['Port'])
        return None


def main():
    """TODO docstring with argparse?
    """
    tutorial_string = textwrap.dedent("""
    Usage:

        Display discoverable services:

        $ python3 connector.py status

        Get a cmd2 prompt on a zerorpc server, connecting by name(for generated services):

        $ python3 connector.py cli -s zerorpc-tools

        Start a zerorpc server by wrapping a file:

        $ python3 connector.py server --service-file tools.py --host 127.0.0.1 --port 4242

        Connect to a zerorpc server with cmd2 prompt:

        $ python3 connector.py cli --host 127.0.0.1 --port 4242



        Notes:

        Connector.py is typically used to wrap files by
        using xml in a machine file:

            <include file = "tools.py" name = "tools" rpc = "true" wireup = "true" />

        Security:

        This method of import everything is not recommended by zerorpc devs
        and exposes more python functions than necessary(ie python os module
        becomes available for rpc).
        Check firewall rules...
        Suggestions on this issue welcomed...

    """)
    parser = argparse.ArgumentParser(description=tutorial_string,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", help="server|cli|status", choices=['server','cli','status'])
    parser.add_argument("-s", "--service",help="connect <service> via lookup",required=False)
    parser.add_argument("--service-file",nargs='+',help="server",required=False,default=[])
    parser.add_argument("--service-class", help="class from file containing functions to serve via rpc")
    parser.add_argument("--host", help="host ip",default="127.0.0.1", required=False)
    parser.add_argument("-p", "--port", help="port number",default="4242", required=False)

    args = parser.parse_args()
    print(args)
    print(args.mode)

    if args.mode == 'server':
        if args.service_class:
            module_class = None
            for f in args.service_file:
                #add path for loading python files from different
                path = os.path.dirname(os.path.abspath(f))
                sys.path.insert(0, path)
                logger.info("Added {} to sys.path".format(f))

                if f.endswith('.py'):
                    f = os.path.basename(f)
                    f = f[:-3]
                    logger.info("Using {} to load as module".format(f))
                try:
                    module = importlib.import_module(f)
                    module_class = args.service_class
                except Exception as ex:
                    logger.error(ex)

            # load class from module using string
            module_to_load = getattr(module, module_class)
            logger.info("Using {} to load as class".format(module_class))
            
            s = zerorpc.Server(module_to_load(), heartbeat=60)
            bind_address = "tcp://{host}:{port}".format(host=args.host,port=args.port)
            logger.info("binding server to: {}".format(bind_address))
            s.bind(bind_address)
            logger.info("running...")
            s.run()
        else:
            services = []
            for f in args.service_file:
                #add path for loading python files from different
                path = os.path.dirname(os.path.abspath(f))
                sys.path.insert(0, path)
                logger.info("Added {} to sys.path".format(f))

                if f.endswith('.py'):
                    f = os.path.basename(f)
                    f = f[:-3]
                    logger.info("Using {} to load as module".format(f))

                try:
                    module = importlib.import_module(f)
                    print(module)
                    services.extend([k for (k, v) in module.__dict__.items() if not k.startswith('_') and callable(module.__dict__[k])])

                    globals().update(
                        {n: getattr(module, n) for n in module.__all__} if hasattr(module, '__all__') 
                        else 
                        {k: v for (k, v) in module.__dict__.items() if not k.startswith('_')
                    })
                except Exception as ex:
                    logger.error(ex)

            logger.info(services)
            a = wrap(services)

            # TODO fix RpcWrapper problems
            # this code is same as above in --class-file..
            s = zerorpc.Server(a)
            bind_address = "tcp://{host}:{port}".format(host=args.host,port=args.port)
            logger.info("binding server to: {}".format(bind_address))
            s.bind(bind_address)
            logger.info("running...")
            s.run()

    elif args.mode == 'cli':
        if args.service:
            l = list_services(args.service)
            #if foregrounded,a lookup will fail since it is deregistered from nomad
            if l:
                print(l)
                args.host = l.ip
                args.port = l.port

        print("connecting to for interactive session {}:{}".format(args.host,args.port))
        cmdline_repl(args.host,args.port)
    elif args.mode == 'status':
        list_services()

if __name__ == "__main__":
    main()