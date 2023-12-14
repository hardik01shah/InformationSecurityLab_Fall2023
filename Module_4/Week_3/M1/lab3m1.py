import json
import logging
import sys
import os
import socket
from sage.all import Zmod, PolynomialRing, matrix, ZZ, ideal, QQ, Integer 
from math import log2, ceil, gcd
from Crypto.Hash import SHA256

# Change the port to match the challenge you're solving
PORT = 40310

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

# generate new keys with different bit length
def gen_key(bit_length, identifier):
    json_send({"command": "gen_key", "bit_length": bit_length, "identifier": identifier})
    return json_recv()

# get the public keys
def get_pubkey(identifier):
    json_send({"command": "get_pubkey", "identifier": identifier})
    return json_recv()

gen_key(512, "key1")
gen_key(2048, "key1")

pub_key = get_pubkey("key1")

# get p
json_send({"command": "export_p", "identifier": "key1"})
recv1 = json_recv()

obfuscated_p = recv1["obfuscated_p"]

# 768 LSB of 1024 bit p leaked
p_ = int(bytes.fromhex(obfuscated_p[512:]), 2)

N = int(pub_key["n"])
e = int(pub_key["e"])

R = PolynomialRing(Zmod(N), 1, 'x')
x = R.gen()
F = (2**768)*x + p_

# make the polynomial monic
F = (F*((Zmod(N)(2**768))**(-1)))
P = F.change_ring(ZZ)

assert P.coefficient({x:1}) == 1
p_ = P.coefficient({x:0})

# construct B
B = matrix(ZZ, 4, 4)
X = Integer(2**256)

B[0,0] = N
B[1,0] = p_
B[1,1] = X
B[2,1] = p_*X
B[2,2] = X**2
B[3,2] = p_*(X**2)
B[3,3] = X**3

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
x0 = None
for root in roots:
    if int(root['x']) < int(X):
        x0 = int(root['x'])
        break

p = gcd(int(p_) + x0, int(N))
q = int(N//p)

assert p*q == N

phi = (p-1) * (q-1)
Zphi = Zmod(phi)
d = 1/Zphi(e)
h = int.from_bytes(SHA256.new(b"gimme the flag").digest())
s = Zmod(N)(h)**d

# solve
json_send({"command": "solve", "identifier": "key1", "signature": int(s)})

# receive flag
print(json_recv())