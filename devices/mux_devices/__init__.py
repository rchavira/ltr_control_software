import sys

from enum import Enum
from devices.dio_devices import DioInterface


class MuxDeviceTypes(Enum):
    emulated = 0
    cd451x = 1


class MuxDeviceInterface(object):
    dio: DioInterface

    def __init__(self, dio, **kwargs):
        self.dio = dio
        self.inputs = {}
        self.outputs = {}

    def encode(self, output_ch):
        pass

    def decode(self, output_ch):
        pass


def loader(dev_type, dio, **cfg):
    device = None
    if dev_type == MuxDeviceTypes.emulated:
        if 'EmulatedMux' not in sys.modules:
            from devices.mux_devices.emulated import EmulatedMux
        device = EmulatedMux(dio, **cfg)
    elif dev_type == MuxDeviceTypes.cd451x:
        if 'CD4515Interface' not in sys.modules:
            from devices.mux_devices.cd451xInterface import CD4515Interface
        device = CD4515Interface(dio, **cfg)

    return device
