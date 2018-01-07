#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import netifaces
import time
import subprocess
import argparse
import sys
from logzero import logger
import jinja2
import pathlib
import fnmatch
from ruamel.yaml import YAML
import os
import uuid
import json
#change to consul library
import local_tools


#Problem:
# nomad will give mosquitto a different port each time
# homie will have to be reset on each change of port
#Solution:
# * dns for mqtt ?
# static port (not recommended by nomad docs)

#running iwlist with sudo seems to find more networks...
def gather_from_env(ap_ssid,ap_pass):
    env_vars = {
    'device_name' : str(uuid.uuid4())[:10],
    'device_id' : str(uuid.uuid4())[:10],
    'ssid' : ap_ssid,
    'ssid_pass' : ap_pass,
    'mqtt_host' : local_tools.lookup('mqtt')[0],
    'mqtt_port' : local_tools.lookup('mqtt')[1],
    'generator_name' : 'associative.py'
    }
    return env_vars

def scan_loop(iface,config=None,ap_ssid=None,ap_pass=None,rate=5):
    #template: file or string
    associate_table = {}
    if config:
        try:
            #append full path to config file if 
            #using a local path
            if not "/" in config:
                script = os.path.abspath(__file__)
                f = os.path.join(os.path.dirname(script),config)
                f = pathlib.Path(f)
            else:
                f = pathlib.Path(config)
                logger.info(f.absolute())
                #f = f.absolute()
            yaml=YAML(typ='safe')
            associations = yaml.load(f)
            for k,v in associations.items():
                for p in v['associate']:
                    if not os.path.isfile(v['template']):
                        associate_table[p] = associations[k]['template']
                        print(k)
                        print(associations[k].keys())
                        print(repr(associations[k]['template']))
                        #associate_table[p] = v['template']
                        #print(v['template'])
                        #print("----")
        except Exception as ex:
            logger.warn(ex)
            logger.warn(os.path.abspath(__file__))
    else:
        logger.warn("No config")

    while True:
        essids = scan(iface)
        print("?")
        #create this table elsewhere
        #to allow send independent of scan process
        for pattern in associate_table.keys():
            for match_ssid in fnmatch.filter(essids, pattern):
                env_vars = gather_from_env(ap_ssid,ap_pass)
                logger.info(env_vars)
                payload = jinja2.Environment().from_string(associate_table[pattern]).render(env_vars)
                logger.info("{} {}".format(match_ssid,pattern))
                logger.info("preparing to associate...")
                associate_and_send(iface,match_ssid,payload)
        time.sleep(rate)

def associate_and_send(iface,essid,payload):
    """
    This section is problematic, perhaps due to interactions
    with networkmanager can work or fail depending on state of
    system
    """
    logger.info("diassociating {} before associating".format(iface))
    #   subprocess.check_output(['sudo','iwconfig',iface,'ap','00:00:00:00:00:00'])
    logger.info("connecting to {}".format(essid))
    try:
        print(subprocess.check_output(['sudo','iwconfig',iface,'essid','{}'.format(essid)]))
        logger.info("sleeping for 5 seconds")
        time.sleep(5)
        logger.info("slept for 5 seconds")
        # #-r prevents 'dhclient() is already running - exiting.'
        # #but releases all other leases too..
        #print(subprocess.check_output(['sudo','dhclient','-1',iface,"-r","-v"]))
        try: 
            print(subprocess.check_output(['sudo','dhclient','-1',iface,"-v"]))
        except:
            logger.warn("no dhcp lease retrying...")
            associate_and_send(iface,essid,payload)        
        print(payload)
        print(json.loads(payload))
        try:
            iface_ip = netifaces.ifaddresses(iface)[2][0]['addr'] 
        except KeyError:
            logger.warn("no ip received retrying...")
            associate_and_send(iface,essid,payload)        
    except:
        send(iface,payload)

def send(iface,payload,post_send_delay=5):
    print(payload)

    iface_ip = netifaces.ifaddresses(iface)[2][0]['addr'] 
    #assume ap ip ends with .1
    ap_ip = iface_ip.rsplit(".",1)[0]+".1"
    #logger.info("connected to {} with ip {}".format(essid,iface_ip))
    logger.info("ap ip assumed to be {}".format(ap_ip))
    #url is homie specific and should be templated
    
    #response = subprocess.check_output(['curl','-X','PUT','http://{}/config'.format(ap_ip),'--header','"Content-Type: application/json"','-d','{}'.format(json.dumps(payload))])
    response = subprocess.check_output(['curl','-X','PUT','http://{}/config'.format(ap_ip),'--header','"Content-Type: application/json"','-d','{}'.format(json.dumps(json.loads(payload)))])
    print(response.decode())

    #b'{"success":false,"error":"Invalid or too big JSON"}'
    #{"success":true}


    logger.info("diassociating {}".format(iface))
    subprocess.check_output(['sudo','iwconfig',iface,'ap','00:00:00:00:00:00'])
    #give device change to reconfigure
    time.sleep(post_send_delay)

def scan(scan_iface):
    #wifi_ifaces = [d for d in netifaces.interfaces() if scan_iface in d]
    a = netifaces.interfaces()
    #wifi_ifaces = [d for d in netifaces.interfaces() if scan_iface == d]
    logger.error(a[-1] == scan_iface)
    print(a[-1],scan_iface)
    wifi_ifaces = [d for d in a if scan_iface == d]
    found_essids =[]
    logger.info(scan_iface)
    logger.info(netifaces.interfaces())
    logger.info(wifi_ifaces)

    for iface in wifi_ifaces:
        found = []
        logger.info("{} scanning...".format(iface))
        found = subprocess.check_output(['sudo','iwlist',iface,'scan'])
        found = [ssid.split('"')[1] for ssid in str(found).split('\\n') if "ESSID" in ssid]
                
        #print("{} found ssids: {}".format(iface,found))

        logger.info("{} found ssids: {}".format(iface,found))
        found_essids.extend(found)
    return found_essids

def main(argv):
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("interface", help="wireless iface")
    parser.add_argument("-c","--config", help="config yaml")
    parser.add_argument("--ap-ssid", help="access point ssid",default=None)
    parser.add_argument("--ap-pass", help="access point password",default=None)

    args = parser.parse_args()
    scan_loop(args.interface,args.config,args.ap_ssid,args.ap_pass)

if __name__ == '__main__':
    main(sys.argv)
