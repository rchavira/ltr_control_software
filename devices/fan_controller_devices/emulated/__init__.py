import logging
from threading import Thread
from time import sleep

from devices.emulation_helpers import get_next_int, get_next_float
from devices.fan_controller_devices import FanSpeedInterface

log = logging.getLogger(__name__)

default_config = {
    "channel_count": 8,
    "values_file": "fan_speed_values.txt",
    "temp_file": "test.txt",
}


class EmulatedFanSpeed(FanSpeedInterface):
    def __init__(self, **kwargs):
        self.channels = {}
        self.channel_count = kwargs["channel_count"]
        self.values_file = kwargs["values_file"]
        self.temp_file = kwargs["temp_file"]
        for i in range(self.channel_count):
            self.channels[i] = 0

        self.temperature = 0.0
        self.update_thread = None
        self.updater_running = False

    def start_updater(self):
        self.update_thread = Thread(target=self.updater)
        self.update_thread.isDaemon = True
        self.updater_running = True
        self.update_thread.start()

    def stop_updater(self):
        self.updater_running = False
        if self.update_thread is not None:
            self.update_thread.join(2)
        self.update_thread = None

    def updater(self):
        while self.updater_running:
            for i in range(self.channel_count):
                self.channels[i] = get_next_int(self.values_file)

            self.temperature = get_next_float(self.temp_file)
            sleep(1)
