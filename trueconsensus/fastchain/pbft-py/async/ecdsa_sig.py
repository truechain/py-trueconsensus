import sys, os
import ecdsa
import pickle
import config

C = ecdsa.NIST256p
SIG_SIZE = 64
HASH_SIZE = 32

def generate_keys():
    sk = ecdsa.SigningKey.generate(curve = C)
    vk = sk.get_verifying_key()
    return sk, vk

def sign(key, message):
    return key.sign(message)
    
def verify(key, sig, message):
    try:
        rc = key.verify(sig, message)
        return rc
    except:
        return False

def write_new_keys(n):
    if not os.path.isdir(config.KD):
        os.mkdir(config.KD)
    for i in range(0,n):
        s_file = open(config.KD+"/sign" + str(i) + ".pem", 'wb')
        v_file = open(config.KD+"/verify" + str(i) + ".pem", 'wb')
        sk, vk = generate_keys()
        s_file.write(sk.to_pem())
        v_file.write(vk.to_pem())
    s_file.close()
    v_file.close()
    
def get_signing_key(i):
    if not os.path.isfile(config.KD + "/sign" + str(i) + ".pem"):
        print "can't find key file: " + "keys/sign" + str(i) + ".pem"
        sys.exit(0)
    f = open(config.KD + "/sign" + str(i) + ".pem", 'rb')
    key_pem = f.read()
    f.close()
    return ecdsa.SigningKey.from_pem(key_pem)
   
def get_verifying_key(i):
    if not os.path.isfile(config.KD + "/verify" + str(i) + ".pem"):
        print "can't find key file: " + config.KD+"/verify" + str(i) + ".pem"
        sys.exit(0)
    f = open(config.KD + "/verify" + str(i) + ".pem", 'rb')
    key_pem = f.read()
    f.close()
    return ecdsa.VerifyingKey.from_pem(key_pem)
    
def read_keys_test(n):
    if not os.path.isdir(config.KD):
        print "Can't find key directory"
        sys.exit(0)
    s = []
    v = []
    for i in range(0,n):
        s.append(ecdsa.SigningKey.from_pem(open(config.KD+"/sign" + str(i) + ".pem", "rb").read()))
        v.append(ecdsa.VerifyingKey.from_pem(open(config.KD+"/verify" + str(i) + ".pem", "rb").read()))
    
    #test
    for i in range(0,n):
        sig = s[i].sign("message" + str(i))
        ver = v[i].verify(sig, "message" + str(i))
        if not ver:
            print "ERROR SOMEWHERE " + str(i)
        else:
            print "Round " + str(i) + " succeeded"
    
    
if __name__ == "__main__":
    write_new_keys(10)
    read_keys_test(10)
