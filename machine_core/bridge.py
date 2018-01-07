#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import redis
import paho.mqtt.client as mosquitto 
import sys
import threading
#import zerorpc
from logzero import logger
import routeling
#import route_crud

import logzero
import os
import sys

import redis
import consul


#define special prefixes with handler function
#define functions as None to avoid 'not defined' 
RESERVED_PREFIXES = {
    "rpc"   : 'handle_rpc', 
    "/rpc"  : 'handle_rpc',
    "set"   : 'handle_set',
    "/set"  : 'handle_set',
}

def handle_rpc(prefix,topic,payload):
    """
    <peripheral type="button" alternative_press="">
        <output type="integer" value="" destination="/rpc/BAR/topology_increment"/>
    </peripheral>
    """
    address = topic.replace(prefix,"")
    if address.startswith("/"):
        address=address[1:]
    logger.info("rpc {}{}{}".format(prefix,topic,payload))

def handle_set(prefix,topic,payload):
    """
    <peripheral type="button" alternative_press="">
        <output type="integer" value="1" destination="/set/BAR/markers/capture1"/>
    </peripheral>
    <peripheral type="button" alternative_press="">
        <output type="integer" value="+=1" destination="/set/BAR/markers/capture1"/>
    </peripheral>
    """
    clobber = True
    payload = payload.decode()
    address = topic.replace(prefix,"")
    if address.startswith("/"):
        address=address[1:]
    logger.info("set {}{}{}".format(prefix,topic,payload))
    
    address,sub_address = address.split("/")
    value = None
    symbol = None
    if "+=" in payload:
        symbol = "+="
    elif "-=" in payload:
        symbol = "-="
    elif "*=" in payload:
        symbol = "*="

    if symbol is None:
        r.hmset("state:{}".format(address),dict({sub_address:payload}))
    else:
        try:
            try:
                stored = int(r.hget("state:{}".format(address),sub_address))
            except Exception as ex:
                logger.warn(ex)
                if clobber:
                    stored = 0
                else:
                    return
            value = int(payload.partition(symbol)[-1])
            if symbol == "+=":
                stored += value
            elif symbol == "-=":
                stored -= value
            elif symbol == "*=":
                stored *= value
            #elif symbol == "++":
            #string concat
            #    stored += value    
            r.hmset("state:{}".format(address),dict({sub_address:stored}))
        except Exception as ex:
            logger.warn(ex)


def lookup(service):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if services[k]['Service'] == service:
                service_ip,service_port = services[k]['Address'],services[k]['Port']
                return service_ip,service_port
                break
    return None,None
try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    print(ex)
#[Errno 13] Permission denied: '/tmp/bridge.py.log'

mqtt_ip,mqtt_port = lookup('mqtt')
redis_ip,redis_port = lookup('redis')
r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
pubsub = r.pubsub()

cli = mosquitto.Client()

def decide_routing(topic,payload):
    """Handle a routing. Redis currently looks up all routes...

        Redis keyname format is route:<route_name>:<origin_channel>:<hash of route>
        route_name is only for organization, and will not be used when 
        hashes are checked for duplicates
        Args:
            topic(str):mqtt topic or redis key
            payload(str):contents
    """
    logger.info("[decide] Routing for {} {}".format(topic,payload))
    #possible_routes = 
    query = 'route:*:{}:*'.format(topic)
    logger.info("[decide] {}".format(query))
    #convert to a list for debugging
    #use as generator once behavior is correct
    query_results = list(r.scan_iter(match=query))
    logger.info("[decide] {}".format(query_results))

    for route in query_results:
        logger.info("[decide] {}".format(route))
        route_dsl = r.get(route)
        #TODO: consider behavior
        #failing a get? ie route is removed between retrievel of query results
        #assert route_dsl is not None
        if route_dsl is not None:
            routeling.interpret_route(route_dsl,topic,payload)
            #return values from interpret route and call here?
            #currently calling in function
        else:
            logger.error("{} returned {}".format(route,route_dsl))

    for prefix,handler in RESERVED_PREFIXES.items():
        logger.info("reserved? {} {}".format(prefix,topic))
        if topic.startswith(prefix):
            logger.info("reserved! {} {}".format(prefix,topic))
            logger.info(handler)
            #handler(prefix,topic,payload)
            globals()[handler](prefix,topic,payload)
