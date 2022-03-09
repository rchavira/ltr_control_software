"""
Emulated Digital IO Interface
"""
from devices.dio_devices import DioInterface
import RPi.GPIO as GPIO
import logging

log = logging.getLogger(__name__)


default_config = {
    "input_pins": [6, 16],
    "output_pins": [5, 17, 22, 23, 26, 27]
}


class RaspiDio(DioInterface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = kwargs
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.init_device()

    def init_device(self):
        for pin in self.config["input_pins"]:
            self.input_pins[pin] = False
            GPIO.setup(pin, GPIO.IN)

        for pin in self.config["output_pins"]:
            self.output_pins[pin] = False
            GPIO.setup(pin, GPIO.OUT)

    def close_device(self):
        GPIO.cleanup()

    def write_digital(self, pin, set_high=False):
        if pin in self.output_pins.keys():
            self.output_pins[pin] = set_high
            val = 1 if set_high else 0
            GPIO.output(pin, val)

    def read_digital(self, pin):
        if pin in self.output_pins.keys():
            return self.output_pins[pin]
        elif pin in self.input_pins.keys():
            self.input_pins[pin] = True if GPIO.input(pin)==1 else False
            return self.input_pins[pin]
