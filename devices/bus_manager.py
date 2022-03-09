"""
Bus Manager
This will just manage the bus so that one device is
being used at a time.
"""
import logging

from time import sleep

from devices.i2c_interface import loader as i2c_loader
from devices.spi_interface import loader as spi_loader
from devices.communication import BusInterface, BusType

log = logging.getLogger(__name__)


class BusManager(object):
    bus: BusInterface
    bus_type: BusType

    def __init__(self, bus_type, device_type, **kwargs):
        self.blocked = False
        self.blocker = ""
        self.bus_type = bus_type

        if self.bus_type == BusType.spi:
            self.bus = spi_loader(device_type, **kwargs)
        elif self.bus_type == BusType.i2c:
            self.bus = i2c_loader(device_type, **kwargs)

    def get_bus(self):
        return self.bus.bus

    def check_bus(self):
        pass

    def send_and_receive(self, byte_data, resp_len, read_delay=0.5):
        return self.bus.send_and_receive(byte_data, resp_len, read_delay)

    def bus_blocker(self, dev_id, block):
        if block:
            if self.blocked:
                log.debug(f"{dev_id} waiting for i2c bus, blocked by {self.blocker}")
                while self.blocked:
                    sleep(1)
            else:
                self.blocked = True
                self.blocker = dev_id
        else:
            self.blocker = ""
            self.blocked = False


