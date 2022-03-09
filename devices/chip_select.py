import logging
import sys

from enum import Enum
from threading import Thread
from time import sleep, time

from devices.dio_devices import DioInterface
from devices.mux_devices import MuxDeviceInterface, MuxDeviceTypes, loader

log = logging.getLogger(__name__)

default_config = {
    "device_type": "emulated",
    "cs_reset": 15,
    "config": {
        "pinA": 17,
        "pinB": 27,
        "pinC": 22,
        "pinD": 5,
        "strobe": 23,
        "strobe_delay": 0.5
    }
}


class ChipSelector(object):
    dio: DioInterface
    device: MuxDeviceInterface

    def __init__(self, dio, **kwargs):
        self.cs_reset = kwargs["cs_reset"]
        self.dio = dio
        self.device = None
        device_type = MuxDeviceTypes[kwargs["device_type"]]

        self.device = loader(device_type, self.dio, **kwargs["config"])

    def chip_select(self, channel):
        self.device.encode(channel)

    def reset(self):
        self.device.encode(self.cs_reset)
