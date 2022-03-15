import logging
from threading import Thread
from time import sleep, time
from typing import Dict, Any

from devices.bus_manager import BusManager
from devices.pwm_devices import PwmInterface, DriverTypes, loader


log = logging.getLogger(__name__)


class DriverData(object):
    def __init__(self, dev):
        self.device_id = dev
        self.target_dc = 0
        self.current_dc = 0
        self.current_dc_time_stamp = 0
        self.locked = False
        self.locker = []

    def lock(self, locker):
        self.locked = True
        if locker not in self.locker:
            self.locker.append(locker)

    def unlock(self, locker):
        if locker in self.locker:
            self.locker.remove(locker)

        if len(self.locker) == 0:
            self.locked = False


class DriverManager(object):
    spi: BusManager
    i2c: BusManager
    update_thread: Thread
    device_data: Dict[Any, DriverData]
    devices: Dict[Any, PwmInterface]

    def __init__(self, spi, i2c, **kwargs):
        self.spi = spi
        self.i2c = i2c
        self.update_thread = None
        self.device_data = {}
        self.devices = {}
        self.update_thread = None
        self.update_interval = kwargs["update_interval"]
        self.updater_running = False
        self.group_lock = {}

        for dev in kwargs["devices"].keys():
            device_type = DriverTypes[kwargs["devices"][dev]["device_type"]]
            self.add_device(dev, device_type, **kwargs["devices"][dev]["config"])

    def add_device(self, dev, device_type, **cfg):
        device = loader(dev, device_type, self.i2c, **cfg)
        self.group_lock[dev] = False

        for dev_id in device.drivers.keys():
            self.device_data[dev_id] = DriverData(dev)

        self.devices[dev] = device

    def set_output(self, dev_id, duty_cycle):
        # log.debug(f"setting driver {dev_id} to {duty_cycle}%...")
        if not self.device_data[dev_id].locked:
            self.device_data[dev_id].target_dc = duty_cycle
        else:
            self.device_data[dev_id].target_dc = 0

    def set_group(self, dev, duty_cycle):
        # log.debug(f"Setting group {dev} to {duty_cycle}%...")
        for dev_id in self.device_data.keys():
            self.set_output(dev_id, duty_cycle)

    def lock(self, dev_id, locker):
        self.device_data[dev_id].lock(locker)

    def unlock(self, dev_id, locker):
        self.device_data[dev_id].unlock(locker)

    def lock_group(self, dev, locker):
        # self.group_lock[dev] = True
        for dev_id in self.device_data.keys():
            if self.device_data[dev_id].device_id == dev:
                self.lock(dev_id, locker)

    def unlock_group(self, dev, locker):
        lock_status = False
        for dev_id in self.device_data.keys():
            if self.device_data[dev_id].device_id == dev:
                self.unlock(dev_id, locker)
            lock_status = self.device_data[dev_id].locked
        # self.group_lock[dev] = lock_status

    def _set_driver_dc(self, dev, dev_id, dc):
        if not self.device_data[dev_id].locked:
            if self.devices[dev].init_device():
                self.devices[dev].set_duty_cycle(dev_id, dc)
                self.devices[dev].close_device()

    def updater(self):
        while self.updater_running:
            for dev_id in self.device_data.keys():
                dev = self.device_data[dev_id].device_id
                self.device_data[dev_id].current_dc = (
                    self.devices[dev].drivers[dev_id].duty_cycle
                )
                cdc = self.device_data[dev_id].current_dc
                tdc = self.device_data[dev_id].target_dc
                rtime = self.devices[dev].ramp_up_delay

                if cdc != tdc:
                    rstep = self.devices[dev].ramp_up_power_step
                    dc = tdc
                    if rstep > 0:
                        if cdc < tdc:
                            if (
                                time() - self.device_data[dev_id].current_dc_time_stamp
                                > rtime
                            ):
                                if rstep > (tdc - cdc):
                                    rstep = tdc - cdc
                                dc = cdc + rstep
                                self.device_data[dev_id].current_dc_time_stamp = time()
                                self._set_driver_dc(dev, dev_id, dc)
                        elif cdc > tdc:
                            self._set_driver_dc(dev, dev_id, dc)
                    else:
                        self._set_driver_dc(dev, dev_id, dc)
                else:
                    self.device_data[dev_id].current_dc_time_stamp = time() - rtime

            sleep(self.update_interval)

    def start_manager(self):
        log.info(f"Starting Driver Manager update Thread")
        self.update_thread = Thread(target=self.updater)
        self.update_thread.isDaemon = True
        self.updater_running = True
        self.update_thread.start()
        sleep(2)

    def stop_manager(self):
        log.info(f"Stopping Driver Manager update Thread")
        for dev in self.devices.keys():
            self.set_group(dev, 0)

        self.updater_running = False
        if self.update_thread is not None:
            self.update_thread.join(2)
        self.update_thread = None

    def get_values(self, dev_id):
        dev = self.device_data[dev_id].device_id
        if self.device_data[dev_id].current_dc_time_stamp > 0:
            time_last_commanded = int(
                time() - self.device_data[dev_id].current_dc_time_stamp
            )
        else:
            time_last_commanded = 0
        return [
            self.device_data[dev_id].current_dc,
            self.device_data[dev_id].target_dc,
            self.devices[dev].drivers[dev_id].channel,
            self.devices[dev].drivers[dev_id].pwm_value,
            time_last_commanded,
            1 if self.devices[dev].drivers[dev_id].locked else 0,
        ]
