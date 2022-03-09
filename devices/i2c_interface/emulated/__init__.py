from devices.communication import BusType
from devices.i2c_interface import I2CInterface


class EmulatedI2C(I2CInterface):
    bus_type: BusType

    def __init__(self, bus_type, **kwargs):
        self.bus_type = bus_type
        self.bus = None
