import os
from subprocess import check_output

import yaml
import logging
import configparser
from logging.handlers import RotatingFileHandler
from pykwalify import core as pykwalify_core
from pykwalify import errors as pykwalify_errors

from local_config import CFG_YAML_PATH, \
    CFG_GENERAL_PATH


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


def _validate_yaml(schema, config):
    """Raises exception if config is invalid.
    :param schema: The schema to validate with (pbft, pow, hybrid...)
    :param config: Loaded yaml to validate
    """
    check = pykwalify_core.Core(
        source_data=config, schema_files=["{}/{}.yml".format(conf_schema_path, schema)])
    try:
        check.validate(raise_exception=True)
    except pykwalify_errors.SchemaError as e:
        _logger.error("Schema validation failed")
        raise Exception("File does not conform to {} schema: {}".format(schema, e))


config_general = load_config(CFG_GENERAL_PATH)

# import pdb; pdb.set_trace()
FNAME = config_general.get('log','pbft_log_file')
FSIZE = int(config_general.get('log',"pbft_log_file_size"))

try:
    if not os.path.exists(os.path.dirname(FNAME)):
        os.makedirs(os.path.dirname(FNAME))
except PermissionError:
    quit("[Permission Denied] during creation of log filepath: %s" % FNAME)
except Exception as E:
    quit("Error: [%s] - Couldn't create log filepath: %s" % (E, FNAME))

FMT = "[%(asctime)s] [%(levelname)s ] " + \
      "[%(filename)s:%(lineno)d:%(funcName)s()] - %(message)s"

_logger = logging.getLogger(__name__)

formatter = logging.Formatter(FMT)
handler = RotatingFileHandler(FNAME, maxBytes=FSIZE, backupCount=1)
handler.setFormatter(formatter)
_logger.root.level = logging.DEBUG
_logger.addHandler(handler)


# _logger = logging.getLogger("pbftx.config")

print("Storing logs to file: %s" % FNAME)

IP_LIST = [l.strip() for l in open(os.path.expanduser('~')+'/hosts','r').read().split('\n') if l]
total = len(IP_LIST)


config_yaml = load_yaml_config(CFG_YAML_PATH)
