import json
import logging
import sys
import os
import socket
from sage.all import Zmod, PolynomialRing, matrix, ZZ, ideal, QQ, Integer 
from math import log2, ceil, gcd
from Crypto.Hash import SHA256

# Change the port to match the challenge you're solving
PORT = 40320

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
N_BIT_LENGTH = 1024
N_BYTE_LENGTH = N_BIT_LENGTH // 8
n = 0x579d4e9590eeb88fd1b640a4d78fcf02bd5c375351cade76b69561d9922d3070d479a67192c67265cf9ae4a1efde400ed40757b0efd2912cbda49e60c83a1ddd361d31859bc4e206158491a528bd46d0b41c6e8d608c586a0788b8027f0f796e9e077766f83683fd52965101bb7bf9fd90c9e9653f02fada8bf10d62bc325ef
a = 17
b = 1

# get encrypted message
json_send({"command": "get_ciphertext"})
recv = json_recv()
ciphertext = recv["ciphertext"]

y = int.from_bytes(bytes.fromhex(ciphertext[256:]))
xk = int.from_bytes(bytes.fromhex(ciphertext[32:256]))

R = PolynomialRing(Zmod(n), 1, 'x')
x = R.gen()
F = (((2**896)*x)+xk)**3 + a*(((2**896)*x)+xk) + b - y**2

# make the polynomial monic
F = (F*((Zmod(n)(2**896))**(-3)))
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

sx = secret*(2**896) + xk
x_coord = (int(sx).to_bytes(N_BYTE_LENGTH)).hex()

secret = bytes(x ^ y for x, y in zip(bytes.fromhex(x_coord[:32]), bytes.fromhex(ciphertext[:32])))

# send secret
json_send({"command": "solve", "plaintext": str(secret.decode())})

# get flag
print(json_recv())