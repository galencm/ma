# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

from textx.metamodel import metamodel_from_file
import uuid
import redis
import hashlib
from logzero import logger
import textwrap
import operator
import attr
import routeling_basic_operations
import os
import zerorpc
import local_tools
import sys


import logzero
try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    print(ex)
# @attr.s 
# class RouteMessage():
#     channel = attr.ib()
#     contents = attr.ib()
#     errors= attr.ib()

path = os.path.dirname(os.path.realpath(__file__))
routeling_metamodel = metamodel_from_file(os.path.join(path,'routeling.tx'))
redis_ip,redis_port = local_tools.lookup('redis')
r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
pubsub = r.pubsub()

def find_route(source_channel=None,route_hash=None, contents=None):
    if source_channel is None or source_channel == '':
        source_channel = "*"
    if route_hash is None or route_hash == '':
        route_hash = "*"


    match_query="route:*:{}:{}".format(source_channel,route_hash)
    matches = list(r.scan_iter(match=match_query))
    logger.info(match_query,matches)
    routes = {}

    for rt in matches:
        #routes.append()
        routes[rt] = r.get(rt)
    return routes

def add_route(dsl_string):
    """
        Args:
            dsl_string(str): A string that using pipeling grammar
    
        Returns:
            Tuple: name, key of created pipe
    """
    #route:<route_name>:<origin_channel>:<hash of route>

    routes = dsl_string.split("\n")
    routes = [r+"\n" for r in routes if r]
    created = []
    logger.debug(routes)
    for rt in routes:
        try:
            route = routeling_metamodel.model_from_str(rt)
            logger.debug("parsed {} into {}".format(rt,route))
            for rl in route.route_rules:
                channel = rl.channel

                dsl_hash = hashlib.sha224(rt.encode()).hexdigest()
                logger.info("adding route with hash: {}".format(dsl_hash))
                try:
                    name = route.name
                except:
                    name="_"
                key = "route:{}:{}:{}".format(name,channel,dsl_hash)
                r.set(key,rt)
                watch_route_key(channel)
                created.append((name,key))
        except Exception as ex:
            logger.error("Failed to parse {} using {}".format(repr(rt),routeling_metamodel))
            logger.error(ex)
    return created

def watch_route_key(channel):
    #add to watched channels
    #"if '/foo' do pipe prepareleft '{payload}' glworb_binary_key_contents\n"
    r.sadd("watch:all",channel)

def remove_routes():
    match_query = "route:*:*:*"
    routes = list(r.scan_iter(match=match_query))
    if routes:
        r.delete(*routes)
        logger.info("removed routes(s) {}".format(routes))

def remove_route(dsl_string):
    """Match and remove pipe(s) based on name, hashed contents or both

        Args:
            name(str): name of pipe
            dsl_string(str): string following pipeling grammar
    """
    if not dsl_string.endswith('\n'):
        dsl_string+="\n"

    dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()

    match_query = "route:*:*:{}".format(dsl_hash)
    routes = list(r.scan_iter(match=match_query))
    #remove from watch?
    if routes:
        r.delete(*routes)
        logger.debug("removed routes(s) {}".format(routes))
    else:
        logger.debug("no routes to remove matching {}".format(match_query))

def get_routes(query_pattern="*"):
    match_query = "route:*:{}".format(query_pattern)
    routes = list(r.scan_iter(match=match_query))
    return routes


def get_route(dsl_string):
    #names / hash could be different is pipe1:hash1 pipe1:hash2
    #for now only return first result
    #if dsl_string != "*":
    dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()
    #else:
    #    dsl_hash = dsl_string
    match_query = "route:*:{}".format(dsl_hash)
    try:
        routes = list(r.scan_iter(match=match_query))[0]
    except IndexError as ex:
        logger.debug("failed to get route {}".format(dsl_string))
        logger.debug(ex)
        return None

    stored_route = r.get(routes)
    if stored_route:
        try:
            route = routeling_metamodel.model_from_str(stored_route)
            return route
        except Exception as ex:
            logger.warn(ex)
            return None

