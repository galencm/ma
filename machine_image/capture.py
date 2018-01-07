# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import os
import subprocess
import sys
import io
from logzero import logger
import gphoto2 as gp
from PIL import Image
import uuid
import redis

import logzero
try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    logger.warn(ex)


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

def pre_slurp(generic_device):
    # getall pre_slurp:<generic_device.name> #sorted list?
    # {zoom,propsets?}
    # zoom func?    
    # dict of vars 
    # r.hgetall("state:{}".format(generic_device.name))

    # for k,v in gotten:
    # if k == "zoom":
    #     if generic_device.method == "gphoto2"
    # path =  "chdkptp.sh"
    # #luar waits for code to finish
    # r = subprocess.check_output(["bash",path,'-c',
    # '-erec',
    # '-eluar set_zoom(8)',
    # '-eluar return get_zoom()'],cwd="/home/<user>/chdk_latest/chdkptp-r735/")
    pass

def post_slurp(generic_device):
    pass
    
def capture(method,generic_device):
    """
        Returns:
            (tuple): keys,errors

                * list(str): list of keys to captured bytes
                * list(str): errors
    """

    pre_slurp(generic_device)
    errors = []
    returned = []
    try:
        returned,errors = globals()["capture_"+method](generic_device)
    except Exception as ex:
        logger.warn(ex)
        errors.append(ex)

    post_slurp(generic_device)

    return returned,errors

def prepare(device):
    """
    TODO
    devling
    ('set_prop(143,2)','chdkptp')
    """
    #./chdkptp.sh -c"-s=61B04259DB2B47F782788EA976488192" -e"rec" -e"luar set_zoom(1)" -e"luar return get_zoom()"

    #subprocess.check_output(['-c','-erec','-eluar set_zoom(1)' '-eluar return get_zoom()'])
    print("trying chdk")
    path =  "chdkptp.sh"
    #luar waits for code to finish
    #<user> placeholder
    r = subprocess.check_output(["bash",path,'-c',
    '-erec',
    '-eluar set_zoom(8)',
    '-eluar return get_zoom()'],cwd="/home/<user>/chdk_latest/chdkptp-r735/")


    returned = None
    errors=[r]
    print("errors? ",errors)
    #["prepare_"+method]
    #placeholder
    return returned,errors

def prepare_chdkptp():
    """
    TODO
    ___> connect

    con 14> =set_zoom(2)
    con 15>  =return get_zoom()
    16:return:2

    ./chdkptp.sh -c"-s=61B04259DB2B47F782788EA976488192" -e"rec" -e"luar set_zoom(1)" -e"luar return get_zoom()"

    36:return:1

    ---------------------------------
    connect
    connected: Canon PowerShot A570 IS, max packet size 512
    WARNING: CHDK extension not detected
    """
    returned = None
    errors=[]
    # =press'shoot_half' t0=get_tick_count() repeat sleep(10) until get_shooting() or get_tick_count() - t0 > 1000
    #https://chdk.setepontos.com/index.php?topic=13062.60
    return returned,errors


def capture_primitive_generic(generic_device):
    import consul
    import zerorpc
    def lookup(service):
        c = consul.Consul()
        services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
        for k in services.keys():
            if services[k]['Service'] == service:
                    service_ip,service_port = services[k]['Address'],services[k]['Port']
                    return service_ip,service_port
                    break
        return None,None

    source = r.get("primitive_generic:{}".format(generic_device.name))
    source_ip,source_port = lookup(source)

    zc = zerorpc.Client()
    zc.connect("tcp://{}:{}".format(source_ip,source_port))
    #result = zc('source')
    result = zc('source',generic_device.name)    
    gluuid = str(uuid.uuid4())
    binary_key = "glworb_binary:"+gluuid
    binary_r.set(binary_key, result)
    errors=[]
    return [binary_key],errors

