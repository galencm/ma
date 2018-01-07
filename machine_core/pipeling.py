from textx.metamodel import metamodel_from_file
import uuid
import redis
import hashlib
from logzero import logger
import textwrap
import attr
import os
import functools
import glob
import importlib
import sys
#import local_tools
import logzero
import consul

try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    print(ex)

import sys
for f in glob.glob('../**/pipeline_*.py'):
    logger.info("{} matches pipe filter ".format(f))
    path,pipe_package = os.path.split(os.path.abspath(f))
    logger.info("adding {} to path".format(path))
    sys.path.append(path)
    logger.info("importing {}".format(pipe_package[:-3]))
    module = importlib.import_module(pipe_package[:-3])
    #module = importlib.import_module(f[:-3])
    globals().update(
        {k: v for (k, v) in module.__dict__.items() if  k.startswith('pipe_')}
    )

    logger.info({k: v for (k, v) in module.__dict__.items() if  k.startswith('pipe_')})

#print([s for s in globals() if s.startswith("pipe_")])
#change RouteMessage object to dict
@attr.s 
class RouteMessage():
    channel = attr.ib()
    contents = attr.ib()
    errors= attr.ib()

path = os.path.dirname(os.path.realpath(__file__))
pipeling_metamodel = metamodel_from_file(os.path.join(path,'pipeling.tx'))


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

redis_ip,redis_port = lookup('redis')

#mqtt_ip,mqtt_port = lookup('mqtt')

#redis_ip,redis_port = local_tools.lookup('redis')
r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
pubsub = r.pubsub()


def add_pipe(dsl_string):
    """
        Args:
            dsl_string(str): A string that using pipeling grammar
    
        Returns:
            Tuple: name, key of created pipe
    """
    #TODO add overwrite? ie if name is same and hash changes, delete others with same name first?
    try:
        pipe = pipeling_metamodel.model_from_str(dsl_string)
    except Exception as ex:
        logger.error("Failed to parse {} using {}".format(dsl_string,pipeling_metamodel))
        logger.error(ex)
        return None,None
    remove_pipe(pipe.name)
    dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()
    pipe_key = "pipe:{}:{}".format(pipe.name,dsl_hash)
    r.set(pipe_key,dsl_string)
    #some sort of success/failure return?
    return pipe.name,pipe_key


def remove_pipe(name=None,dsl_string=None):
    """Match and remove pipe(s) based on name, hashed contents or both

        Args:
            name(str): name of pipe
            dsl_string(str): string following pipeling grammar
    """
    if name is None and dsl_string is None:
        return

    if dsl_string is not None:
        dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()
    else:
        dsl_hash = '*'

    if name is None or name is '':
        name="*"

    match_query = "pipe:{}:{}".format(name,dsl_hash)
    pipes = list(r.scan_iter(match=match_query))
    
    #do not pass empty list to redis
    if pipes:
        r.delete(*pipes)
        logger.info("removed pipe(s) {}".format(pipes))
    else:
        logger.info("no pipes to remove matching {}".format(match_query))


def pipe(name,glworb_key,glworb_field,*args):

    # for f in glob.glob('pipeline_*.py'):
    #     print("globbing ",f)
    #     module = importlib.import_module(f[:-3])
    #     globals().update(
    #         {k: v for (k, v) in module.__dict__.items() if  k.startswith('pipe_')}
    #     )

    #     logger.info({k: v for (k, v) in module.__dict__.items() if  k.startswith('pipe_')})


    #['prepareleft', 'bar', 'glworb_binary_key_contents']
    # pipename     glworb_id glworb_key
    p = get_pipe(name)
    logger.info("pipe: {} {}".format(p,name))

    #def pipe_starti(glworb_uuid,glworb_key,prefix="glworb:",*args):

    logger.info("starting pipe for {} {}".format(glworb_key,glworb_field))
    piped_obj = None
    
    #multiprocessing? process_steps(target=)
    for step in p.pipe_steps:
        args = [arg.arg for arg in step.args]
        logger.info("{}{}".format(step,args))
        try:
            if '_' in args:
                args[args.index('_')] = glworb_key
                logger.debug('{} substituted for _'.format(glworb_key))
        except Exception as ex:
            print(ex)
            pass

        if step.call == 'pipe':
            pipe((args[0]),*args[1:])
        elif 'start' in step.call:
            #special first call, move to objects?
            #logger.info([s for s in globals() if s.startswith("pipe_")])
            piped_obj = globals()["pipe_"+step.call](glworb_key,glworb_field,*args)
            #    path = os.path.dirname(os.path.realpath(__file__))
        else:
            piped_obj = globals()["pipe_"+step.call](piped_obj,*args)

        #return 


