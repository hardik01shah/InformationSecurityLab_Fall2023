import json
import logging
import sys
import os
import socket
from sage.all import Zmod, PolynomialRing, matrix, ZZ, ideal, QQ, Integer 

# Change the port to match the challenge you're solving
PORT = 40300

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

# get public key
json_send({"command": "get_pubkey"})
recv = json_recv()
n = Integer(recv["n"])
e = Integer(recv["e"])

# send command to get ciphertext
json_send({"command": "get_ciphertext"})

# receive ciphertext
recv = json_recv()
ciphertext = int.from_bytes(bytes.fromhex(recv["ciphertext"]))

padding = int.from_bytes(bytes([111] * 111))

R = PolynomialRing(Zmod(n), 1, 'x')
x = R.gen()
F = ((2**888)*x + padding)**e - ciphertext

# make the polynomial monic
F = (F*((Zmod(n)(2**888))**(-e)))
P = F.change_ring(ZZ)
assert P.coefficient({x:3}) == 1

# construct B
B = matrix(ZZ, 4, 4)
X = Integer(2**128)
B[0,0] = n
B[1,1] = n*X
B[2,2] = n*(X**2)
B[3,3] = X**3
B[3,0] = P.coefficient({x:0})
B[3,1] = P.coefficient({x:1})*X
B[3,2] = P.coefficient({x:2})*(X**2)

B = B.LLL()

# get min norm index
norms = []
for i in range(4):
    norms.append(B[i].norm())
norms_sorted = sorted(norms)
min_norm = norms_sorted[0]
indx = norms.index(min_norm)

coeffs = B[indx]
R = PolynomialRing(ZZ, 1, 'x')
x = R.gen()
P_new = int(coeffs[3]/X**3)*x**3 + int(coeffs[2]/X**2)*x**2 + int(coeffs[1]/X)*x + coeffs[0]
I = ideal(P_new.change_ring(QQ))

# get roots
roots = I.variety(ring=ZZ)
secret = None
for root in roots:
    if int(root['x']) < int(X):
        secret = int(root['x'])
        break
num_bytes = (secret.bit_length() + 7) // 8
secret = secret.to_bytes(num_bytes, byteorder='big').decode('ascii')

# send command to solve
json_send({"command": "solve", "message": secret})

# receive flag
print(json_recv())