def interpret_route(route,source_channel,payload):
    """Parse route rule(s) and route payload

        Args:
            route(str): a route rule to be parsed
            source_channel(str): source of payload
            payload(str):contents
    """
    logger.debug("{} {} {}".format(route,source_channel,payload))
    #grammer recognizes substitutions but use replace
    route = route.replace("{'from'}",source_channel)
    #added '' s around payload to allow correct parsing
    #of dashed-uuid-s
    try:
        #decode if from mqtt
        route = route.replace("{'payload'}","'{}'".format(payload.decode()))
    except:
        route = route.replace("{'payload'}","'{}'".format(payload))

    logger.debug("{} {} {} [after template substitutions]".format(route,source_channel,payload))

    routes = routeling_metamodel.model_from_str(route)
    #messy parsing...
    for route in routes.route_rules:
        try:
            try:
                result_left = comparate(route.left_compare.comparator_symbol.symbol,route.left_compare.comparator_value,payload.decode())
            except Exception as ex:
                result_left = True
            try:
                result_right = comparate(route.right_compare.comparator_symbol.symbol,payload.decode(),route.right_compare.comparator_value)
            except Exception as ex:
                result_right = True

            decision = result_left and result_right
            logger.info("{} and {} = {}".format(result_left,result_right,decision))
            if decision is True:
                args = []
                for arg in route.args:
                    print(arg)
                    try:
                        print(arg.arg)
                        args.append(arg.arg)
                        try:
                            print(arg.arg.sub)
                        except Exception as ex:
                            print(ex)

                    except Exception as ex:
                        print(ex)

                #builtins = ['mapii','mapix','mapxi','mapxx']
                #if route.action in builtins:
                if hasattr(routeling_basic_operations,route.action.lower()):
                    #use dict instead of custom obj
                    #rm = RouteMessage(source_channel,payload,'')
                    rm = {'channel':source_channel,
                          'contents':payload,
                          'errors':''
                    }
                    rargs = [rm] + args
                    logger.debug("builtin rpc --> {} + {}".format(route.action,rargs))
                    try:
                        getattr(routeling_basic_operations, route.action.lower())(*rargs)
                    except Exception as ex:
                        logger.warn(ex)
                elif route.action == 'pipe':
                    logger.info("PIPE {} {}".format(route.action,args))
                    #with pipe assume message is a glworb id?
                    #rargs = [] + rargs
                    #put into a todo queue?
                    #query route.action.lower() for rpc address
                    #another option:
                    #https://www.hashicorp.com/blog/replacing-queues-with-nomad-dispatch/
                    #TODO queue here...

                    for service in local_tools.fuzzy_lookup('zerorpc-'):
                        logger.info("trying service {}".format(service['service']))
                        zc = zerorpc.Client()
                        zc.connect("tcp://{}:{}".format(service['ip'],service['port']))
                        result = zc(route.action.lower(),*args)
                        logger.info(result)
                else:
                    for service in local_tools.fuzzy_lookup('zerorpc-'):
                        try:
                            logger.info("trying service {}".format(service['service']))
                            zc = zerorpc.Client()
                            zc.connect("tcp://{}:{}".format(service['ip'],service['port']))
                            result = zc(route.action.lower(),*args)
                            logger.info(result)
                        except Exception as ex:
                            print(ex)

                    #rpc_ip,rpc_port = local_tools.lookup('zerorpc-image')
                    # zc = zerorpc.Client()
                    # zc.connect("tcp://{}:{}".format(rpc_ip,rpc_port))
                    # result = zc(route.action.lower(),*args)
                    # logger.info(result)
                    #rpc(*rargs)
        except Exception as ex:
            logger.warn(ex)

def comparate(comparator,a,b,try_to_cast=True):
    """Given a string comparator and two inputs return results.

        Args:
            comparator(str): 
            a:
            b:

        Returns:
            bool: comparator results
    """
    if try_to_cast:
        try:
            a = float(a)
            b = float(b)
        except Exception as ex:
            logger.debug(ex)
            pass

    result = False

    if comparator == "<":
        result =  operator.lt(a,b)
    elif comparator == ">":
        result =  operator.gt(a,b)
    elif comparator == "<=":
        result =  operator.le(a,b)
    elif comparator == ">=":
        result =  operator.ge(a,b)
    elif comparator == "!=":
        result =  operator.ne(a,b)
    elif comparator == "==":
        result =  operator.eq(a,b)
    else:
        result = False

    logger.debug("{a} {symbol} {b} = {result}".format(a=a,b=b,symbol=comparator,result=result))
    return result


## ##

#import route_funcs

#comparisons:
#comparator = channelname pointer(lookup) | float | string 
# (left_comparator <) payload                           check
# (left_comparator <) payload (< right_comparator)      check 
#                     payload (< right_comparator)      check
#                     payload                           True

