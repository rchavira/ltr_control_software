"""
Digital IO Interface
"""
import sys
import logging

from system_control import ControllerDeviceTypes

log = logging.getLogger(__name__)


class DioInterface(object):
    def __init__(self, **kwargs):
        self.input_pins = {}
        self.output_pins = {}

    def init_device(self):
        pass

    def close_device(self):
        pass

    def write_digital(self, pin, set_high=False):
        pass

    def read_digital(self, pin):
        pass


def loader(dev_type, **cfg):
    # log.debug(f"Loading Device Type: {dev_type}")
    device = None
    if dev_type == ControllerDeviceTypes.emulated:
        if 'EmulatedIO' not in sys.modules:
            from devices.dio_devices.emulated import EmulatedIO
        device = EmulatedIO(**cfg)
    elif dev_type == ControllerDeviceTypes.raspi:
        if 'RaspiDio' not in sys.modules:
            from devices.dio_devices.raspi_dio import RaspiDio
        device = RaspiDio(**cfg)

    return device
