# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import gphoto2 as gp
import attr
import datetime
import inspect
import sys
from logzero import logger
import logzero
import os

try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    logger.warn(ex)

NAME = sys.modules[__name__]

@attr.s 
class GenericDevice(object):
    """Generic Device class

        Attributes:
            name (str): Device name 
            uid (str): unique id. Not guaranteed to be universally unique 
            address (str): address, depends on device(ie usb path for gphoto2)
            discovery_method (str): method by which device is identified and properties enumerated 
            foundnow (bool): found during last discovery method query
            lastseen (str): timestamp for last time foundnow was True

    """
    name = attr.ib(default="")
    address = attr.ib(default="")
    uid = attr.ib(default="")
    discovery_method = attr.ib(default="")
    foundnow = attr.ib(default=True)
    lastseen = attr.ib(default="")

def discover():
    """Use available discvery methods to enumerate devices

        Returns:
            list(GenericDevices): list of discovered devices
            list(str): errors

    """
    errors = []
    device_list = []
    all_functions = inspect.getmembers(NAME, inspect.isfunction)
    discovery_methods = [s[1] for s in all_functions if s[0].startswith("discover_")]

    for method in discovery_methods:
        logger.info(method)
        try:
            result,err = method()
            device_list.extend(result)
            errors.extend(err)
        except Exception as ex:
            logger.warn(ex)
            errors.append(ex)
    return device_list,errors

def discover_primitive_virtual_camera():
    import redis
    import consul
    def lookup(service):
        c = consul.Consul()
        services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
        for k in services.keys():
            if services[k]['Service'] == service:
                    service_ip,service_port = services[k]['Address'],services[k]['Port']
                    return service_ip,service_port
                    break
        return None,None

    r_ip,r_port = lookup('redis')
    r = redis.StrictRedis(host=r_ip, port=str(r_port),decode_responses=True)
    binary_r = redis.StrictRedis(host=r_ip, port=str(r_port))

    discovery_method = "primitive_virtual_camera"
    camera_list = []
    errors = []
    matched = r.scan_iter("primitive_virtual_camera:*")
    for match in matched:
        name = match.split(":")[-1]
        source = r.get(match)
        now = str(datetime.datetime.now())
        camera_list.append(GenericDevice(name=name,address=source,uid=name, discovery_method=discovery_method,lastseen=now))
    return camera_list,errors

def discover_primitive_generic():
    import redis
    import consul
    def lookup(service):
        c = consul.Consul()
        services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
        for k in services.keys():
            if services[k]['Service'] == service:
                    service_ip,service_port = services[k]['Address'],services[k]['Port']
                    return service_ip,service_port
                    break
        return None,None

    r_ip,r_port = lookup('redis')
    r = redis.StrictRedis(host=r_ip, port=str(r_port),decode_responses=True)
    binary_r = redis.StrictRedis(host=r_ip, port=str(r_port))

    discovery_method = "primitive_generic"
    camera_list = []
    errors = []
    matched = r.scan_iter("primitive_generic:*")
    for match in matched:
        name = match.split(":")[-1]
        source = r.get(match)
        now = str(datetime.datetime.now())
        camera_list.append(GenericDevice(name=name,address=source,uid=name, discovery_method=discovery_method,lastseen=now))
    return camera_list,errors


def discover_gphoto2():
    """ Discover devices using python bindings 
    for gphoto2. Gphoto2 attempts to autodetect
    any connected devices, identifying them by name 
    and usb address. 

    The name is not unique and the 
    usb address can change on disconnects or poweroff.
    
    Upon discovering a device, query for information and 
    parse serial number to use as a unique identifier.

    Construct a GenericDevice for each device found

    Returns:
        list(GenericDevices): discovered devices
        list(str): errors

    """
    discovery_method = "gphoto2"
    camera_list = []
    errors = []
    context = gp.Context()
    try:
        for name, addr in context.camera_autodetect():
            now = str(datetime.datetime.now())
            c = gp.Context()
            camera = gp.Camera()
            camera.init(c)
            text = camera.get_summary(c)
            serial =""
            for t in str(text).split("\n"):
                if ("Serial Number:") in t:
                    serial = t.partition(":")[-1].strip()
                    logger.info(serial)
                    break
            camera.exit(c)
            camera_list.append(GenericDevice(name, addr,serial,discovery_method=discovery_method,lastseen=now))
    except Exception as ex:
        logger.warn(ex)
        errors.append(ex)
    return camera_list,errors

if __name__ == "__main__":
    print(discover())