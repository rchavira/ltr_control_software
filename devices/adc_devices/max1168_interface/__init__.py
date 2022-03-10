"""
Max1168 interface
"""

import logging
import struct

from devices.bus_manager import BusManager
from devices.adc_devices import AdcInfo, AdcInterface
from devices.chip_select import ChipSelector

log = logging.getLogger(__name__)

default_config = {
    "chip_select": 9,
    "devices": {
        "t11": {
            "channel": 0,
            "min_val": 0,
            "max_val": 150
        },
        "t12": {
            "channel": 1,
            "min_val": 0,
            "max_val": 150
        }
    }
}


class Max1168Interface(AdcInterface):
    bus_mgr: BusManager
    chip_select: ChipSelector

    def __init__(self, dev_name, bus, ch_sel, **kwargs):
        super().__init__()
        self.chip_select = ch_sel
        self.bus_mgr = bus
        self.resolution = 65535
        self.cs = kwargs["chip_select"]
        for dev_id in kwargs["devices"].keys():
            self.channels[dev_id] = AdcInfo(
                kwargs["devices"][dev_id]["channel"],
                dev_name,
                kwargs["devices"][dev_id]["min_val"],
                kwargs["devices"][dev_id]["max_val"],
                self.resolution
            )

    def read_channel(self, dev_id):

        if self.bus_mgr.bus_blocker(dev_id, True):
            self.chip_select.chip_select(self.cs)

            cmd = struct.pack("<H", (int(self.channels[dev_id].channel) << 5 | 3 << 3))
            response = self.bus_mgr.send_and_receive(cmd, 3)
            raw, _ = struct.unpack("<HB", response)
            self.channels[dev_id].set_value(raw)

            self.chip_select.reset()

            self.bus_mgr.bus_blocker(dev_id, False)

        return self.channels[dev_id].value

