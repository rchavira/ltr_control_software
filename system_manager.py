import logging
import threading
import time
import subprocess

from driver_interface import DriverInterface
from output_control import OutputControl
from sensor_aggregator import SensorAggregator
from sensor_monitor import SensorMonitor
from driver_hardware import DriverHardware

log = logging.getLogger(__name__)


class SystemManager(object):
    def __init__(self, sensor_monitor, **kwargs):
        self.drivers = None  # type: DriverInterface
        self.emulate = kwargs["emulate_system"]
        self.thermal_config = kwargs["thermal_monitor"]
        self.leak_config = kwargs["leak_monitor"]
        self.sensor_monitor = sensor_monitor  # type: SensorMonitor
        self.power_config = kwargs["normal_operation"]
        self.power_target = self.power_config["default_power_target"]
        self.power_step = self.power_config["power_step"]
        self.step_delay = self.power_config["step_delay"]
        self.run_power = False
        self.current_power = 0
        self.time_at_power_level = 0

        self.leak_flag = False
        self.thermal_flag = False
        self.system_flag = False

        self.config = kwargs

        """ if self.emulate:
            self.drivers = DriverInterface(**kwargs)
        else:
            from driver_hardware import DriverHardware

            self.drivers = DriverHardware(**kwargs) """

        self.outputs = {}
        for dout in kwargs["driver_outputs"].keys():
            channel = kwargs["driver_outputs"][dout]["channel"]
            default = kwargs["driver_outputs"][dout]["default"]
            self.outputs[dout] = OutputControl(channel, default)

        self.thermal_loop = None  # type: threading.Thread
        self.thermal_loop_running = False

        self.leak_detect_loop = None  # type: threading.Thread
        self.leak_detect_loop_running = False

        self.main_control_loop = None  # type: threading.Thread
        self.main_control_loop_running = False

    def set_power_target(self, value):
        if value <= self.power_config["max_power"]:
            self.power_target = value

    def run(self):
        self.start_thermal_monitor()
        self.start_leak_monitor()
        self.start_main()

    def stop(self):
        self.e_stop_activate()
        self.stop_thermal_monitor()
        self.stop_leak_monitor()
        self.stop_main()

    def start_main(self):
        log.info("Starting Main Power loop...")
        self.main_control_loop = threading.Thread(target=self.main_loop)
        self.main_control_loop.isDaemon = True
        self.main_control_loop.start()
        log.info("Main Power loop Started")

    def stop_main(self):
        log.info("Stopping Main Power Loop")
        self.main_control_loop_running = False
        if self.main_control_loop is not None:
            self.main_control_loop.join(2)
        self.main_control_loop = None
        log.info("Main Power loop Stopped")

    def main_loop(self):
        # once reliable current and voltage readings are obtained... this loop will become a PID
        rg = self.power_config["run_group"]
        mp = int(self.power_config["max_power"])
        dc = int(float(int(self.power_target) / mp)*100)
        counter = 0
        last_change = 0
        last_power = 0
        self.current_power = 0  # current power
        self.main_control_loop_running = True
        while self.main_control_loop_running:
            if self.run_power:
                # calculate power setting...
                # TODO: add power ramp up...
                if self.current_power < self.power_target:
                    if last_power != self.current_power:
                        step = self.power_step  #  100W steps, x 8 for each ttv
                        if self.power_target - self.current_power < step:
                            step = self.power_target - self.current_power
                        self.current_power += step
                        last_poewr = self.current_power
                        last_change = time.time()
                    else:
                        if time.time() - last_change >= self.step_delay:
                            step = self.power_step  #  100W steps, x 8 for each ttv
                            if self.power_target - self.current_power < step:
                                step = self.power_target - self.current_power
                            self.current_power += step
                            last_poewr = self.current_power
                            last_change = time.time()
                else:
                    self.current_power = self.power_target
                    last_power = self.current_power

                dc = int(float(int(self.current_power) / mp)*100)
                self.set_outputs(rg, dc)
            else:
                self.current_power = 0
                last_power = self.current_power
                last_change = time.time()
                self.set_outputs(rg, 0)

            if time.time() - last_change > self.step_delay:
                last_change = time.time() - self.step_delay

            self.time_at_power_level = int(time.time() - last_change)
            time.sleep(1)
        self.set_outputs(rg, 0)

    def stop_thermal_monitor(self):
        log.info("Stopping Thermal Monitor...")
        self.thermal_loop_running = False
        self.thermal_loop.join(2)
        self.thermal_loop = None
        log.info("Thermal Monitor Stopped")

    def start_thermal_monitor(self):
        log.info("Starting Thermal Monitor...")
        self.thermal_loop = threading.Thread(target=self.thermal_monitor)
        self.thermal_loop.isDaemon = True
        self.thermal_loop.start()
        log.info("Thermal Monitor Started")

    def thermal_monitor(self):
        self.thermal_loop_running = True
        sdata = SensorAggregator(self.thermal_config["sensor_group"], self.thermal_config["sample_size"])
        tcdata = SensorAggregator(self.thermal_config["ttv_sensor_group"], self.thermal_config["ttv_sensor_sample_size"])
        btbl = self.thermal_config["behaviour_table"]
        while self.thermal_loop_running:
            sdict = self.sensor_monitor.get_sensor_dict()
            sdata.add_data_point(sdict)
            tcdata.add_data_point(sdict)

            t_data = tcdata.get_running_mean()
            if t_data < self.thermal_config["ttv_sd_temp"]:
                self.unlock_outputs(
                    self.thermal_config["output_group"], "ttv_thermal_monitor"
                )
                t_data = sdata.get_running_mean()
                if t_data < btbl["T1"]["temp"]:
                    self.set_outputs(
                        self.thermal_config["output_group"], btbl["T1"]["output_dc"]
                    )
                elif t_data <= btbl["T2"]["temp"]:
                    self.set_outputs(
                        self.thermal_config["output_group"], btbl["T2"]["output_dc"]
                    )
                elif t_data <= btbl["T3"]["temp"]:
                    self.set_outputs(
                        self.thermal_config["output_group"], btbl["T3"]["output_dc"]
                    )
                elif t_data <= btbl["T4"]["temp"]:
                    self.set_outputs(
                        self.thermal_config["output_group"], btbl["T4"]["output_dc"]
                    )
                elif t_data <= btbl["T5"]["temp"]:
                    self.set_outputs(
                        self.thermal_config["output_group"], btbl["T5"]["output_dc"]
                    )

                if t_data >= btbl["SD"]["temp"]:
                    self.set_outputs(
                        self.thermal_config["output_group"], btbl["SD"]["output_dc"]
                    )
                    # lock out shutdown group
                    self.lock_outputs(
                        self.thermal_config["shutdown_group"], "thermal_monitor"
                    )
                    self.thermal_flag = True
                else:
                    # remove the thermal lock
                    self.unlock_outputs(
                        self.thermal_config["shutdown_group"], "thermal_monitor"
                    )
                    self.thermal_flag = False
            else:
                self.thermal_flag = True
                self.lock_outputs(
                    self.thermal_config["shutdown_group"], "ttv_thermal_monitor"
                )

            time.sleep(self.thermal_config["sample_rate"])


    def stop_leak_monitor(self):
        log.info("Stopping Leak Monitor...")
        self.leak_detect_loop_running = False
        self.leak_detect_loop.join(2)
        self.leak_detect_loop = None
        log.info("Leak Monitor Stopped")

    def start_leak_monitor(self):
        log.info("Starting Leak Monitor...")
        self.leak_detect_loop = threading.Thread(target=self.leak_monitor)
        self.leak_detect_loop.isDaemon = True
        self.leak_detect_loop.start()
        log.info("Leak Monitor Started")

    def leak_monitor(self):
        self.leak_detect_loop_running = True
        sdata = SensorAggregator(
            [self.leak_config["internal"]], self.leak_config["sample_size"]
        )

        while self.leak_detect_loop_running:
            sdict = self.sensor_monitor.get_sensor_dict()
            sdata.add_data_point(sdict)
            t_data = sdata.get_running_mean()

            if t_data > self.leak_config["threshold"]:
                log.info(f"Internal Leak detected value={t_data}, threshold={self.leak_config['threshold']}")
                self.lock_outputs(self.leak_config["shutdown_group"], "leak_monitor")
                self.sensor_monitor.report_out(0)
                self.leak_flag = True
            else:
                self.unlock_outputs(self.leak_config["shutdown_group"], "leak_monitor")
                self.sensor_monitor.report_out(1)
                self.leak_flag = False
            time.sleep(self.leak_config["sample_rate"])

            # check external leak signal
            # print(f"ext_leak: {sdict[self.leak_config['external']]}")
            # if sdict[self.leak_config["external"]] == 0:
                #log.info("External Leak Detected")
                # self.lock_outputs(self.leak_config["shutdown_group"], "leak_monitor")
                # todo: check if this signal is pulled up or down
                #self.sensor_monitor.report_out(1)
            # else:

    def e_stop_activate(self):
        self.system_flag = True
        for sout in self.outputs.keys():
            self.output[sout].lock("e_stop")

    def e_stop_deactivate(self):
        for sout in self.outputs.keys():
            self.output[sout].unlock("e_stop")
        self.system_flag = False

    def unlock_outputs(self, group, locker):
        for sout in group:
            self.outputs[sout].unlock(locker)

    def lock_outputs(self, group, locker):
        for sout in group:
            self.outputs[sout].lock(locker)

    def set_outputs(self, group, value):
        channels = {
            "ttv1": 0,
            "ttv2": 1,
            "ttv3": 2,
            "ttv4": 3,
            "fan1": 4,
            "fan2": 5
        }

        l = []
        for dout in group:
            l.append(f"[{dout}]: {self.outputs[dout].get_value()}")

        outputs = ",".join(l)

        drv = DriverHardware(**self.config)

        for dout in group:
            self.outputs[dout].set_output(value)
            if dout in channels.keys():
                v = self.outputs[dout].get_value()
                drv.set_duty_cycle(channels[dout], v)

        l = []
        for dout in group:
            l.append(f"[{dout}]: {self.outputs[dout].get_value()}")

        outputs_new = ",".join(l)
        if outputs != outputs_new:
            print(outputs_new)

    def get_driver_states(self):
        driver_dict = {}
        for ch in self.outputs.keys():
            driver_dict[ch] = self.outputs[ch].get_value()
        return driver_dict
