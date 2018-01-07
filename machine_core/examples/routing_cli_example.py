# Simple routing with cli interaction using curses:
#     Setup routes
#     Setup listener for message
#     Press SPACE to send message
#     Press Q or q to exit

import curses
import sys
sys.path.insert(0,"../")
import routeling
import routeling_basic_operations
#zerorpc-tools has echo...
import local_tools
import threading
import redis
import time

stdscr = curses.initscr()
curses.noecho()
stdscr.keypad(True)
curses.cbreak()


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
            #assert item['data'] == listen_for
            #break
            if item['data'] == 'quit':
                break

message  = "hello world"
endpoint = "/baz"
t = threading.Thread(name='listener', target=listen,args=(endpoint,message,))
print("starting listener thread")
t.start()

example_route_1 = "if '/foo' do mapii '/bar'"
example_route_2 = "if '/bar' do mapii '/baz'"
routeling.add_route(example_route_1)
routeling.add_route(example_route_2)

while True:
    stdscr.addstr(0,0,"Press SPACE to send message. Q or q to exit...")
    x = stdscr.getkey()
    if x == ' ':
        routeling_basic_operations.sendi('/foo',message)

    if x in 'qQ':
        routeling_basic_operations.sendi('/foo','quit')
        break

curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()
t.join()

print("removing routes")
routeling.remove_route(example_route_1)
routeling.remove_route(example_route_2)
