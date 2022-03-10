import logging
import json

from os import path


def check_path(config_file):
    return path.exists(config_file)


def read_config(config_file):
    logging.info(f"Loading {config_file}")
    config = {}

    if "emulate" in config_file:
        f_name = path.join("config", "emulation", config_file)
    else:
        f_name = path.join("config", config_file)

    with open(f_name, "r") as f:
        try:
            config = json.load(f)
        except Exception as ex:
            logging.error(f"Problem loading config.json, {ex}")
        f.close()
    return config
