import json
import logging
import sys
import os
import socket
from ecdsa2 import ECDSA2_Params, ECDSA2, Point, bits_to_int, hash_message_to_bits
import time
import random

# Change the port to match the challenge you're solving
PORT = 40120

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

nistp256_params = ECDSA2_Params(a, b, p, P_x, P_y, q)
ecdsa = ECDSA2(nistp256_params)

store = {}
privkey = None
k = None

while True:

    cur_m = "dummy"+str(random.randint(0, 10000000000))
    json_send({"command": "get_signature", "msg": cur_m})
    recv1 = json_recv()

    r = ecdsa.Z_q(recv1["r"])
    s = ecdsa.Z_q(recv1["s"])

    if r not in store:
        store[r] = [s, cur_m]
    else:
        h1 = bits_to_int(hash_message_to_bits(store[r][1]), ecdsa.q)
        h2 = bits_to_int(hash_message_to_bits(cur_m), ecdsa.q)

        s1 = store[r][0]
        s2 = s

        num = s2*(h1**2) - s1*(h2**2)
        den = 1337*r*(s1 - s2)

        privkey = ecdsa.Z_q(num*den**(-1))
        k = ecdsa.Z_q(s1**(-1) * (h1**2 - 1337*privkey*r))
        break

h = bits_to_int(hash_message_to_bits("gimme the flag"), ecdsa.q)
r, s = ecdsa.Sign_FixedNonce(k, privkey, "gimme the flag")

# Send the signature
json_send({"command": "solve", "r": int(r), "s": int(s)})
print(json_recv())