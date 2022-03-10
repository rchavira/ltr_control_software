"""
Interface for all MAX31855 thermocouple amplifiers
"""

import logging
import board
import adafruit_max3186
from math import nan

import digitalio
from digitalio import DigitalInOut
from devices.thermocouples import ThermoInterface
from devices.chip_select import ChipSelector
from devices.bus_manager import BusManager

log = logging.getLogger(__name__)


class MAX31856Interface(ThermoInterface):
    chip_select: ChipSelector
    device: adafruit_max3186.MAX31855
    bus_mgr: BusManager

    def __init__(self, dev_id, spi, ch_sel, **kwargs):
        super().__init__(**kwargs)
        self.cs = kwargs["cs"]
        self._cs = DigitalInOut(board.D4)
        self._cs.direction = digitalio.Direction.OUTPUT
        self.chip_select = ch_sel
        self.device = None  # type: adafruit_max31855.MAX31855
        self.bus_mgr = spi
        self.dev_id = dev_id

    def init_device(self):
        result = True
        self.bus_mgr.bus_blocker(self.dev_id, True)
        if self.chip_select is not None:
            self.chip_select.chip_select(self.cs)
        try:
            self.device = adafruit_max31856.MAX31856(self.bus_mgr.bus.bus, self._cs)
        except Exception as ex:
            log.error(ex)
            result = False
        return result

    def close_device(self):
        self.bus_mgr.bus_blocker(self.dev_id, False)
        self.device = None

    def get_junction_temp(self):
        value = nan
        try:
            value = self.device.temperature
        except Exception as ex:
            if "thermocouple not connected" in ex.__str__():
                self.flag = True
                self.flag_no_tc = True
            elif "short circuit to ground" in ex.__str__():
                self.flag = True
                self.flag_shorted_gnd = True
            elif "short circuit to power" in ex.__str__():
                self.flag = True
                self.flag_shorted_vcc = True
        return value

    def get_internal_temp(self):
        it = 0
        if self.device is not None:
            it = self.device.reference_temperature
        return it

    def get_faults(self):
        self.flag = False
        if self.device is not None:
            faults = self.device.faults
            self.flag_no_tc = faults["open_tc"]
            self.flag_shorted_vcc = faults["tc_high"]
            self.flag_shorted_gnd = faults["tc_low"]
            self.flag_other = faults["voltage"]
            self.flag = self.flag_other or self.flag_no_tc or self.flag_shorted_gnd or self.flag_shorted_vcc
        return self.flag
