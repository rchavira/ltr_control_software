import logging
import sys

from enum import Enum
from threading import Thread
from time import sleep

from devices.fan_controller_devices import FanDevType, FanSpeedInterface, loader as fan_loader

from system_control.sensor_aggregator import SensorAggregator

from devices.driver_manager import DriverManager
from system_control.sensor_manager import SensorManager

from system_control import ControllerDeviceTypes
from system_control.sensor_manager import SensorManager

log = logging.getLogger(__name__)

default_config = {
    "fan_group": ["fan1", "fan2"],
    "driver_group": ["ttv1", "ttv2", "ttv3", "ttv4"],
    "inlet_group": ["t9", "t10"],
    "outlet_group": ["t10", "t11"],
    "monitor_group": ["t1", "t2", "t3", "t4"],
    "monitor_threshold_temp": 70,
    "outlet_threshold_temp": 45,
    "inlet_threshold_temp": 45,
    "fan_table": [
            (45, 60),
            (44, 45),
            (42, 30),
            (40, 20),
    ],
    "default_fan_value": 70,
    "sample_size": 10,
    "fan_run_mode": "fan_table"
}


class FanRunMode(Enum):
    disabled = 0
    fan_table = 1
    fan_speed = 2
    temp_control = 3


class ThermalManager(object):
    driver_manager: DriverManager
    sensor_manager: SensorManager
    update_thread: Thread
    inlet_group: SensorAggregator
    outlet_group: SensorAggregator
    monitor_group: SensorAggregator

    def __init__(self, sensor_manager, driver_manager, **kwargs):
        self.driver_manager = driver_manager
        self.sensor_manager = sensor_manager
        self.updater_running = False
        self.update_thread = None
        self.fan_group = kwargs["fan_group"]
        self.driver_group = kwargs["driver_group"]
        self.inlet_group = SensorAggregator(kwargs["inlet_group"], kwargs["sample_size"])
        self.outlet_group = SensorAggregator(kwargs["outlet_group"], kwargs["sample_size"])
        self.monitor_group = SensorAggregator(kwargs["monitor_group"], kwargs["sample_size"])
        self.default_fan_value = kwargs["default_fan_value"]
        self.inlet_threshold_temp = kwargs["inlet_threshold_temp"]
        self.outlet_threshold_temp = kwargs["outlet_threshold_temp"]
        self.monitor_threshold_temp = kwargs["monitor_threshold_temp"]
        self.fan_table = kwargs["fan_table"]
        self.inlet_temp = 0
        self.outlet_temp = 0
        self.monitor_temp = 0

        self.fan_run_mode = FanRunMode[kwargs["fan_run_mode"]]
        self.thermal_flag = False

    def start_manager(self):
        self.updater_running = True
        self.update_thread = Thread(target=self.updater)
        self.update_thread.isDaemon = True
        self.update_thread.start()

    def stop_manager(self):
        self.updater_running = False
        if self.update_thread is not None:
            self.update_thread.join(2)
        self.update_thread = None

    def updater(self):
        sleep(2)
        log.info("Setting default fan value...")
        for dev_id in self.fan_group:
            self.driver_manager.set_output(dev_id, self.default_fan_value)
        sleep(5)
        while self.updater_running:
            # update sensor data
            sdict = self.sensor_manager.sensor_data
            self.inlet_group.add_data_point(sdict)
            self.outlet_group.add_data_point(sdict)
            self.monitor_group.add_data_point(sdict)
            self.inlet_temp = self.inlet_group.value
            self.outlet_temp = self.outlet_group.value
            self.monitor_temp = self.monitor_group.value
            log.debug(f"{self.monitor_temp}, {self.inlet_temp}, {self.outlet_temp}")
            thermal_flag = False

            fan_dc = self.default_fan_value
            if self.inlet_temp > self.inlet_threshold_temp:
                thermal_flag = True

            if self.outlet_temp > self.outlet_threshold_temp:
                thermal_flag = True

            if self.monitor_temp > self.monitor_threshold_temp:
                thermal_flag = True

            if not thermal_flag:
                if self.fan_run_mode == FanRunMode.fan_table:
                    fan_dc = self.default_fan_value
                    for fcheck in self.fan_table:
                        if self.outlet_temp < fcheck[0]:
                            fan_dc = fcheck[1]
                elif self.fan_run_mode == FanRunMode.fan_speed:
                    pass
                elif self.fan_run_mode == FanRunMode.temp_control:
                    pass
                # self.driver_manager.unlock_group(self.driver_group, "thermal_manager")
            else:
                # self.driver_manager.lock_group(self.driver_group, "thermal_manager")
                pass

            self.thermal_flag = thermal_flag
            for dev_id in self.fan_group:
                log.debug(f"{dev_id}: {fan_dc}")
                self.driver_manager.set_output(dev_id, fan_dc)

            sleep(1)
        log.info("Setting low fan value")
        for dev_id in self.fan_group:
            self.driver_manager.set_output(dev_id, 10)



