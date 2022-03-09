import logging
import sys

from enum import Enum
from typing import Dict, Any
from devices.bus_manager import BusManager

log = logging.getLogger(__name__)


class DriverTypes(Enum):
    emulated = 0
    pca9685 = 1


class DriverInfo(object):
    def __init__(self, channel, offset, resolution):
        self.channel = channel
        self.offset = offset
        self.resolution = resolution
        self.duty_cycle = 0
        self.pwm_value = 0
        self.locked = False
        self.locker = []

    def lock(self, locker):
        self.locked = True
        if locker not in self.locker:
            self.locker.append(locker)

    def unlock(self, locker):
        if locker in self.locker:
            self.locker.remove(locker)

        if len(self.locker) == 0:
            self.locked = False

    def set_dc(self, dc):
        dc = int(dc)
        self.duty_cycle = dc
        self.pwm_value = int((dc/100) * self.resolution)


class PwmInterface(object):
    drivers: Dict[Any, DriverInfo]
    bus: BusManager

    def __init__(self, dev_name, bus, **kwargs):
        self.bus = bus
        self.drivers = {}
        self.dev_name = dev_name
        self.ramp_up_power_step = kwargs["ramp_up_dc_step"]
        self.ramp_up_delay = kwargs["ramp_up_delay_seconds"]

    def lock(self, dev_id, locker):
        self.set_duty_cycle(dev_id, 0)
        self.drivers[dev_id].lock(locker)

    def unlock(self, dev_id, locker):
        self.drivers[dev_id].unlock(locker)

    def init_device(self):
        pass

    def close_device(self):
        pass

    def set_duty_cycle(self, dev_id, dc):
        pass


def loader(dev_name, dev_type, bus, **cfg):
    device = None
    if dev_type == DriverTypes.emulated:
        if 'EmulatedPwm' not in sys.modules:
            from devices.pwm_devices.emulated import EmulatedPwm
        device = EmulatedPwm(dev_name, bus, **cfg)
    elif dev_type == DriverTypes.pca9685:
        if 'PCA9685Interface' not in sys.modules:
            from devices.pwm_devices.pca9685_interface import PCA9685Interface
        device = PCA9685Interface(dev_name, bus, **cfg)
    return device
