import logging
import threading


log = logging.getLogger(__name__)


class FanBoardInterface(object):
    def __init__(self, **kwargs):
        self.rpm_values = {}
        self.pwm_values = {}
        self.temperature = 0
        self.manual = False
        self.rpm_div = 0
        self.report_delay = 0
        self.report_output = 0
        self.temperature = 0

        self.monitor_running = False
        self.monitor_loop = threading.Thread(target=self.monitor_thread)

        for i in range(16):
            self.rpm_values[i] = 0

    def start_monitor(self):
        log.info("Starting Fan Interface...")
        self.monitor_loop = threading.Thread(target=self.monitor_thread)
        self.monitor_loop.isDaemon = True
        self.monitor_loop.start()
        log.info("Fan Interface Started")

    def stop_monitor(self):
        log.info("Stopping Fan Interface...")
        self.monitor_running = False
        if self.monitor_loop is not None:
            self.monitor_loop.join(2)

        self.monitor_loop = None
        log.info("Fan Interface Stopped")

    def monitor_thread(self):
        self.monitor_running = True

    def process_data(self, data):
        # log.info(data)
        if len(data.split(':'))==2:
            if "rpm_div:" in data:
                self.rpm_div = data.split(":")[1]
            elif "report_delay:" in data:
                self.report_delay = data.split(":")[1]
            elif "report_output:" in data:
                self.report_output = data.split(":")[1]
            elif "Mode:" in data:
                self.manual = data.split(":")[1] == 1
            elif "Channel[" in data:
                channel = int(data.split("[")[1].split("]")[0])
                if "]_rpm:" in data:
                    self.rpm_values[channel] = int(data.split(":")[1])
                elif "]_pwm:" in data:
                    self.pwm_values[channel] = int(data.split(":")[1])
            elif "Temperature:" in data:
                self.temperature = float(data.split(":")[1])


class FanBoardEmulate(FanBoardInterface):
    def __init__(self, **kwargs):

        super().__init__(**kwargs)

    def set_temp(self, value):
        data = f"Temperature:{value}"
        self.process_data(data)

    def set_rpm(self, value):
        for i in range(8):
            data = f"Channel[{i}]_rpm:{value}"
            self.process_data(data)
