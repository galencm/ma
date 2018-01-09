# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import jinja2
import consul
import subprocess
import requests
import json
import textwrap
import argparse
import sys
import os
import logging
import logzero
from logzero import logger
import logzero
logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
#add logs option calling stderr
#./nomad logs -stderr -address=http://192.168.0.155:4646 343beff9

#nomad does not accept underscores in job names

def nomad_details():
    c = consul.Consul()
    nomad_details = c.agent.services()['_nomad-server-nomad-http']
    nomad_port = nomad_details['Port']
    nomad_ip = nomad_details['Address']
    return nomad_ip,nomad_port

def list_jobs(nomad_location=None):
    nomad,nomad_ip,nomad_port = nomad_details(nomad_location)
    print(nomad,nomad_ip,nomad_port)
    print(subprocess.check_output('{} status -address=http://{}:{}'.format(nomad,nomad_ip,nomad_port).split()).decode())


def list_services():
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    logger.info("retrieving service details from consul")
    print("{}\t\t{}\t\t{}".format("Service","Ip","Port"))
    for k in services.keys():
        print("{}\t{}\t{}".format(services[k]['Service'].ljust(15),services[k]['Address'],services[k]['Port']))

def get_job(name,path=".jobs",file=None):
    if not os.path.exists(os.path.abspath(path)):
        os.makedirs(path)

    nomad_ip,nomad_port = nomad_details()
    gs = 'http://{}:{}/v1/job/{}'.format(nomad_ip,nomad_port,name)
    r = requests.get(gs)
    logger.info(r.text)

    if file is not False:
        if file is None:
            fname = '{}.json'.format(name)
        else:
            fname = file
        with open(os.path.join(path,fname),'w+') as f:
            f.write(json.dumps(r.json(), indent=4))

    return r.json()

def stop_job(name,purge=False,verbose=False,nomad_location=None):
    logger.info("stopping {}".format(name))

    nomad,nomad_ip,nomad_port = nomad_details(nomad_location)
    if purge:
        purge = '-purge'
    else:
        purge=''

    print(subprocess.check_output('{} stop -address=http://{}:{} {} {}'.format(nomad,nomad_ip,nomad_port,purge,name).split()).decode())
    if verbose:
        #print(subprocess.check_output('{} status -address=http://{}:{}'.format(nomad,nomad_ip,nomad_port).split()).decode())
        list_jobs()

def run_external_job(external_file):
    external_file = os.path.join(path,external_file)
    logger.info("loading {}".format(external_file))
    if external_file.endswith('.hcl'):
        job_json = subprocess.check_output('{} run -output {}'.format(nomad,external_file).split()) 
        j = json.loads(job_json)

    elif external_file.endswith('.json'):
        with open(external_file) as json_data:
            j = json.load(json_data)

    if verbose:
        print(j)

    req = 'http://{}:{}/v1/job/{}'.format(nomad_ip,nomad_port,name)

    r = requests.put(req, json=j)
    print(r.status_code)
    
    fname = '{}.json'.format(name)

    with open(os.path.join(path,fname),'w+') as f:
        f.write(json.dumps(j, indent=4))


