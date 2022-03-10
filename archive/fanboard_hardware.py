import logging

import serial
from fanboard_interface import FanBoardInterface

log = logging.getLogger(__name__)


class FanBoardHardware(FanBoardInterface):
    def __init__(self, **kwargs):
        self.port = kwargs["port"]
        self.baudrate = kwargs["baudrate"]
        self.timeout = kwargs["timeout"]
        self.fcb = None  # type:  serial.Serial
        try:
            self.fcb = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
        except Exception as ex:
            log.error(ex)

        super().__init__(**kwargs)

    def monitor_thread(self):
        self.monitor_running = True
        while self.monitor_running:
            if self.fcb is not None:
                while self.fcb.in_waiting:
                    data = self.fcb.readline()
                    self.process_data(data.decode("utf-8"))

        if self.fcb is not None:
            self.fcb.close()
