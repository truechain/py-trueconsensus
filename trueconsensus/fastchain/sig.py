import os
import sys
import ecdsa
import hmac
import hashlib
from trueconsensus.fastchain import config

MAC_SIZE = 32
HASH_SIZE = 32
KEY_SIZE = 32


def generate_key():
    return os.urandom(KEY_SIZE)


def sign(key, message):
    h = hmac.new(key, message, hashlib.sha256)
    return h.digest()


def verify(key, dig1, bytes):
    h = hmac.new(key, bytes, hashlib.sha256)
    # return hmac.compare_digest(dig1, h.digest())
    return dig1 == h.digest()


def write_new_keys(n):
    if not os.path.isdir(config.KD):
        os.mkdir(config.KD)
    for i in range(0, n):
        s_file = open(config.KD+"/sign" + str(i) + ".dat", 'wb')
        sk = generate_key()
        s_file.write(sk)
        s_file.close()

def get_signing_key(i):
    if not os.path.isfile(config.KD + "/sign" + str(i) + ".dat"):
        print("can't find key file: " + "keys/sign" + str(i) + ".dat")
        sys.exit(0)
    f = open(config.KD + "/sign" + str(i) + ".dat", 'rb')
    sk = f.read()
    f.close()
    return sk

def read_keys_test(n):
    if not os.path.isdir(config.KD):
        print("Can't find key directory")
        sys.exit(0)
    s = []
    v = []
    for i in range(0, n):
        s.append(ecdsa.SigningKey.from_pem(open(config.KD+"/sign" + str(i) + ".pem", "rb").read()))
        v.append(ecdsa.VerifyingKey.from_pem(open(config.KD+"/verify" + str(i) + ".pem", "rb").read()))

    # test
    for i in range(0, n):
        sig = s[i].sign("message" + str(i))
        ver = v[i].verify(sig, "message" + str(i))
        if not ver:
            print("ERROR SOMEWHERE " + str(i))
        else:
            print("Round " + str(i) + " succeeded")


if __name__ == "__main__":
    N = int(sys.argv[1])
    write_new_keys(N)
    read_keys_test(N)
