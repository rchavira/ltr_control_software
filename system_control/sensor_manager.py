import logging
from enum import Enum
from threading import Thread
from time import sleep

from devices.adc_manager import AdcManager
from devices.bus_manager import BusManager
from devices.chip_select import ChipSelector
from devices.dio_devices import DioInterface
from devices.fan_controller_devices import FanSpeedInterface
from devices.thermo_manager import ThermoManager
from system_control.sensor_aggregator import SensorAggregator

log = logging.getLogger(__name__)

default_config = {
    "adc": {
        "update_interval": 1,
        "devices": {
            "adc1": {
                "device_type": "emulated",
                "chip_select": 11,
                "input_file": "test.txt",
                "resolution": 1024,
                "devices": {"leak_1": {"channel": 3, "min_val": 0, "max_val": 1024}},
            }
        },
    },
    "thermo": {
        "update_interval": 1,
        "temp_decimals": 2,
        "devices": {
            "t1": {
                "device_type": "emulated",
                "config": {
                    "junction_values_file": "test.txt",
                    "internal_values_file": "test2.txt",
                    "flag_values_file": "test3.txt",
                },
            },
            "t2": {
                "device_type": "emulated",
                "config": {
                    "junction_values_file": "test.txt",
                    "internal_values_file": "test2.txt",
                    "flag_values_file": "test3.txt",
                },
            },
        },
    },
    "fan_speed_device_type": "fan_control_board",
    "fan_speed_device": {
        "port": "/dev/ttyusb0",
        "baudrate": 115200,
        "timeout": 0.5,
        "channel_count": 8,
    },
    "internal_leak_dev_id": "leak_1",
    "leak_detection_mode": "delta",
    "leak_detection_value": 100,
    "external_leak_pin": 1,
    "leak_report_out_pin": 2,
    "leak_report_active": 0,
    "leak_report_inactive": 1,
    "leak_sample_rate": 10,
}


class LeakDetectionModes(Enum):
    disabled = 0
    digital = 1
    threshold = 2
    delta = 3
    range = 4


class SensorManager(object):
    adc_inputs: AdcManager
    thermo_inputs: ThermoManager
    spi: BusManager
    i2c: BusManager
    ch_sel: ChipSelector
    dio: DioInterface
    update_thread: Thread
    fan_speed_device: FanSpeedInterface

    def __init__(self, spi, i2c, ch_sel, dio, adc, thermo, fans, **kwargs):
        self.spi = spi
        self.i2c = i2c
        self.ch_sel = ch_sel
        self.dio = dio

        self.internal_leak_dev_id = kwargs["internal_leak_dev_id"]
        self.external_leak_pin = kwargs["external_leak_pin"]
        self.leak_report_out_pin = kwargs["leak_report_out_pin"]
        self.leak_detection_mode = LeakDetectionModes[kwargs["leak_detection_mode"]]
        self.leak_detection_value = kwargs["leak_detection_value"]
        self.leak_sample_rate = kwargs["leak_sample_rate"]
        self.leak_report_active = kwargs["leak_report_active"]
        self.leak_report_inactive = kwargs["leak_report_inactive"]

        # ADC Initialization
        self.adc_inputs = adc

        # Thermocouple Initialization
        self.thermo_inputs = thermo

        self.update_thread = None
        self.updater_running = False

        self.fan_speed_device = fans

        self.sensor_flag = False
        self.leak_flag = False
        self.leak_data = SensorAggregator(
            self.internal_leak_dev_id, self.leak_sample_rate
        )

        self.sensor_data = {}

    def start_manager(self):
        self.update_thread = Thread(target=self.updater)
        self.updater_running = True
        self.update_thread.isDaemon = True
        self.update_thread.start()
        sleep(1)

    def stop_manager(self):
        self.updater_running = False
        if self.update_thread is not None:
            self.update_thread.join(2)

    def updater(self):
        while self.updater_running:
            self.get_sensor_data()

            # check for sensor flags
            sensor_flag = False
            for dev_id in self.thermo_inputs.device_data.keys():
                if not sensor_flag:
                    sensor_flag = self.thermo_inputs.device_data[dev_id].flag
                    break

            self.sensor_flag = sensor_flag

            # leak checking

            leak_flag = False

            # self.leak_data.add_data_point(self.sensor_data)
            leak_value = self.sensor_data[self.internal_leak_dev_id]

            if self.internal_leak_dev_id in self.sensor_data.keys():
                if self.leak_detection_mode == LeakDetectionModes.digital:
                    if int(leak_value) != self.leak_detection_value:
                        leak_flag = True
                elif self.leak_detection_mode == LeakDetectionModes.threshold:
                    if leak_value > self.leak_detection_value:
                        leak_flag = True
                elif self.leak_detection_mode == LeakDetectionModes.delta:
                    if self.leak_data.get_delta() > self.leak_detection_value:
                        leak_flag = True
                elif self.leak_detection_mode == LeakDetectionModes.range:
                    if self.leak_data.get_range() > self.leak_detection_value:
                        leak_flag = True
            log.debug(
                f"{self.internal_leak_dev_id}: {self.sensor_data[self.internal_leak_dev_id]}"
            )
            log.debug(
                f"Leak flag: {leak_flag} leak_value:{leak_value} threshold:{self.leak_detection_value}"
            )

            if leak_flag:
                self.dio.write_digital(self.external_leak_pin, self.leak_report_active)
            else:
                self.dio.write_digital(
                    self.external_leak_pin, self.leak_report_inactive
                )

            self.leak_flag = leak_flag

            sleep(0.5)

    def get_sensor_data(self):
        # log.debug(f"Reading {len(self.adc_inputs.data)} ADC inputs...")
        for dev_id in self.adc_inputs.data.keys():
            self.sensor_data[dev_id] = self.adc_inputs.get_values(dev_id)[0]

        # log.debug(f"Reading {len(self.thermo_inputs.device_data)} Thermo inputs...")
        for dev_id in self.thermo_inputs.device_data.keys():
            self.sensor_data[dev_id] = self.thermo_inputs.get_values(dev_id)[0]

        # log.debug(f"Reading {len(self.dio.input_pins)} Digital inputs...")
        for pin in self.dio.input_pins:
            dev_id = f"d{pin}"
            self.sensor_data[dev_id] = self.dio.read_digital(pin)

        # log.debug(f"Reading {len(self.fan_speed_device.channels)} Fan Speed inputs...")
        for i in range(len(self.fan_speed_device.channels)):
            dev_id = f"fan_rpm{i+1}"
            self.sensor_data[dev_id] = self.fan_speed_device.channels[i]

        dev_id = f"tFCB"
        self.sensor_data[dev_id] = self.fan_speed_device.temperature


def test():
    sm = SensorManager(**default_config)
    sm.start_manager()
    while True:
        for dev_id in sm.sensor_data.keys():
            print(f"{dev_id}: {sm.sensor_data[dev_id]}")

        try:
            sleep(1)
        except KeyboardInterrupt:
            break

    sm.stop_manager()
    sm = None
