
from enum import Enum


class BusTypes(Enum):
    spi = 0
    i2c = 1


class ControllerDeviceTypes(Enum):
    emulated = 0
    raspi = 1
