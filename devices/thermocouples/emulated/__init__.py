"""
Emulated interface for thermocouple devices

Usage:
from thermocouples.emulated import EmulatedThermo, gen_values, gen_up_and_down, default_config

"""

from devices.thermocouples import ThermoInterface
from devices.emulation_helpers import get_next_float, get_next_int
import logging


log = logging.getLogger(__name__)

default_config = {
    "junction_values_file": "test.txt",
    "internal_values_file": "test2.txt",
    "flag_values_file": "test3.txt"
}


class EmulatedThermo(ThermoInterface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_internal_temp(self):
        self.internal_temp = get_next_float(self.config["internal_values_file"])
        return self.internal_temp

    def get_junction_temp(self):
        self.junction_temp = get_next_float(self.config["junction_values_file"])
        return self.junction_temp

    def get_faults(self):
        self.flag = False
        self.flag_shorted_gnd = (get_next_int(self.config["flag_values_file"]) == 1)
        self.flag_no_tc = (get_next_int(self.config["flag_values_file"]) == 1)
        self.flag = self.flag_shorted_gnd or self.flag_no_tc
