import logging

import busio
from board import SCL, SDA
from devices.communication import BusType
from devices.i2c_interface import I2CInterface

log = logging.getLogger(__name__)


class RaspiI2c(I2CInterface):
    bus_type: BusType

    def __init__(self, bus_type, **kwargs):
        self.bus_type = bus_type
        self.bus = busio.I2C(SCL, SDA)
