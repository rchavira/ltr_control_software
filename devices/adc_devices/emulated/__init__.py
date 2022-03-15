import logging

from devices.adc_devices import AdcInfo, AdcInterface
from devices.emulation_helpers import get_next_int

log = logging.getLogger(__name__)

default_config = {
    "input_file": "test.txt",
    "resolution": 1024,
    "chip_select": 0,
    "devices": {
        "t11": {"channel": 0, "min_val": 0, "max_val": 150},
        "t12": {"channel": 1, "min_val": 0, "max_val": 150},
    },
}


class EmulatedAdc(AdcInterface):
    def __init__(self, dev_name, bus, **kwargs):
        super().__init__()
        self.bus = bus
        self.input_file = kwargs["input_file"]
        self.resolution = kwargs["resolution"]
        self.cs = kwargs["chip_select"]
        for dev_id in kwargs["devices"].keys():
            self.channels[dev_id] = AdcInfo(
                kwargs["devices"][dev_id]["channel"],
                dev_name,
                kwargs["devices"][dev_id]["min_val"],
                kwargs["devices"][dev_id]["max_val"],
                self.resolution,
            )

    def read_channel(self, dev_id):
        self.bus.bus_blocker(dev_id, True)
        raw = get_next_int(self.input_file)
        self.channels[dev_id].set_value(raw)
        self.bus.bus_blocker(dev_id, False)
        return self.channels[dev_id].value
