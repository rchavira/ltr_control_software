"""
PCA9685 PWM Driver Interface
"""

import logging

from adafruit_pca9685 import PCA9685
from devices.pwm_devices import PwmInterface, DriverInfo
from devices.bus_manager import BusManager

log = logging.getLogger(__name__)

default_config = {
    "drivers": {
        "ttv1": {
            "channel": 0,
            "offset": 0
        }
    }
}


class PCA9685Interface(PwmInterface):
    device: PCA9685
    bus: BusManager

    def __init__(self, dev_name, bus, **kwargs):
        super().__init__(dev_name, bus, **kwargs)
        self.device = None
        self.frequency = kwargs["frequency"]
        self.address = kwargs["i2c_addr"]
        for dev_id in kwargs["drivers"]:
            self.drivers[dev_id] = DriverInfo(
                kwargs["drivers"][dev_id]["channel"],
                kwargs["drivers"][dev_id]["offset"],
                65535
            )

    def init_device(self):
        result = True
        self.bus.bus_blocker(self.dev_name, True)
        try:
            self.device = PCA9685(self.bus.bus)
            self.device.frequency = self.frequency
        except Exception as ex:
            log.error(ex)
            result = False
        return result

    def close_device(self):
        self.device = None
        self.bus.bus_blocker(self.dev_name, False)

    def set_duty_cycle(self, dev_id, dc):
        self.drivers[dev_id].set_dc(dc)
        if self.device is not None:
            self.device.channels[self.drivers[dev_id].channel].duty_cycle = self.drivers[dev_id].pwm_value
