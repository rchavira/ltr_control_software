import logging

import busio
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
from driver_interface import DriverInterface

log = logging.getLogger(__name__)


class DriverHardware(DriverInterface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        i2c_bus = busio.I2C(SCL, SDA)
        try:
            self.pca = PCA9685(i2c_bus)
        except Exception as ex:
            log.error(f"{ex}")
            self.pca = None
        if self.pca is not None:
            self.pca.frequency = self.frequency

    def set_duty_cycle(self, channel, dc):
        # print(f"setting {channel} to DC: {dc}")
        self.dc[channel] = dc

        pwm = int(self.remap(self.dc[channel], 0, 100, 0, 0xFFFF))

        self.pca.channels[channel].duty_cycle = pwm
        # time.sleep(0.1)
        """ l = []
        for i in range(6):
            l.append(f"{i}: {self.pca.channels[i].duty_cycle}")

        states = ",".join(l)
        print(f"{states}") """
