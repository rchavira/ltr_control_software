import logging
import json

from os import path


def check_path(config_file):
    return path.exists(config_file)


def read_config(config_file):
    logging.info(f"Loading {config_file}")
    config = {}
    with open(path.join("config", config_file), "r") as f:
        try:
            config = json.load(f)
        except Exception as ex:
            logging.error(f"Problem loading config.json, {ex}")
        f.close()
    return config