#was/will be pipe
def old_pipe(name=None,dsl_string=None):
    #pipe to mimic route call...
    #TODO ponder
    #could create an empty pipe if not found
    empty_pipe = textwrap.dedent('''
    pipe {} {{
    startimg 
    ocr ocr_results 
    endimg 
    }} 
    '''.format(name))

    if dsl_string is not None:
        created,_ = add_pipe(dsl_string)
        return get_pipe(created)

    if name is not None:
        p =  get_pipe(name)
        if p is None:
            created,_ = add_pipe(empty_pipe)
            return get_pipe(created)   
        else:
            return p

def get_pipes(query_pattern="*"):
    match_query = "pipe:{}:*".format(query_pattern)
    pipes = list(r.scan_iter(match=match_query))
    return pipes

def get_pipe(name):
    #names / hash could be different is pipe1:hash1 pipe1:hash2
    #for now only return first result
    match_query = "pipe:{}:*".format(name)
    try:
        pipes = list(r.scan_iter(match=match_query))[0]
    except IndexError as ex:
        logger.debug(ex)
        return None

    stored_pipe = r.get(pipes)
    logger.info(match_query)
    if stored_pipe:
        try:
            pipe = pipeling_metamodel.model_from_str(stored_pipe)
            return pipe
        except Exception as ex:
            logger.warn(ex)
            return None

#def rpc(call,*args):
#    logger.info("mock rpc {}".format(call,args))

def into_pipe(p,glworb_key,glworb_field_key):
    logger.info("starting pipe for {} {}".format(glworb_key,glworb_field_key))
    for step in p.pipe_steps:
        args = [arg.arg for arg in step.args]

        try:
            if '_' in args:
                args[args.index('_')] = glworb_key
                logger.debug('{} substituted for _'.format(glworb_key))
        except:
            pass

        if step.call == 'pipe':
            into_pipe(pipe(args[0]),*args[1:])

        else:
            #cannot do one rpc call at a time since object
            #will not be serialized
            #look in same dir for functions?
            rpc(step.call,*args)

def compose(*functions):
    """Compose list of functions

        Args:
            *functions: list of functions

        Returns:
            func: composed functions
    """
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


# ################################################################
# #should be separate file,part of image_machi copied and pasted
# #due to import issues
# from PIL import Image
# import redis
# from io import BytesIO
# import attr
# import uuid
# import sys
# #from tesserocr import PyTessBaseAPI, RIL 
# from tesserocr import PyTessBaseAPI, PSM,image_to_text,OEM
# from logzero import logger


# import local_tools
# redis_ip,redis_port = local_tools.lookup('redis')

# r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
# binary_r = redis.StrictRedis(host=redis_ip, port=str(redis_port))



# @attr.s 
# class GlworbSelection():
#     source_uuid = attr.ib()
#     key_contents= attr.ib()
#     key_name = attr.ib()
#     working_file= attr.ib()
#     working_metadata = attr.ib()
#     errors= attr.ib()


# #def starti(glworb_uuid:str,glworb_key:str,prefix:str="glworb:",*args) -> GlworbSelection:
# def pipe_starti(glworb_uuid,glworb_key,prefix="glworb:",*args):
#     """Load image bytes, start of pipe
        
#         Args:
#             glworb_uuid(str): glworb uuid
#             glworb_key(str): hash key to use
#             prefix(str): db key prefix, default is "glworb:"
        
#         Returns:
#             GlworbSelection:
#     """
#     logger.info(sys._getframe().f_code.co_name)
#     #Pillow cannot in general close and reopen a file, so any access to that file needs to be prior to the close.
#     errors = []

#     bytes_key = r.hget(prefix+glworb_uuid, glworb_key)
#     if bytes_key is None:
#         logger.warn("retrieved {} from {}".format(bytes_key,glworb_key))
#         logger.warn("did you mean: {}".format(r.hkeys(prefix+glworb_uuid)))
#     else:
#         logger.info("{} field {} has {}".format(prefix+glworb_uuid,glworb_key,bytes_key))

