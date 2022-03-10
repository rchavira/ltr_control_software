import logging

from devices.pwm_devices import PwmInterface, DriverInfo

log = logging.getLogger(__name__)

default_config = {
    "drivers": {
        "ttv1": {
            "channel": 0,
            "offset": 0,
            "resolution": 65535
        }
    }
}

class EmulatedPwm(PwmInterface):
    def __init__(self, dev_name, bus, **kwargs):
        super().__init__(dev_name, bus, **kwargs)
        for dev_id in kwargs["drivers"]:
            self.drivers[dev_id] = DriverInfo(
                kwargs["drivers"][dev_id]["channel"],
                kwargs["drivers"][dev_id]["offset"],
                kwargs["drivers"][dev_id]["resolution"],
            )

    def set_duty_cycle(self, dev_id, dc):
        self.drivers[dev_id].set_dc(dc)
