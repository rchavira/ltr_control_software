import logging

from time import sleep
from devices.mux_devices import MuxDeviceInterface

log = logging.getLogger(__name__)

default_configuration = {
    "pinA": 17,
    "pinB": 27,
    "pinC": 22,
    "pinD": 5,
    "strobe": 23,
    "strobe_delay": 0.5
}


class CD4515Interface(MuxDeviceInterface):
    def __init__(self, dio, **kwargs):
        super().__init__(dio, **kwargs)
        self.pinA = kwargs["pinA"]
        self.pinB = kwargs["pinB"]
        self.pinC = kwargs["pinC"]
        self.pinD = kwargs["pinD"]
        self.strobe = kwargs["strobe"]
        self.strobe_delay = kwargs["strobe_delay"]

    def encode(self, output_ch):
        dA = 1 if (output_ch & 1) else 0
        dB = 1 if (output_ch & 2) else 0
        dC = 1 if (output_ch & 4) else 0
        dD = 1 if (output_ch & 8) else 0

        # # log.debug(f"MUX setting output {output_ch}: encoded to {[dA, dB, dC, dD]}")

        self.dio.write_digital(self.strobe, 1)
        sleep(self.strobe_delay)

        self.dio.write_digital(self.pinA, dA)
        self.dio.write_digital(self.pinB, dB)
        self.dio.write_digital(self.pinC, dC)
        self.dio.write_digital(self.pinD, dD)

        self.dio.write_digital(self.strobe, 0)
        sleep(self.strobe_delay)




