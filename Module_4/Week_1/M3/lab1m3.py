import json
import logging
import sys
import os
import socket
from matplotlib import pyplot as plt

# Change the port to match the challenge you're solving
PORT = 40130

# Pro tip: for debugging, set the level to logging.DEBUG if you want
# to read all the messages back and forth from the server
# log_level = logging.DEBUG
log_level = logging.INFO
logging.basicConfig(stream=sys.stdout, level=log_level)

s = socket.socket()

# Set the environmental variable REMOTE to True in order to connect to the server
#
# To do so, run on the terminal:
# REMOTE=True sage solve.py
#
# When we grade, we will automatically set this for you
if "REMOTE" in os.environ:
    s.connect(("isl.aclabs.ethz.ch", PORT))
else:
    s.connect(("localhost", PORT))

fd = s.makefile("rw")


def json_recv():
    """Receive a serialized json object from the server and deserialize it"""

    line = fd.readline()
    logging.debug(f"Recv: {line}")
    return json.loads(line)

def json_send(obj):
    """Convert the object to json and send to the server"""

    request = json.dumps(obj)
    logging.debug(f"Send: {request}")
    fd.write(request + "\n")
    fd.flush()

# WRITE YOUR SOLUTION HERE
# 2000 - 96%
# 2100 - 97%
NUM_SIGNATURES = 4000
store = {}
t_sum = 0
times = []
scores = []
for i in range(NUM_SIGNATURES):
    json_send({"command": "get_signature"})
    recv1 = json_recv()
    h = recv1["h"]
    s = recv1["s"]
    msg = recv1["msg"]
    time = recv1["time"]    

    store[time] = (h, s, msg)

    t_sum += time
    times.append(time)

time_list = list(store.keys())
time_list.sort()
time_list = time_list[:20]

msgs = []
for t in time_list:
    msgs.append(store[t][2])

json_send({"command": "solve", "messages": msgs})
print(json_recv())

# plt.scatter([*range(len(times))], times, label="time")
# t_avg = t_sum/len(times)
# scores = [t_avg - t for i, t in enumerate(times)]
# plt.scatter([*range(len(scores))], scores, label="score")
# plt.legend()
# plt.show()
