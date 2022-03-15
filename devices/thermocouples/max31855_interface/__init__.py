"""
Interface for all MAX31855 thermocouple amplifiers
"""

import logging

import adafruit_max31855
import board
from devices.bus_manager import BusManager
from devices.chip_select import ChipSelector
from devices.thermocouples import ThermoInterface
from digitalio import DigitalInOut

log = logging.getLogger(__name__)


class MAX31855Interface(ThermoInterface):
    chip_select: ChipSelector
    bus_mgr: BusManager

    def __init__(self, dev_id, bus, ch_sel, **kwargs):
        super().__init__(**kwargs)
        self.cs = kwargs["cs"]
        self._cs = DigitalInOut(board.D4)
        self.chip_select = ch_sel
        self.device = None  # type: adafruit_max31855.MAX31855
        self.bus_mgr = bus
        self.dev_id = dev_id

    def init_device(self):
        result = False
        if self.bus_mgr.bus_blocker(self.dev_id, True):
            result = True
            if self.chip_select is not None:
                self.chip_select.chip_select(self.cs)
            try:
                self.device = adafruit_max31855.MAX31855(
                    self.bus_mgr.get_bus(), self._cs
                )
            except Exception as ex:
                log.error(ex)
                result = False
        return result

    def close_device(self):
        self.bus_mgr.bus_blocker(self.dev_id, False)
        self.device = None

    def get_junction_temp(self):
        value = 0.0
        try:
            value = self.device.temperature
        except Exception as ex:
            log.error(ex)
            if "thermocouple not connected" in ex.__str__():
                self.flag = True
                self.flag_no_tc = True
            elif "short circuit to ground" in ex.__str__():
                self.flag = True
                self.flag_shorted_gnd = True
            elif "short circuit to power" in ex.__str__():
                self.flag = True
                self.flag_shorted_vcc = True
            else:
                log.error(ex)
        return value

    def get_internal_temp(self):
        it = 0
        try:
            if self.device is not None:
                it = self.device.reference_temperature
        except Exception as ex:
            log.error(ex)
        return it

    def get_faults(self):
        self.get_junction_temp()
        return self.flag
