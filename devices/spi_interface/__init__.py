"""
SPI Interface Prototype
"""
import sys

from devices.communication import BusInterface, BusType
from system_control import ControllerDeviceTypes


class SpiInterface(BusInterface):
    bus_type: BusType

    def __init__(self, bus_type, **kwargs):
        self.bus_type = bus_type
        self.bus = None
        self.cs = None

    def send_and_receive(self, byte_data, resp_len, read_delay=0.5):
        pass


def loader(dev_type, **cfg):
    device = None  # type: SpiInterface
    if dev_type == ControllerDeviceTypes.emulated:
        if 'EmulatedSpi' not in sys.modules:
            from devices.spi_interface.emulated import EmulatedSpi
        device = EmulatedSpi(BusType.spi, **cfg)
    elif dev_type == ControllerDeviceTypes.raspi:
        if 'RaspiSpi' not in sys.modules:
            from devices.spi_interface.raspi_spi import RaspiSpi
        device = RaspiSpi(BusType.spi, **cfg)

    return device
