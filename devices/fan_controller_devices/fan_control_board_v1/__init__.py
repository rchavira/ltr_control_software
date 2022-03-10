import logging

from serial import Serial
from devices.fan_controller_devices import FanSpeedInterface
from threading import Thread
from time import sleep


log = logging.getLogger(__name__)

default_config = {
    "port" : "/dev/ttyusb0",
    "baudrate": 115200,
    "timeout": 0.5,
    "channel_count": 8
}


class FCBv1Interface(FanSpeedInterface):
    ser: Serial
    update_thread: Thread

    def __init__(self, **kwargs):
        self.channels = {}
        super().__init__(**kwargs)

        self.port = kwargs["port"]
        self.baudrate = kwargs["baudrate"]
        self.timeout = kwargs["timeout"]
        self.channel_count = kwargs["channel_count"]
        self.temperature = 0

        for i in range(self.channel_count):
            self.channels[i] = 0

        self.ser = None
        try:
            self.ser = Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
        except Exception as ex:
            log.error(ex)

        self.update_thread = None
        self.updater_running = False

    def start_updater(self):
        self.update_thread = Thread(target=self.updater)
        self.update_thread.isDaemon = True
        self.updater_running = True
        self.update_thread.start()
        sleep(1)

    def stop_updater(self):
        self.updater_running = False
        if self.update_thread is not None:
            self.update_thread.join(2)
        self.update_thread = None

    def init_device(self):
        if self.ser is not None:
            if self.ser.closed:
                self.ser.open()

    def close_device(self):
        if self.ser is not None:
            self.ser.close()

    def updater(self):
        while self.updater_running:
            if self.ser is not None:
                while self.ser.in_waiting:
                    sleep(0.2)
                    data = self.ser.readline()
                    self.process_data(data.decode("utf-8"))

    def process_data(self, data):
        log.debug(f"FCB: {data}")
        if len(data.split(':')) == 2:
            if "Channel[" in data:
                channel = int(data.split("[")[1].split("]")[0])
                if "]_rpm:" in data:
                    self.channels[channel] = int(data.split(":")[1])
            elif "Temperature:" in data:
                self.temperature = float(data.split(":")[1])


