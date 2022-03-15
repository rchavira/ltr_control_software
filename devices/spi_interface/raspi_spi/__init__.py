"""
Raspi SPI Interface
"""

import logging

import board
from adafruit_bus_device.spi_device import SPIDevice
from devices.communication import BusType
from devices.spi_interface import SpiInterface
from digitalio import DigitalInOut

log = logging.getLogger(__name__)

default_config = {}


class RaspiSpi(SpiInterface):
    bus_type: BusType

    def __init__(self, bus_type, **kwargs):
        self.bus = board.SPI()
        # self.bus2 = SPIDevice(self.bus)

        self.cs = DigitalInOut(board.D4)

    def send_and_receive(self, byte_data, resp_len, read_delay=0.5):
        with SPIDevice(self.bus, self.cs, baudrate=4000000) as spi:
            spi.write(byte_data)
            # sleep(read_delay)

            resp = bytearray(resp_len)

            spi.readinto(resp)

        return resp