def run_job(name,command,args,path=".jobs",tags=None,verbose=False,external_file=None,checks=None,no_default_host_port_args=None):
    #pass in checks as list of textfiles with path
    args = list(filter(None, args)) 

    if not os.path.exists(os.path.abspath(path)):
        logger.info("creating: {}".format(os.path.abspath(path)))
        os.makedirs(path)

    logger.info("job path: {}".format(os.path.abspath(path)))

    logger.info("preparing to run job: {}".format(name))
    nomad_ip,nomad_port = nomad_details()
    logger.info("nomad address: http://{}:{}".format(nomad_ip,nomad_port))

    config = {}
    config['name'] = name
    if tags:
        config['tags'] = tags

    config['args'] = args
    config['command'] = command
    config['no_default_args'] = no_default_host_port_args

    #TODO modularize checks
    check_gphoto2 = textwrap.dedent('''
        check {
          type = "script"
          #id = "interfering-gphoto"
          name = "Interfering os gphoto processes"
          command = "/usr/local/bin/check_gphoto"
          interval = "10s"
          timeout = "1s"
          }
        ''')

    if checks == 'gphoto2':
        config['checks'] = [check_gphoto2]

    job_template = textwrap.dedent('''
    job "{{ name }}" {
      datacenters = ["dc1"]
      
      group "example" {
      count = 1
        task "{{ name }}" {
          driver = "raw_exec"
          service {
            name = "{{ name }}"
            tags = [{% for tag in tags %} "{{ tag }}",{% endfor %}]
            port = "service_port"
            {% for check in checks %}
            {{ check }}
            {% endfor %}

            }

          config {
            command = "{{ command }}"
            args = [
              {% for arg in args -%}
              "{{arg}}"{{ "," }}
              {%- endfor %}
              {% if no_default_args != true %}
              "--host","${NOMAD_IP_service_port}",
              "--port","${NOMAD_PORT_service_port}",
              {% endif%}
            ]
          }

          resources {
            network {
              #mbits = 10
              port "service_port" {}
            }
          }
        }
      }
    }
    ''')

    logger.info("rendering hcl from args dict: {}".format(config))
    job_hcl = jinja2.Environment().from_string(job_template).render(config)
    
    #do not overwrite if using external kwarg
    #in case of reload
    if not external_file:
        logger.info("writing job .hcl file: {}".format(os.path.join(path,'{}.hcl'.format(name))))
        with open(os.path.join(path,'{}.hcl'.format(name)),'w+') as f:
            f.write(job_hcl)

        logger.info("converting .hcl to .json for submission")
        job_json = subprocess.check_output('{} run -output {}.hcl'.format(nomad,os.path.join(path,name)).split()) 
        job_json=job_json.decode()

        logger.info("loading json")
        j = json.loads(job_json)

    if external_file:
        #external_file = os.path.join(path,external_file)
        logger.info("loading job file: {}".format(external_file))

        if external_file.endswith('.hcl'):
            logger.info("converting .hcl to .json for submission")
            job_json = subprocess.check_output('{} run -output {}'.format(nomad,external_file).split()) 
            job_json=job_json.decode()
            logger.info("loading json")
            j = json.loads(job_json)

        elif external_file.endswith('.json'):
            logger.info("loading json from file {}".format(external_file))
            with open(external_file) as json_data:
                j = json.load(json_data)

    job_submit_endpoint = 'http://{}:{}/v1/job/{}'.format(nomad_ip,nomad_port,name)
    logger.info("submitting(PUT) job json to: {}".format(job_submit_endpoint))
    r = requests.put(job_submit_endpoint, json=j)
    logger.info("{}".format(r))
    logger.info(j)

    json_file = '{}.json'.format(name)

    logger.info("writing job .json file: {}".format(os.path.join(path,json_file)))
    with open(os.path.join(path,json_file),'w+') as f:
        f.write(json.dumps(j, indent=4))

def foo(args):
    if 'status' in args or 'status-raw' in args:
        return False
    else:
        return True

def run_existing(argv):
    #parser.add_argument("--command",required='run' in argv , help="full path of command to call")
    logger.info("args: {}".format(argv))
    job_name = ""
    for i,arg in enumerate(argv):
        if arg == "--name":
            try:
                job_name = argv[i+1]
            except:
                return True
    job = os.path.join(os.path.expanduser('~/.local/jobs'),job_name)
    #sys.exit()
    if 'run' in argv and '--existing-file' in argv:
        return False
    elif 'run' in argv and os.path.isfile(job):
        return True
    elif 'run' in argv:
        return True
    else:
        return False

