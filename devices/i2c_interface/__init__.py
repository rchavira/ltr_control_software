"""
I2C Interface Prototype
"""
import sys

from devices.communication import BusInterface, BusType
from system_control import ControllerDeviceTypes


class I2CInterface(BusInterface):
    bus_type: BusType

    def __init__(self, bus_type, **kwargs):
        self.bus_type = bus_type
        self.bus = None


def loader(dev_type, **cfg):
    device = None
    if dev_type == ControllerDeviceTypes.emulated:
        if "EmulatedI2C" not in sys.modules:
            from devices.i2c_interface.emulated import EmulatedI2C
        device = EmulatedI2C(BusType.i2c, **cfg)
    elif dev_type == ControllerDeviceTypes.raspi:
        if "RaspiI2c" not in sys.modules:
            from devices.i2c_interface.raspi_i2c import RaspiI2c
        device = RaspiI2c(BusType.i2c, **cfg)

    return device