#     key_bytes = binary_r.get(bytes_key)

#     #leave file open until end of pipe
#     file = BytesIO(key_bytes)

#     gs = GlworbSelection(glworb_uuid,Image.open(file),glworb_key,file,dict({}),errors)
#     gs.working_metadata['preserve_format'] = gs.key_contents.format

#     return gs

# #def endi(gs: GlworbSelection,*args)-> GlworbSelection:
# def pipe_endi(gs,*args):
#     """End of image pipe, write and close

#         Args:
#             gs(GlworbSelection): active GlworbSelection
#             *args: args
        
#         Returns:
#             GlworbSelection:
#     """

#     logger.info(sys._getframe().f_code.co_name)
#     binary_prefix="glworb_binary:"
#     prefix="glworb:"

#     file = BytesIO()
#     extension =gs.working_metadata['preserve_format']
#     gs.key_contents.save(file,extension)
#     gs.key_contents.close()
#     file.seek(0)
#     contents = file.read()
#     k = prefix+gs.source_uuid
#     bytes_key = r.hget(k, gs.key_name)
#     print("bytes key is......",bytes_key)
#     binary_r.set(bytes_key, contents)
#     file.close()
#     gs.working_file.close()
#     print("endi",bytes_key)

#     return "done!"

# #def show(gs: GlworbSelection,*args):
# def pipe_show(gs,*args):
#     """Display image

#         Args:
#             gs(GlworbSelection): active glworbselection
#             *args:

#         Returns:
#             GlworbSelection:
#     """
#     logger.info(sys._getframe().f_code.co_name)
#     gs.key_contents.show()
#     return gs

# #crops as partials...
# #def cropto(gs: GlworbSelection,x1:float,y1:float,w:float,h: float,to_key:str,*args) -> bytes:
# def pipe_pcropto(gs,x1,y1,w,h,to_key,*args):
#     """Crop selection from gs to new key

#         Args:
#             gs(GlworbSelection): active glworbselection
#             x1(float): starting x coordinate
#             y1(float):  starting y coordinate
#             w(float): width
#             h(float): height
#             to_key: key to store crop
#             *args:

#         Returns:
#             GlworbSelection:
#     """
#     print(sys._getframe().f_code.co_name)
#     x1 = float(x1)
#     y1 = float(y1)
#     w = float(w)
#     h = float(h)

#     width, height = gs.key_contents.size
#     x1 *= width
#     y1 *= height
#     w  *= width
#     h  *= height
    
#     box = (x1,y1,x1+w,y1+h)
#     region = gs.key_contents.crop(box)

#     file = BytesIO()
#     extension = gs.working_metadata['preserve_format']
#     region.save(file,extension)
#     file.seek(0)
#     contents = file.read()
#     g_uuid = str(uuid.uuid4())
#     bytes_key = "glworb_binary:{}".format(g_uuid)
#     binary_r.set(bytes_key, contents)
#     k = "glworb:"+gs.source_uuid
#     r.hset(k,to_key,bytes_key)
#     #region.show()
#     region.close()
#     file.close()

#     return gs

# def pipe_cropto(gs,x1,y1,w,h,to_key,*args):
#     """Crop selection from gs to new key

#         Args:
#             gs(GlworbSelection): active glworbselection
#             x1(float): starting x coordinate
#             y1(float):  starting y coordinate
#             w(float): width
#             h(float): height
#             to_key: key to store crop
#             *args:

#         Returns:
#             GlworbSelection:
#     """
#     print(sys._getframe().f_code.co_name)
#     x1 = float(x1)
#     y1 = float(y1)
#     w = float(w)
#     h = float(h)
#     box = (x1,y1,x1+w,y1+h)
#     region = gs.key_contents.crop(box)

#     file = BytesIO()
#     extension = gs.working_metadata['preserve_format']
#     region.save(file,extension)
#     file.seek(0)
#     contents = file.read()
#     g_uuid = str(uuid.uuid4())
#     bytes_key = "glworb_binary:{}".format(g_uuid)
#     binary_r.set(bytes_key, contents)
#     k = "glworb:"+gs.source_uuid
#     r.hset(k,to_key,bytes_key)
#     #region.show()
#     region.close()
#     file.close()

