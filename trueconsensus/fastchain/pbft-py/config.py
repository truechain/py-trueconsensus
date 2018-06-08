import os

import yaml
import logging
import configparser
# from subprocess import check_output
# from pykwalify import core as pykwalify_core
# from pykwalify import errors as pykwalify_errors
from logging.handlers import RotatingFileHandler

from local_config import CFG_YAML_PATH, \
    CFG_GENERAL_PATH, \
    PEER_NETWORK_FILE


def load_config(path, no_val=False):
    """
    general logistics such as log file paths in logistics CFG
    """
    if no_val:
        config = configparser.ConfigParser(allow_no_value=True)
    else:
        config = configparser.ConfigParser()
    config.read(path)

    return config


def load_yaml_config(path, no_val=False):
    """
    general tunables specified in YAML
    """
    with open(path, "r") as config_file:
        pbft_config = yaml.safe_load(config_file)

    _logger.debug("PBFT config {} yaml loaded".format(path))

    # # Validate base config for Browbeat format
    # _validate_yaml("pbft", pbft_config)
    # _logger.info("Config {} validated".format(path))
    return pbft_config

#
# def _validate_yaml(schema, config):
#     """Raises exception if config is invalid.
#     :param schema: The schema to validate with (pbft, pow, hybrid...)
#     :param config: Loaded yaml to validate
#     """
#     check = pykwalify_core.Core(
#         source_data=config,
#         schema_files=["{}/{}.yml".format(conf_schema_path, schema)])
#     try:
#         check.validate(raise_exception=True)
#     except pykwalify_errors.SchemaError as e:
#         _logger.error("Schema validation failed")
#         raise Exception("File does not conform to {} schema: {}".format(schema, e))


config_general = load_config(CFG_GENERAL_PATH)

LOG_ROOT = config_general.get("log", "root_folder")
# import pdb; pdb.set_trace()
FNAME = config_general.get("log", "server_logfile")
FSIZE = int(config_general.get("log", "max_log_size"))

try:
    if not os.path.exists(LOG_ROOT):
        os.makedirs(LOG_ROOT)
except PermissionError:
    quit("[Permission Denied] during creation of log file dir: %s" % LOG_ROOT)
except Exception as E:
    quit("Error: [%s] - Couldn't create log file dir: %s" % (E, LOG_ROOT))

FMT = "[%(asctime)s] [%(levelname)s ] " + \
      "[%(filename)s:%(lineno)d:%(funcName)s()] - %(message)s"

_logger = logging.getLogger(__name__)

formatter = logging.Formatter(FMT)
handler = RotatingFileHandler(
    os.path.join(LOG_ROOT, FNAME),
    maxBytes=FSIZE,
    backupCount=1
)
handler.setFormatter(formatter)
_logger.root.level = logging.DEBUG
_logger.addHandler(handler)


# _logger = logging.getLogger("pbftx.config")

print("Storing logs to file: %s" % FNAME)

config_yaml = load_yaml_config(CFG_YAML_PATH)

IP_LIST = [l.strip() for l in open(PEER_NETWORK_FILE, 'r').read().split('\n') if l]
# total = len(IP_LIST)

KD = config_general.get("general", "pem_keystore_path")

# import pdb; pdb.set_trace()
basePort = config_yaml["general"]["base_port"]
N = config_yaml['nodes']['total']

client_id = config_yaml["nodes"]["client_id"]

# replica list
RL = [(l, basePort+i) for i, l in enumerate(IP_LIST[:client_id])]
# We reserve the last IP as the client
client_address = ((IP_LIST[client_id], basePort+client_id))

# threading_enabled = True
threading_enabled = False
