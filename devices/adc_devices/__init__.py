import sys
from enum import Enum
from typing import Dict, Any

from devices.bus_manager import BusManager


class AdcDeviceTypes(Enum):
    emulated = 0
    max1168 = 1


class AdcInfo(object):
    def __init__(self, channel, dev, min_val, max_val, resolution):
        self.device_id = dev
        self.min_val = min_val
        self.max_val = max_val
        self.channel = channel
        self.raw_value = 0
        self.value = 0.0
        self.resolution = resolution

    def set_value(self, value):
        self.raw_value = value
        o_scale = float(value / self.resolution)
        n_range = float(self.max_val - self.min_val)
        self.value = float(o_scale * n_range + self.min_val)


class AdcInterface(object):
    channels: Dict[Any, AdcInfo]
    bus_mgr: BusManager

    def __init__(self):
        self.channels = {}
        self.resolution = 0
        self.bus_mgr = None
        self.chip_select = None
        self.cs = 0

    def init_device(self):
        pass

    def close_device(self):
        pass

    def read_channel(self, dev_id):
        pass


def loader(dev_type, dev_name, bus, ch_sel, **cfg):
    device = None
    if dev_type == AdcDeviceTypes.emulated:
        if "EmulatedAdc" not in sys.modules:
            from devices.adc_devices.emulated import EmulatedAdc
        device = EmulatedAdc(dev_name, bus, **cfg)
    elif dev_type == AdcDeviceTypes.max1168:
        if "Max1168Interface" not in sys.modules:
            from devices.adc_devices.max1168_interface import Max1168Interface
        device = Max1168Interface(dev_name, bus, ch_sel, **cfg)
    return device