#     return gs
# #def crop(gs: GlworbSelection,x1:float,y1:float,x2:float,y2: float,*args) -> bytes:
# def pipe_crop(gs,x1,y1,x2,y2,*args):
#     """Crop in place

#         Args:
#             gs(GlworbSelection): active glworbselection
#             x1(float): starting x coordinate
#             y1(float):  starting y coordinate
#             x2(float): width
#             y2(float): height
#             *args:

#         Returns:
#             GlworbSelection:
#     """
#     print(sys._getframe().f_code.co_name)
#     #left upper right lower
#     #(x, y, w, h)
#     x1 = float(x1)
#     y1 = float(y1)
#     w = float(w)
#     h = float(h)
#     box = (x1,y1,x1+w,y1+h)    #box = floats#(x1, y1, x2, y2)
#     region = gs.crop(box)
#     gs.key_contents = region
#     return gs

# #def rotate(gs: GlworbSelection, rotation:float,*args):
# def pipe_rotate(gs, rotation,*args):
#     """Rotate in place

#         Args:
#             gs(GlworbSelection): active glworbselection
#             rotation(float): starting x coordinate
#             *args:

#         Returns:
#             GlworbSelection:
#     """    
#     print(sys._getframe().f_code.co_name)
#     gs.key_contents = gs.key_contents.rotate(float(rotation),expand=True)
#     return gs

# #def orientation(gs: GlworbSelection,*args):
# def pipe_orientation(gs,*args):
#     """Calculate text orientation using tesseract

#         Args:
#             gs(GlworbSelection): active glworbselection
#             *args:

#         Returns:
#             GlworbSelection:
#     """    
#     print(sys._getframe().f_code.co_name)

#     with PyTessBaseAPI(psm=PSM.AUTO_OSD) as api:
#         image = gs.key_contents
#         #image = Image.open("/usr/src/tesseract/testing/eurotext.tif")
#         api.SetImage(image)
#         api.Recognize()

#         it = api.AnalyseLayout()
#         orientation, direction, order, deskew_angle = it.Orientation()
#         logger.info("Orientation: {:d}".format(orientation))
#         logger.info("WritingDirection: {:d}".format(direction))
#         logger.info("TextlineOrder: {:d}".format(order))
#         logger.info("Deskew angle: {:.4f}".format(deskew_angle))

#     #needs 4.0
#     #https://github.com/tesseract-ocr/tesseract/wiki/4.0-with-LSTM
#     """
#     with PyTessBaseAPI(psm=PSM.OSD_ONLY, oem=OEM.LSTM_ONLY) as api:
#         #api.SetImageFile("/usr/src/tesseract/testing/eurotext.tif")
#         image = gs.key_contents
#         api.SetImage(image)

#         os = api.DetectOrientationScript()
#         print ("Orientation: {orient_deg}\nOrientation confidence: {orient_conf}\n"
#                "Script: {script_name}\nScript confidence: {script_conf}").format(**os)
#     return gs
#     """

# #def ocr(gs: GlworbSelection,ocr_results_key:str,*args):
# def pipe_ocr(gs,ocr_results_key,*args):
#     """Optical Character Recognition(OCR) using tesseract

#         Args:
#             gs(GlworbSelection): active glworbselection
#             ocr_results_key(str): key to store ocr results
#             *args:

#         Returns:
#             GlworbSelection:
#     """        
#     print(sys._getframe().f_code.co_name)

#     print(image_to_text(gs.key_contents))

#     """
#     #image = Image.open('/usr/src/tesseract/testing/phototest.tif')
#     image = gs.key_contents
#     with PyTessBaseAPI() as api:
#         api.SetImage(image)
#         boxes = api.GetComponentImages(RIL.TEXTLINE, True)
#         print 'Found {} textline image components.'.format(len(boxes))
#         for i, (im, box, _, _) in enumerate(boxes):
#             # im is a PIL image object
#             # box is a dict with x, y, w and h keys
#             api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
#             ocrResult = api.GetUTF8Text()
#             conf = api.MeanTextConf()
#             print ("Box[{0}]: x={x}, y={y}, w={w}, h={h}, "
#                    "confidence: {1}, text: {2}").format(i, conf, ocrResult, **box)
#     """
#     return gs

