"""
Emulated Digital IO Interface
"""
from devices.dio_devices import DioInterface
import logging

log = logging.getLogger(__name__)

default_config = {
    "input_pins": [1,2,3,4],
    "output_pins": [10,24,35]
}


class EmulatedIO(DioInterface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for pin in kwargs["input_pins"]:
            self.input_pins[pin] = False

        for pin in kwargs["output_pins"]:
            self.output_pins[pin] = False

    def write_digital(self, pin, set_high=False):
        if pin in self.output_pins.keys():
            self.output_pins[pin] = set_high

    def read_digital(self, pin):
        if pin in self.output_pins.keys():
            return self.output_pins[pin]
        elif pin in self.input_pins.keys():
            return self.input_pins[pin]
