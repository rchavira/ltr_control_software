"""
Thermocouple manager
"""

import logging
import sys

from enum import Enum
from threading import Thread
from time import sleep
from typing import Dict, Any
from devices.thermocouples import ThermoInterface, ThermoTypes, loader
from devices.bus_manager import BusManager

log = logging.getLogger(__name__)


default_config = {
    "update_interval": 1,
    "temp_decimals": 2,
    "devices": {
        "t1": {
            "device_type": "emulated",
            "config": {
                "junction_values_file": "test.txt",
                "internal_values_file": "test2.txt",
                "flag_values_file": "test3.txt"
            }
        },
        "t2": {
            "device_type": "emulated",
            "config": {
                "junction_values_file": "test.txt",
                "internal_values_file": "test2.txt",
                "flag_values_file": "test3.txt"
            }
        }

    }
}


class ThermoData(object):
    def __init__(self):
        self.junction_temp = 0
        self.internal_temp = 0
        self.flag = False
        self.flag_no_tc = False
        self.flag_shorted_gnd = False
        self.flag_shorted_vcc = False
        self.flag_other = False
        self.junction_temp_register = 0
        self.internal_temp_register = 0
        self.status_register = 0
        self.flag_register = 0


class ThermoManager(object):
    spi: BusManager
    i2c: BusManager
    update_thread: Thread
    device_data: Dict[Any, ThermoData]
    devices: Dict[Any, ThermoInterface]

    def __init__(self, spi, i2c, chip_sel, **thermal_config):
        """
        Initialization of the Thermomanager Object
        :param spi:
        :param i2c:
        :param spi_blocker:
        :param i2c_blocker:
        :param chip_sel:
        :param thermal_config:
        """
        self.devices = {}
        self.device_data = {}
        self.update_thread = None
        self.update_interval = thermal_config["update_interval"]
        self.updater_running = False
        self.config = thermal_config
        self.spi = spi
        self.i2c = i2c
        self.chip_sel = chip_sel
        self.temp_decimals = thermal_config["temp_decimals"]
        log.info(f"ThermoManager v0.0.1")

        for dev_id in thermal_config["devices"].keys():
            device_type = ThermoTypes[thermal_config["devices"][dev_id]["device_type"]]
            self.add_device(dev_id, dev_type=device_type, **thermal_config["devices"][dev_id])

    def add_device(self, dev_id, dev_type, **cfg):
        device = loader(dev_type=dev_type, dev_id=dev_id, spi=self.spi, i2c=self.spi, ch_sel=self.chip_sel, **cfg)
        d_data = ThermoData()

        self.device_data[dev_id] = d_data
        self.devices[dev_id] = device

        log.info(f"Added {dev_type} device {dev_id}.")

    def updater(self):
        while self.updater_running:
            for dev_id in self.devices.keys():
                log.debug(f"reading data for {dev_id}")
                self.devices[dev_id].init_device()
                self.device_data[dev_id].junction_temp = self.devices[dev_id].get_junction_temp()
                self.device_data[dev_id].internal_temp = self.devices[dev_id].get_internal_temp()
                self.device_data[dev_id].flag = self.devices[dev_id].get_faults()
                self.devices[dev_id].close_device()

            sleep(self.update_interval)

    def start_manager(self):
        log.info(f"Starting Thermo Manager update Thread")
        self.update_thread = Thread(target=self.updater)
        self.update_thread.isDaemon = True
        self.updater_running = True
        self.update_thread.start()
        sleep(1)

    def stop_manager(self):
        log.info(f"Stopping Thermo Manager update Thread")
        self.updater_running = False
        if self.update_thread is not None:
            self.update_thread.join(2)
        self.update_thread = None

    def get_values(self, dev_id):
        jt = self.device_data[dev_id].junction_temp
        it = self.device_data[dev_id].internal_temp
        ft = 1 if self.device_data[dev_id].flag else 0
        st = 0
        st += 1 if self.device_data[dev_id].flag_no_tc else 0
        st += 2 if self.device_data[dev_id].flag_shorted_gnd else 0
        st += 4 if self.device_data[dev_id].flag_shorted_vcc else 0
        st += 8 if self.device_data[dev_id].flag_other else 0

        return jt, it, ft, st


def test():

    """
    from devices.thermocouples.emulated import gen_up_and_down, gen_values

    gen_up_and_down("test.txt", 15, 65, 1000)
    gen_up_and_down("test2.txt", 15, 35, 1000)
    gen_values("test3.txt", 0, 1, 1000, isfloat=False)
    """
    from devices.bus_manager import BusManager
    from devices.spi_interface import SpiInterface
    i2c_mgr = BusManager()
    spi_mgr = BusManager()
    tm = ThermoManager(
        spi=SpiInterface().spi, i2c=None, spi_blocker=spi_mgr.bus_blocker, i2c_blocker=i2c_mgr.bus_blocker,
        chip_sel=None, **default_config
    )
    tm.start_manager()
    while True:
        for dev_id in default_config["devices"].keys():
            print(f"{dev_id}:{tm.get_values(dev_id)}")
        try:
            sleep(1)
        except KeyboardInterrupt:
            break
    tm.stop_manager()
    tm = None
