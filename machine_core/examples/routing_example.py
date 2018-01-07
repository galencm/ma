# Simple routing example:
#     Setup two routes where the endpoint of the 
#     first route is the starpoint of the second

#     start a thread to listen on second endpoint
#     for a specific message

#     send message using routling and exit when
#     received...
import sys
sys.path.insert(0,"../")
import routeling
import routeling_basic_operations
#zerorpc-tools has echo...
import local_tools
import threading
import redis
import time

def listen(listen_on,listen_for):
    print("listening for {}".format(repr(listen_for)))
    redis_ip,redis_port = local_tools.lookup('redis')
    r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe(listen_on)
    for item in pubsub.listen():
        #1 signals channel sub
        if item['data'] != 1:
            #{'pattern': None, 'data': 'hello world', 'channel': '/baz', 'type': 'message'}
            print("received {} on {}".format(item['data'],item['channel']))
            assert item['data'] == listen_for
            break

message = "hello world"
endpoint = "/baz"
startpoint = "/foo"
print("""Routing example:
         Add routes: 
             /foo to /bar
             /bar to /baz
         
         Starts a thread to listen on {endpoint} for message

         Send message {message} to {startpoint}

         When message is received:
            remove routes
            exit
      """.format(endpoint=endpoint,message=message,startpoint=startpoint))

t = threading.Thread(name='listener', target=listen,args=(endpoint,message,))
print("starting listener thread")
t.start()

example_route_1 = "if '/foo' do mapii '/bar'"
example_route_2 = "if '/bar' do mapii '/baz'"
routeling.add_route(example_route_1)
routeling.add_route(example_route_2)
routeling_basic_operations.sendi(startpoint,message)

# there is a slight latency for routing
# so do not remove routes immediately
time.sleep(1)
print("removing routes")
routeling.remove_route(example_route_1)
routeling.remove_route(example_route_2)
t.join()
print("exiting")