"""
Main interface for thermocouples
"""
import sys

from enum import Enum
from devices.bus_manager import BusManager


class ThermoTypes(Enum):
    emulated = 0
    max31855 = 1
    max31856 = 2
    mcp960x = 3


class ThermoInterface(object):
    bus_blocker: BusManager

    def __init__(self, **kwargs):
        self.junction_temp = 0
        self.internal_temp = 0
        self.flag = False
        self.flag_no_tc = False
        self.flag_shorted_gnd = False
        self.flag_shorted_vcc = False
        self.flag_other = False
        self.config = kwargs
        self.bus_blocker = None

    def init_device(self):
        """
        Perform any device initialization here
        :return: True if successful, False on Error
        """
        return True

    def close_device(self):
        """
        Perform any device closing here
        :return: None
        """
        pass

    def get_junction_temp(self):
        """
        Read and return junction temperature from device
        :return: float value for thermocouple device junction temp
        """
        pass

    def get_internal_temp(self):
        """
        read and return internal temperature from device
        :return: float value for internal device temp
        """
        pass

    def get_faults(self):
        """
        read or detect any flags, faults or errors and update any
        internal flags here.
        :return: bool, general flag value
        """
        self.flag = False
        return self.flag


def loader(dev_type, dev_id, spi, i2c, ch_sel, **cfg):
    device = None
    if dev_type == ThermoTypes.emulated:
        if 'EmulatedThermo' not in sys.modules:
            from devices.thermocouples.emulated import EmulatedThermo
        device = EmulatedThermo(**cfg)
    elif dev_type == ThermoTypes.max31855:
        if 'MAX31855Interface' not in sys.modules:
            from devices.thermocouples.max31855_interface import MAX31855Interface
        device = MAX31855Interface(dev_id, spi, ch_sel, **cfg)
    elif dev_type == ThermoTypes.max31856:
        if 'MAX31856Interface' not in sys.modules:
            from devices.thermocouples.max31856_interface import MAX31856Interface
        device = MAX31856Interface(dev_id, spi, ch_sel, **cfg)
    elif dev_type == ThermoTypes.mcp960x:
        if 'MCP960xInterface' not in sys.modules:
            from devices.thermocouples.mcp960x_interface import MCP960xInterface
        device = MCP960xInterface(dev_id, i2c, **cfg)

    return device