def main(argv):
    """Nomad jobs cli. Allow creation of jobs 
    via templates. 
    """
    log_levels = {
        "info":logging.INFO,
        "debug":logging.DEBUG,
        "warn":logging.WARN,
        "error":logging.ERROR,
    }

    jobs_path = os.path.expanduser('~/.local/jobs')

    tutorial_string = textwrap.dedent("""
        Example: Generate control scripts(start.sh, stop.sh):
            
            python3 machine.py run --name foo --file ~/machine_foo/machine.yaml

        job files are stored at:
            {}
    """.format(jobs_path))

    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser = argparse.ArgumentParser(epilog=tutorial_string,formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("action", help="stop|run|run-file|reload|status|status-raw|get|purge|rerun", choices=['run','run-file','stop','reload','status','status-raw','get','purge','rerun'])
    parser.add_argument("--name",required=foo(argv) , help="job name/id")
    parser.add_argument("--command",required=run_existing(argv), help="full path of command to call",default=None)
    parser.add_argument("--args", help="Args,kwargs and flags to be used by command. A string separated by space, quoted at beginning and end to avoid parsing. Example: \"--foo bar.baz --another-flag\" ",default=[])
    parser.add_argument("--nomad-location", help="nomad binary location",default="nomad")
    parser.add_argument("-v","--verbose",action="store_true", help="verbose")
    parser.add_argument("--existing-file", help="",default=False)
    parser.add_argument("-c","--checks",help="checks ie gphoto2")
    parser.add_argument("--log-level", choices=['debug','info','warn','error'],default="info",help="checks ie gphoto2")
    parser.add_argument("-j","--jobs-path", help="directory to story job output and generated files default: ~/.local/jobs" ,default=jobs_path)
    parser.add_argument("-t","--tags", help="store in tags",nargs='+',default=None)
    parser.add_argument("--no-default-args", action='store_true',default=False)

    #TODO tutorial string on error with no arguments
    args = parser.parse_args()  

    logzero.loglevel(log_levels[args.log_level])
    
    try:
        args.args=args.args.strip().split(" ")
    except AttributeError as ex:
        pass

    if args.action == 'run':
        run_job(args.name,args.command,args.args,path=args.jobs_path,tags=args.tags,verbose=args.verbose,checks=args.checks,external_file=args.existing_file,no_default_host_port_args=args.no_default_args)
    if args.action == 'rerun':
        args.existing_file = os.path.join(os.path.expanduser('~/.local/jobs'),args.name)
        formats={}

        #if no extension...
        for ext in [".json",".hcl"]:
            f_ext = args.existing_file+ext
            #formats.append(os.path.isfile(f_ext))
            formats[ext] = os.path.isfile(f_ext)

            print("{} {}".format(f_ext, formats[ext]))

        if len(set(list(formats.keys()))) == 1 and False in formats:
            print("no files found there!")
            return 
        else:
            for k,v in formats.items():
                if v is True:    
                    args.existing_file+=k
                    break

        run_job(args.name,args.command,args.args,path=args.jobs_path,tags=args.tags,verbose=args.verbose,checks=args.checks,external_file=args.existing_file,no_default_host_port_args=args.no_default_args)
    elif args.action =='stop':
        stop_job(args.name,False,args.verbose,args.nomad_location)
    elif args.action == 'reload':
        reload_file = '{}.json'.format(args.name)
        if not os.path.isfile(reload_file):
            if not os.path.isfile(os.path.join(args.jobs_path,reload_file)):
                parser.error('{} not found at {}'.format(reload_file,os.path.join(args.jobs_path,reload_file)))
        logger.info("reloading {}".format(args.name))
        stop_job(args.name,False,args.verbose,args.nomad_location)
        run_job(args.name,'',[],verbose=args.verbose,external_file=reload_file)
    elif args.action == 'run-file':
        run_job(args.name,'',args.args,verbose=args.verbose,external_file=args.existing_file)
    elif args.action =='purge':
        stop_job(args.name,True,args.verbose,args.nomad_location)
    elif args.action == 'status':
        list_jobs(args.nomad_location)
    elif args.action == 'status-raw':
        list_services()
    elif args.action == 'get':
        get_job(args.name,path=args.jobs_path)

if __name__ == "__main__":
    main(sys.argv)


