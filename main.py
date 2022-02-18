#!/usr/bin/env python3
"""
(c) Meta, Inc. and its affiliates.  Confidential and proprietary.
Area 404 Thermal Test Control Software
Author: Ricardo Chavira

Main control for Thermal Test Systems.  Runs an instance of the main
control software to run automated TTV monitoring telemetry, and
exposing control aspects of the system to external controllers (PLC, Laptop)
via Modbus TCP
"""


import json
import logging
import time

from modbus_server import ModbusServer
from sensor_monitor import SensorMonitor
from system_manager import SystemManager

default_config = {
    "emulate_system": True,
    "modbus_config": {"address": "localhost", "port": 502},
    "fan_control_board_config": {"port": "/ttyusb0"},
    "gpio_config": {
        "mux_pins": [17, 22, 27, 5],
        "strobe": 23,
        "report_pin": 26,
        "input_pins": [6, 16],
    },
    "sensor_inputs": {
        "t1": {"channel": "T", "cs": 1},
        "t2": {"channel": "T", "cs": 2},
        "i1": {"channel": "0", "cs": 11, "min": 0, "max": 25},
        "i2": {"channel": "1", "cs": 11, "min": 0, "max": 25},
        "v1": {"channel": "4", "cs": 11, "min": 0, "max": 60},
        "v2": {"channel": "5", "cs": 11, "min": 0, "max": 60},
        "a1": {"channel": "2", "cs": 12, "min": 0, "max": 1024},
        "l1": {"channel": "3", "cs": 12, "min": 0, "max": 1024},
        "d1": {"channel": "I", "pin": 6},
        "d2": {"channel": "I", "pin": 16},
    },
    "driver_config": {"device_address": 64, "device_frequency": 60},
    "driver_outputs": {
        "ttv1": {"channel": 0, "default": 80},
        "fan1": {"channel": 4, "default": 20},
    },
    "leak_monitor": {
        "threshold": 400,
        "input": "l1",
        "shutdown_group": ["ttv1", "ttv2", "ttv3", "ttv4", "fan1", "fan2"],
    },
    "thermal_monitor": {
        "sensor_group": ["t9", "t10"],
        "sample_rate": 1,
        "sample_size": 60,
        "output_group": ["fan1", "fan2"],
        "behaviour_table": {
            "T1": {"temp": 40, "output_dc": 20},
            "T2": {"temp": 41, "output_dc": 25},
            "T3": {"temp": 42, "output_dc": 30},
            "T4": {"temp": 43, "output_dc": 35},
            "T5": {"temp": 44, "output_dc": 40},
            "SD": {"temp": 45, "output_dc": 80},
        },
        "shutdown_group": ["ttv1", "ttv2", "ttv3", "ttv4"],
    },
    "safety_monitor": {
        "default_shutdown_temp_C": 45,
        "driver_group": ["ttv1", "ttv2", "ttv3", "ttv4"],
    },
}

logging.basicConfig(
    filename="system.log", level=logging.DEBUG, format="%(asctime)s - %(message)s"
    #level=logging.DEBUG, format="%(asctime)s - %(message)s"
)


class ControlSystem(object):
    def __init__(self):
        self.config = {}
        self.sensors = None  # type: SensorMonitor
        self.system = None  # type: SystemManager
        self.modbus = None  # type: ModbusServer
        self.shutdown = False

    def load_config(self):
        logging.info("Loading config.json")
        with open("config.json") as f:
            try:
                self.config = json.load(f)
            except Exception as ex:
                logging.error(f"Problem loading config.json, {ex}")
                self.config = default_config
            f.close()

    def stop_server(self):
        self.modbus.stop_server()
        self.system.stop()
        self.sensors.stop_sensors()

    def run_system(self):
        # Initialize system drivers.....
        emulate = self.config["emulate_system"]
        logging.info("Initializing Main Control System...")
        logging.info(f"System Emulation: {emulate}")
        # start sensors
        logging.info("Initializing Sensors...")
        self.sensors = SensorMonitor(emulate, **self.config)
        if not emulate:
            self.sensors.start_sensors()

        # start system
        logging.info("Initializing System Manager...")
        self.system = SystemManager(self.sensors, **self.config)
        self.system.run()
        # start modbus interface
        logging.info("Initializing Modbus Server...")
        self.modbus = ModbusServer(**self.config)
        self.modbus.start_server()

        # last_run_mode = 2
        # last_target = -1

        logging.info("Starting Main System Control Loop...")
        try:
            while not self.shutdown:
                # get modbus run values
                pt = self.modbus.get_power_target()
                rs = self.modbus.get_run_status()
                sd = self.modbus.get_shutdown_cmd()

                if sd == 0xDEAD:
                    self.shutdown = True
                    break

                self.system.set_power_target(pt)
                self.system.run_power = rs != 0

                # update telemetry
                if emulate:
                    sdict = self.modbus.get_emulated_values()
                    self.sensors.set_sensor_emulation(sdict)

                self.modbus.update_sensor_info(self.sensors.get_sensor_dict())

                # update flags
                self.modbus.update_system_flags(
                    self.system.run_power,
                    self.system.system_flag,
                    self.system.leak_flag,
                    self.system.thermal_flag,
                    self.sensors.sensor_flag,
                    self.system.current_power,
                    self.system.time_at_power_level
                    )

                # update driver states
                ddict = self.system.get_driver_states()
                self.modbus.update_driver_states(ddict)
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Stopping Server")
            self.shutdown = True
            self.stop_server()


if __name__ == "__main__":
    cs = ControlSystem()
    cs.load_config()
    cs.run_system()
