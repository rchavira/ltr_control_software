import logging

from threading import Thread
from time import sleep
from typing import Dict, Any

from devices.bus_manager import BusManager
from devices.chip_select import ChipSelector
from devices.adc_devices import AdcInterface, AdcInfo, AdcDeviceTypes, loader

log = logging.getLogger(__name__)

default_config = {
    "update_interval": 1,
    "devices": {
        "adc1": {
            "device_type": "emulated",
            "chip_select": 11,
            "input_file": "test.txt",
            "resolution": 1024,
            "devices": {
                "leak_1": {
                    "channel": 3,
                    "min_val": 0,
                    "max_val": 1024
                }
            }
        }
    }
}


class AdcManager(object):
    spi: BusManager
    i2c: BusManager
    devices: Dict[Any, AdcInterface]
    data: Dict[Any, AdcInfo]
    ch_sel: ChipSelector

    def __init__(self, spi, i2c, ch_sel, **kwargs):
        self.devices = {}
        self.data = {}
        self.spi = spi
        self.i2c = None
        self.ch_sel = ch_sel
        self.update_thread = None
        self.update_interval = kwargs["update_interval"]
        self.updater_running = False
        # log.debug(f"Adding {len(kwargs['devices'])} device")
        for dev in kwargs["devices"].keys():
            device_type = AdcDeviceTypes[kwargs['devices'][dev]['device_type']]
            self.add_device(dev, dev_type=device_type, **kwargs['devices'][dev])

    def add_device(self, dev, dev_type, **cfg):
        device = loader(dev_type, dev, self.spi, self.ch_sel, **cfg)
        for d in device.channels.keys():
            self.data[d] = device.channels[d]

        self.devices[dev] = device

    def updater(self):
        while self.updater_running:
            for dev_id in self.data.keys():
                dev = self.data[dev_id].device_id
                self.devices[dev].read_channel(dev_id)
                # log.debug(f"{dev_id}: {self.get_values(dev_id)}")
            sleep(self.update_interval)

    def start_manager(self):
        log.info(f"Starting ADC Manager update Thread")
        self.update_thread = Thread(target=self.updater)
        self.update_thread.isDaemon = True
        self.updater_running = True
        self.update_thread.start()

    def stop_manager(self):
        log.info(f"Stopping ADC Manager update Thread")
        self.updater_running = False
        if self.update_thread is not None:
            self.update_thread.join(2)

        self.update_thread = None

    def get_values(self, dev_id):
        dev = self.data[dev_id].device_id
        ch = self.devices[dev].channels[dev_id].channel
        raw = self.devices[dev].channels[dev_id].raw_value
        val = self.devices[dev].channels[dev_id].value
        min_val = self.devices[dev].channels[dev_id].min_val
        max_val = self.devices[dev].channels[dev_id].max_val
        res = self.devices[dev].channels[dev_id].resolution
        return [val, raw, ch, min_val, max_val, res]

