import consul
import zerorpc
import redis
import functools
from logzero import logger
import logzero
import os
import sys

logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))

#decorated function needs to be inside object?
#zerorpc.exceptions.LostRemote: Lost remote after 10s heartbeat
#receiving with tests ^
# @zerorpc.stream
# def streaming_sub(channels):
#     s = list_services('redis')
#     r = redis.StrictRedis(host=s['ip'], port=s['port'],decode_responses=True)
#     rsub = r.pubsub() 
#     rsub.subscribe(channels)

#     for item in rsub.listen():
#         yield item


def pub(func,publisher="redis",channel="/",message=None,*args):
    """Take a function and args: and publish result on channel
        publisher : redis or mqtt
    """
    #sandbox funcs?
    #result = globals()[func](*args)
    if publisher == 'redis':
        s = list_services('redis')
        r = redis.StrictRedis(host=s['ip'], port=s['port'],decode_responses=True)
        r.publish(channel,result)
    elif publisher == 'mqtt':
        pass 

def list_services(service_name=None,return_format=list):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    if service_name is None:
        if return_format == list:
            service_objs = []
            for k in services.keys():
                service_objs.append(dict({"service":services[k]['Service'],"ip":services[k]['Address'],"port":services[k]['Port']}))
            return service_objs
    else:
        for k in services.keys():
            if services[k]['Service'] == service_name:
                return dict({"service":services[k]['Service'],"ip":services[k]['Address'],"port":services[k]['Port']})
        return None

def echo(*args):
    return args

#def from_redis(pattern,keytype):
def b64_key(uuid):
    #import base64
    import io
    f = io.BytesIO()
    s = list_services('redis')
    binary_r = redis.StrictRedis(host=s['ip'], port=s['port'])
    contents = binary_r.get(uuid)
    #contents = contents.encode('base64')
    #contents = base64.b64encode(contents.read())
    return contents

def bimg_resized(uuid,new_size):
    import io
    from PIL import Image

    s = list_services('redis')
    binary_r = redis.StrictRedis(host=s['ip'], port=s['port'])
    contents = binary_r.get(uuid)
    f = io.BytesIO()
    f = io.BytesIO(contents)


    img = Image.open(f)
    img.thumbnail((new_size,new_size), Image.ANTIALIAS)

    extension = img.format
    file = io.BytesIO()
    img.save(file,extension)
    img.close()
    file.seek(0)

    return file.getvalue()

def b64_key(uuid):
    #import base64
    import io
    f = io.BytesIO()
    s = list_services('redis')
    binary_r = redis.StrictRedis(host=s['ip'], port=s['port'])
    contents = binary_r.get(uuid)
    #contents = contents.encode('base64')
    #contents = base64.b64encode(contents.read())
    return contents

def from_redis(pattern=None,keytype=None,*args):
#def from_redis(pattern,keytype,*args,**kwargs):
    print(pattern,keytype)
    keys={
    'string':'get',
    'hash':'hgetall',
    #'list':''
    'set':'smembers',
    #'zset'
    'binary':'get'
    }
    s = list_services('redis')
    if keytype == 'binary':
        r = redis.StrictRedis(host=s['ip'], port=s['port'])
    else:
        r = redis.StrictRedis(host=s['ip'], port=s['port'],decode_responses=True)
    
    if pattern is None:
        pattern="*"
    matches = r.scan_iter(match=pattern)
    #since retrieval depends on keytype, if none
    #just return all matching key names
    if keytype is None:
        results = list(matches)
    else:       
        results = []
        for m in matches:
            results.append(getattr(r,keys[keytype])(m))

    return results


glworbs = functools.partial(from_redis, pattern='glworb:*',keytype='hash')
routes = functools.partial(from_redis, pattern='route:*',keytype='string')
pipes = functools.partial(from_redis, pattern='pipe:*',keytype='string')
binaries = functools.partial(from_redis, pattern='*binary*:*',keytype='string')
