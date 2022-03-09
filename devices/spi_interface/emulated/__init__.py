import logging

from time import sleep

from devices.communication import BusType
from devices.spi_interface import SpiInterface
from os import path

log = logging.getLogger(__name__)

default_config = {
    "input_file": "spi_stdin.txt",
    "output_file": "spi_stdout.txt"
}


class EmulatedSpi(SpiInterface):
    bus_type: BusType

    def __init__(self, bus_type, **kwargs):
        self.bus_type = bus_type
        self.bus = None
        self.cs = None
        self.input_file = kwargs["input_file"]
        self.output_file = kwargs["output_file"]

    def send_and_receive(self, byte_data, resp_len, read_delay=0.5):
        with open(self.output_file, 'wb') as file:
            file.write(byte_data)

        sleep(read_delay)
        data = [0] * resp_len
        if path.exists(self.input_file):
            with open(self.input_file, 'rb') as file:
                data = file.read(resp_len)

        return data
