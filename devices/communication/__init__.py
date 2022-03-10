"""
Communication prototype interfaces
"""
from enum import Enum


class BusType(Enum):
    spi = 0
    i2c = 1


class BusInterface(object):
    bus_type: BusType

    def __init__(self, bus_type, **kwargs):
        self.bus_type = bus_type
        self.bus = None
        self.bus2 = None

    def send_and_receive(self, byte_data, resp_len, read_delay=0.5):
        pass
