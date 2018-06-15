import os
import sys
import hmac
import ecdsa
import hashlib
# import pickle
# import logging
# from trueconsensus.fastchain.config import KD

from fastchain.config import KD, \
    _logger

C = ecdsa.NIST256p
SIG_SIZE = 256
HASH_SIZE = 32
# MAC_SIZE = 32

ASYMM_FILE_FORMATS = {
    "sign": ".pem",
    "verify": ".pub"
}

ASYMM_FUNC_MAP = {
    "sign": ecdsa.SigningKey.from_pem,
    "verify": ecdsa.VerifyingKey.from_pem
}


def generate_keys():
    sk = ecdsa.SigningKey.generate(curve=C)
    vk = sk.get_verifying_key()
    return sk, vk


def sign(key, message):
    return key.sign(message)


def sign_proto_key(key, message):
    # import pdb; pdb.set_trace()
    key = bytes(key.to_string())
    h = hmac.new(key, message, hashlib.sha256)
    return h.digest()


def verify(key, sig, message):
    try:
        rc = key.verify(sig, message)
        return rc
    except Exception as E:
        _logger.error(E)
        return False


def verify_proto_key(key, dig1, message):
    # import pdb; pdb.set_trace()
    key = bytes(key.to_string())
    h = hmac.new(key, message, hashlib.sha256)
    # return hmac.compare_digest(dig1, h.digest())
    return dig1 == h.digest()


def get_key_path(i, ktype):
    try:
        KEY_NAME = ktype + str(i) + ASYMM_FILE_FORMATS[ktype]
        # _logger.info("KPATH - FETCH - %s -- %s" % (ktype, KEY_NAME))
        return os.path.join(KD, KEY_NAME)
    # generic catch
    except Exception as E:
        _logger.error(E)
        return
        # raise


def write_new_keys(n):
    if not os.path.isdir(KD):
        os.mkdir(KD)
    for i in range(0, n):
        s_file = open(get_key_path(i, "sign"), 'wb')
        v_file = open(get_key_path(i, "verify"), 'wb')
        sk, vk = generate_keys()
        s_file.write(sk.to_pem())
        v_file.write(vk.to_pem())
    s_file.close()
    v_file.close()
    msg = "written new keys to %s" % KD
    _logger.info(msg)
    return msg

def get_asymm_key(i, ktype=None):
    kpath = get_key_path(i, ktype)
    found_error = False
    try:
        if not os.path.isfile(kpath):
            result = "File Not Found: %s" % kpath
            _logger.error(result)
            found_error = True
        else:
            key_pem = open(kpath, 'rb').read()
            result = ASYMM_FUNC_MAP[ktype](key_pem)
    except Exception as result:
        found_error = True

    if found_error:
        _logger.error("%s" % result)
        return

    return result
#
# def get_verifying_key(i):
#     kpath = get_key_path(i, "verify")
#     if not os.path.isfile(kpath):
#         _logger.error("can't find key file: ", kpath)
#         sys.exit(0)
#     key_pub = open(kpath, 'rb').read()
#     return ecdsa.VerifyingKey.from_pem(key_pem)


def read_keys_test(n, validate=False):
    if not os.path.isdir(KD):
        _logger.error("Can't find key directory")
        sys.exit(0)
    s = []
    v = []
    for i in range(0, n):
        secret_key = open(get_key_path(i, "sign"), "rb").read()
        public_key = open(get_key_path(i, "verify"), "rb").read()
        s.append(ecdsa.SigningKey.from_pem(secret_key))
        v.append(ecdsa.VerifyingKey.from_pem(public_key))
        if validate:
            assert validate_keypair(i, s[-1], v[-1]) is True
    return s, v


def validate_keypair(i, s, v):
    msg = "message" + str(i)
    sig = s.sign(msg)
    ver = v.verify(sig, msg)
    if not ver:
        _logger.error("Error while reading keypair: " % i)
        return False
    _logger.info("Round succeeded for keypair: " % i)
    return True


if __name__ == "__main__":
    N = int(sys.argv[1])
    write_new_keys(N)
    s, v = read_keys_test(N)