def capture_primitive_virtual_camera(generic_device):
    import consul
    import zerorpc

    def lookup(service):
        c = consul.Consul()
        services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
        for k in services.keys():
            if services[k]['Service'] == service:
                    service_ip,service_port = services[k]['Address'],services[k]['Port']
                    return service_ip,service_port
                    break
        return None,None

    source = r.get("primitive_virtual_camera:{}".format(generic_device.name))
    source_ip,source_port = lookup(source)

    zc = zerorpc.Client()
    zc.connect("tcp://{}:{}".format(source_ip,source_port))
    #would prefer a single source() to avoid specifying
    #parameters, but device name is needed for certain
    #types of state, ie index position

    #could pass device name in
    result = zc('source',generic_device.name)
    #could dynamically generate function
    #result = zc('source_{}'.format(generic_device.name))
    #result = zc('source')
    gluuid = str(uuid.uuid4())
    binary_key = "glworb_binary:"+gluuid
    binary_r.set(binary_key, result)
    #process here...
    #problem should virtual camera be a widely available primitive?
    #not just in image_machine?
    from virtual_camera import render_img_from_kv
    #how to handle passing args if using zerorpc?
    render_img_from_kv(binary_key,generic_device.name)

    errors=[]
    return [binary_key],errors


def capture_gphoto2(generic_device):
    """Capture using gphoto2
        Args:
            generic_device: GenericDevice object
    
        Returns:
            list(str): keys to access bytes of created captures 
            list(str): errors
    """
    #TODO add thanks to gphoto2 bindings author...

    #can imagine a situation where chdkptp is used
    #to set focus,colorbalance etc...

    errors=[]
    binary_key = None
    err=[]
    #do not run prepare until TODO
    ###_,err = prepare(generic_device)

    errors.append(err)
    try:
        #code adapted from:
        #https://github.com/jim-easterbrook/python-gphoto2/blob/master/examples/copy-data.py
        logger.info(generic_device)
        name = generic_device.name
        addr = generic_device.address

        #context = gp.Context()
        context = gp.gp_context_new()
        #name, addr = camera_list[choice]
        camera = gp.Camera()
        # search ports for camera port name
        port_info_list = gp.PortInfoList()
        port_info_list.load()

        idx = port_info_list.lookup_path(addr)
        camera.set_port_info(port_info_list[idx])
        
        #camera.init(context)
        #gp.check_result(gp.use_python_logging())
        #context = gp.gp_context_new()
        #camera = gp.check_result(gp.gp_camera_new())
        gp.check_result(gp.gp_camera_init(camera, context))
        #print('Capturing image')
        file_path = gp.check_result(gp.gp_camera_capture(
            camera, gp.GP_CAPTURE_IMAGE, context))
        #print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
        target = os.path.join('/tmp', file_path.name)
        #target = io.BytesIO()
        print('Copying image to', target)
        camera_file = gp.check_result(gp.gp_camera_file_get(
                camera, file_path.folder, file_path.name,
                gp.GP_FILE_TYPE_NORMAL, context))

        file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))
        data = memoryview(file_data)
        nfile = io.BytesIO(data)
        #io.BytesIO(file_data)
        nfile.seek(0)
        contents = nfile.read()

        #image = Image.open(io.BytesIO(file_data))
        gluuid = str(uuid.uuid4())
        #glworb_binary:
        #glworb: binary_image : glworb_binary ?
        binary_key = "glworb_binary:"+gluuid
        binary_r.set(binary_key, contents)
        
        #store key of binary
        #binary_redis_conn.hmset("glworb:"+gluuid, dict({"image_binary_key":"glworb_binary:"+gluuid}))

        #image.show()

        gp.check_result(gp.gp_file_save(camera_file, target))
        #subprocess.call(['xdg-open', target])
        gp.check_result(gp.gp_camera_exit(camera, context))
    except Exception as ex:
        logger.warn(ex)
        errors.append(ex)
    if binary_key:
        return [binary_key],errors
    else:
        return [],errors
