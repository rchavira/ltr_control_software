"""
Interface for MCP9600 and MCP9601 Thermocouple Amplifier
"""
import logging
import mcp9600
from devices.thermocouples import ThermoInterface
from devices.bus_manager import BusManager


log = logging.getLogger(__name__)


class MCP960xInterface(ThermoInterface):
    device: mcp9600.MCP9600
    bus_mgr: BusManager

    def __init__(self, dev_id, bus, **kwargs):
        super().__init__(**kwargs)
        self.address = kwargs["i2c_addr"]
        self.device = None  # type: mcp9600.MCP9600
        self.dev_id = dev_id
        self.bus_mgr = bus

    def init_device(self):
        result = False
        if self.bus_mgr.bus_blocker(self.dev_id, True):
            result = True
            try:
                self.device = mcp9600.MCP9600(i2c_addr=self.address)
            except Exception as ex:
                log.error(ex)
                result = False
        return result

    def close_device(self):
        self.device = None
        self.bus_mgr.bus_blocker(self.dev_id, False)

    def get_junction_temp(self):
        jt = 0
        if self.device is not None:
            jt = self.device.get_hot_junction_temperature()
        return jt

    def get_internal_temp(self):
        it = 0
        if self.device is not None:
            it = self.device.get_cold_junction_temperature()
        return it

    def get_faults(self):
        self.flag = False
        if self.device is not None:
            self.flag_no_tc = self.device.is_disconnected()
            self.flag_shorted_gnd = self.device.is_shorted()
            self.flag = self.flag_no_tc or self.flag_shorted_gnd
        return self.flag