def to_redis(pubchannel,content):
    """Publish via redis

        Args:
            pubchannel(str): publishing channel
            content(str): content    

    """
    try:
        logger.info("topic: {0} with payload: {1} -> redis channel {0}".format(pubchannel,content))
        r.publish(pubchannel, content)
    except Exception as ex:
        logger.warn(ex)
        sys.exit(1)

def on_message(mosq, obj, msg):
    """mosquitto callback 
    """
    #logger.info("%-20s %d %s" % (msg.topic, msg.qos, msg.payload))
    logger.info("[mqtt received] topic: {} payload: {}".format(msg.topic, msg.payload))

    #always to redis regardless of routing?
    #to_redis(msg.topic, msg.payload)
    decide_routing(msg.topic, msg.payload)

def watch_internal(redis_conn):
    """Watch redis keys for changes and do any routing on change
        
        Args:
            redis_conn(redis.StrictRedis): redis connection object
    """
    redis_conn_pubsub = redis_conn.pubsub()
    keys = []
    for w in r.scan_iter(match='watch:*'):
        keys.extend(list(redis_conn.smembers(w)))
    #print(keys)
    keys = ["__keyspace*__:{}".format(s) for s in keys]

    #redis_conn_pubsub.psubscribe(keys)
    redis_conn_pubsub.psubscribe("*")
    #redis_conn_pubsub.psubscribe("*","__keyspace*__:*")

    for item in redis_conn_pubsub.listen():
        #{'channel': '__keyspace@0__:foo', 'data': 'set', 'type': 'pmessage', 'pattern': '__keyspace*__:foo'}
        #key value has been set/changed
        #{'type': 'pmessage', 'pattern': '*', 'data': 'barz', 'channel': '/foo'}
        #print(item)
        logger.debug(item)
        for w in redis_conn.scan_iter(match='watch:*'):
            key = item['channel']
            value = item['data']
            #logger.debug(item)
            if redis_conn.sismember(w,key):
                logger.debug("[watcher] {} is in {}".format(key,w))
                decide_routing(key,value)


def on_publish(mosq, obj, mid):
    """mosquitto callback on publish
    """
    pass

def on_subscribe(mosq, obj, mid, granted_qos):
    """mosquitto callback on subscribe
    """
    pass

def run_bridge():
    logger.info("starting mosquitto client loop")
    while cli.loop() == 0:
        pass
    logger.info("bridging halted")
    sys.exit(1)

cli.on_message = on_message
cli.on_publish = on_publish
cli.on_subscribe = on_subscribe
sub_topics = "#"
cli.connect(mqtt_ip, mqtt_port, 60)
cli.subscribe(sub_topics, 0)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("action", help="bridge|reactor|both", choices=['bridge','reactor','both'])


    #parser.add_argument("--watch-internal", help="handle internal events",action="store_true")
    #parser.add_argument("--bridge", help="run router",action="store_true")
    #parser.add_argument("--all", help="run all",action="store_true")

    #args = parser.parse_args()
    #do this to avoid --host args...
    args = parser.parse_known_args()[0]

    print(args)
    if args.action == 'both':
        logger.info("starting internal reactor in thread...")
        threads = []
        t = threading.Thread(target=watch_internal,args=(r,))
        threads.append(t)
        t.start()
        logger.info("starting bridge...")
        run_bridge()

    if args.action == 'bridge':
        logger.info("starting bridge...")
        run_bridge()

    if args.action == 'reactor':
        logger.info("starting reactor...")
        watch_internal(r)
