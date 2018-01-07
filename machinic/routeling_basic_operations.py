# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

from logzero import logger
import redis
import paho.mqtt.client as mosquitto 
import sys
#import local_tools
import logzero
import os
import consul
try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    print(ex)

#redis_ip,redis_port = local_tools.lookup('redis')

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

mqtt_ip,mqtt_port = lookup('mqtt')
redis_ip,redis_port = lookup('redis')


logger.info("{}{}".format(redis_ip,redis_port))
r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
pubsub = r.pubsub()

#mqtt_ip,mqtt_port = local_tools.lookup('mqtt')
cli = mosquitto.Client()
cli.connect(mqtt_ip, mqtt_port, 60)

def mapii(rm,to_channel:str,*args):
    """Map internal to internal

        Args:
            channel(str): source channel
            to_channel(str): destination channel
            *args:

        Returns:
            RouteMessage:
    """
    logger.debug(sys._getframe().f_code.co_name)
    #internal_to_internal(to_channel,rm.contents)
    #r.sadd("watch:ii",rm.channel)
    r.sadd("watch:all",rm['channel'])
    r.sadd("watch:all",to_channel)

    logger.debug("{} {}".format(str(rm),to_channel))
    internal_to_internal(to_channel,rm['contents'])
    #internal_to_internal(channel,rm.contents)
    return rm

def mapix(rm,to_channel:str,*args):
    """Map internal to external

        Args:
            channel(str): source channel
            to_channel(str): destination channel
            *args:

        Returns:
            RouteMessage:
    """    
    logger.debug(sys._getframe().f_code.co_name)
    #r.sadd("watch:ix",rm.channel)
    r.sadd("watch:all",rm['channel'])
    internal_to_external(to_channel,rm['contents'])
    return rm

def mapxi(rm,to_channel:str,*args):
    """Map external to internal

        Args:
            channel(str): source channel
            to_channel(str): destination channel
            *args:

        Returns:
            RouteMessage:
    """    
    logger.debug(sys._getframe().f_code.co_name)
    #r.sadd("watch:xi",to_channel)
    r.sadd("watch:all",to_channel)
    external_to_internal(to_channel,rm['contents'])
    return rm

def mapxx(rm,to_channel:str,*args):
    """Map external to external

        Args:
            channel(str): source channel
            to_channel(str): destination channel
            *args:

        Returns:
            RouteMessage:
    """    
    logger.debug(sys._getframe().f_code.co_name)
    #r.sadd("watch:xx",to_channel)
    r.sadd("watch:all",to_channel)

    external_to_external(to_channel,rm['contents'])
    return rm



def external_to_internal(pubchannel,content):
    """external to internal

        Args:
            pubchannel(str): publishing channel
            content(str): content
    """  
    try:
        logger.info("xi topic: {0} with payload: {1} -> redis channel {0}".format(pubchannel,content))
        r.publish(pubchannel, content)
    except Exception as ex:
        logger.error(ex)        
        sys.exit(1)

def external_to_external(pubchannel,content):
    """external to external

        Args:
            pubchannel(str): publishing channel
            content(str): content
    """  
    try:
        logger.info("xx topic: {0} with payload: {1} -> mqtt channel {0}".format(pubchannel,content))
        cli.publish(pubchannel, payload=content)
    except Exception as ex:
        logger.warn(ex)
        sys.exit(1)

def internal_to_external(pubchannel,content):
    """internal to external

        Args:
            pubchannel(str): publishing channel
            content(str): content
    """  
    logger.info("ix topic: {0} with payload: {1} -> mqtt channel {0}".format(pubchannel,content))
    try:
        cli.publish(pubchannel, payload=content)
    except Exception as ex:
        logger.warn(ex)
        sys.exit(1)

def internal_to_internal(pubchannel,content):
    """internal to internal

        Args:
            pubchannel(str): publishing channel
            content(str): content
    """  

    logger.info("ii: channel {0} with payload: {1}".format(pubchannel,content))
    try:
        r.publish(pubchannel, content)
    except Exception as ex:
        logger.warn(ex)
        sys.exit(1)