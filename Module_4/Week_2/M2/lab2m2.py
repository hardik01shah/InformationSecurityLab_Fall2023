import json
import logging
import sys
import os
import socket
from schnorr import Schnorr, Schnorr_Params
from sage.all import matrix, vector, ZZ
from matplotlib import pyplot as plt

# Change the port to match the challenge you're solving
PORT = 40220

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

# Parameters of the P-256 NIST curve
a   = 0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc
b   = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
p   = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
P_x = 0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296
P_y = 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5
q   = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551

nistp256_params = Schnorr_Params(a, b, p, P_x, P_y, q)
schnorr = Schnorr(nistp256_params)

num_leaked_bits = 8
max_querries = 60
NUM_SIGNATURES = 10000
store = {}
t_sum = 0
times = []

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
# plt.scatter([*range(len(times))], times)
# plt.savefig("times.png")
# plt.show()

N = q.bit_length()
L = num_leaked_bits
n = max_querries
B = matrix.identity(ZZ, n+1) * schnorr.q
B[-1,-1] = 1

U = vector(ZZ, n+2)
M = int(((n+1)*(2**(2*(N-(L+1)))))**(0.5))

for i in range(max_querries):
    time = time_list[i]
    h, s, _ = store[time]

    h = schnorr.Z_q(h)
    s = schnorr.Z_q(s)
    u = 2**(N - L - 1) - s

    B[n, i] = h
    U[i] = u

U = U*(2**(L+1))
M = M*(2**(L+1))
B = B*(2**(L+1))
B[-1,-1] = 1

B_p = matrix(ZZ, n+2, n+2)
B_p[:n+1, :n+1] = B
B_p[n+1, :] = U
B_p[n+1, n+1] = M

B_p = B_p.LLL()
norms = []
# get 2nd min norm index
for i in range(n+2):
    norms.append(B_p[i].norm())
norms_sorted = sorted(norms)
min2_norm = norms_sorted[1]
indx = norms.index(min2_norm)

f = B_p.LLL()[indx][:-1]
v = U[:-1] - f

priv_key = schnorr.Z_q(v[-1])
msg = "gimme the flag"
h, s = schnorr.Sign_Deterministic(priv_key, msg)

json_send({"command": "solve", "h": int(h), "s": int(s)})
print(json_recv())