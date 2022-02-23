import logging
import threading
import time

from fanboard_interface import FanBoardInterface, FanBoardEmulate
from raspi_interface import RaspiInterface, RaspiEmulate

log = logging.getLogger(__name__)


class SensorInput(object):
    def __init__(self):
        self.value = 0

    def set_value(self, value):
        self.value = float(value)

    def get_value(self):
        return self.value


class ThermocoupleInput(SensorInput):
    internalC = 0
    tempC = 0
    data = 0
    openCircuit = False
    shortGround = False
    shortVCC = False
    fault = False

    def __init__(self):
        self.data = 0
        super().__init__()

    def set_value(self, data):
        self.data = int.from_bytes(data, "big")
        if self.data > 0:
            self.set_internal()
            self.set_temp()
            self.set_flags()
        self.value = self.tempC

    def set_internal(self):
        v = self.data >> 4
        v = v & 0x7FF
        if v & 0x800:
            v -= 4096

        self.internalC = v * 0.0625

    def set_temp(self):
        v = self.data
        if v & 0x7:
            return float("NaN")
        if v & 0x80000000:
            v >>= 18
            v -= 16384
        else:
            v >>= 18

        self.tempC = v * 0.25

    def set_flags(self):
        v = self.data
        self.openCircuit = (v & (1 << 0)) > 0
        self.shortGround = (v & (1 << 1)) > 0
        self.shortVCC = (v & (1 << 2)) > 0
        self.fault = (v & (1 << 16)) > 0


class AnalogInput(SensorInput):
    def __init__(self):
        super().__init__()


class DigitalInput(SensorInput):
    def __init__(self):
        super().__init__()


class FanInput(SensorInput):
    def __init__(self):
        self.temp = 0
        self.rpm = 0
        self.pwm = 0
        super().__init__()

    def set_value(self, value):
        self.rpm = value
        self.value = value

    def set_temp(self, value):
        self.temp = value

    def set_pwm(self, value):
        self.pwm = value


class SensorMonitor(object):
    # __slots__ = ["thermocouples", "analoginputs", "digitalinputs"]

    def __init__(self, emulate, **kwargs):
        self.gpio_config = kwargs["gpio_config"]
        self.sensor_inputs = kwargs["sensor_inputs"]
        self.fanboard_config = kwargs["fan_control_board_config"]
        self.emulate = emulate

        self.raspi = None  # type: RaspiInterface
        self.fanboard = None  # type: FanBoardInterface

        if not self.emulate:
            from raspi_hardware import RaspiGPIO

            self.raspi = RaspiGPIO(**self.gpio_config)

            from fanboard_hardware import FanBoardHardware

            self.fanboard = FanBoardHardware(**self.fanboard_config)
        else:
            self.raspi = RaspiEmulate(**self.gpio_config)
            self.fanboard = FanBoardEmulate(**self.fanboard_config)

        self.thermocouples = 0
        self.digitalinputs = 0
        self.analoginputs = 0
        self.faninputs = 0
        self.sensor_flag = False

        self.sensorvalues = {}

        for si in self.sensor_inputs.keys():
            if self.sensor_inputs[si]["type"] == "T":
                self.thermocouples += 1
                self.sensorvalues[si] = SensorInput()
            elif self.sensor_inputs[si]["type"] == "D":
                self.digitalinputs += 1
                self.sensorvalues[si] = DigitalInput()
            elif self.sensor_inputs[si]["type"] == "A":
                self.analoginputs += 1
                self.sensorvalues[si] = AnalogInput()
            elif self.sensor_inputs[si]["type"] == "F":
                if self.sensor_inputs[si]["channel"] != "T":
                    self.faninputs += 1
                    self.sensorvalues[si] = FanInput()
                else:
                    self.faninputs += 1
                    self.sensorvalues[si] = SensorInput()

        log.info(
            f"Initializing {self.thermocouples} thermocouples,{self.digitalinputs} digital inputs,{self.analoginputs} analog inputs and {self.faninputs} fan inputs"
        )
        self.sensor_loop = None
        self.sensors_running = False

    def start_sensors(self):
        log.info("Starting Sensors...")
        self.fanboard.start_monitor()
        self.sensor_loop = threading.Thread(target=self.sensor_thread)
        self.sensor_loop.isDaemon = True
        self.sensor_loop.start()
        log.info("Sensor Monitoring Started")

    def stop_sensors(self):
        log.info("Stopping Sensors...")
        self.fanboard.stop_monitor()
        self.sensors_running = False
        if self.sensor_loop is not None:
            self.sensor_loop.join(2)
        self.sensor_loop = None
        log.info("Sensor Monitoring Stopped")
        self.raspi.shutdown()

    @staticmethod
    def remap(x, oMin, oMax, nMin, nMax):

        # range check
        if oMin == oMax:
            print("Warning: Zero input range")
            return None

        if nMin == nMax:
            print("Warning: Zero output range")
            return None

        # check reversed input range
        reverseInput = False
        oldMin = min(oMin, oMax)
        oldMax = max(oMin, oMax)
        if not oldMin == oMin:
            reverseInput = True

        # check reversed output range
        reverseOutput = False
        newMin = min(nMin, nMax)
        newMax = max(nMin, nMax)
        if not newMin == nMin:
            reverseOutput = True

        portion = (x - oldMin) * (newMax - newMin) / (oldMax - oldMin)
        if reverseInput:
            portion = (oldMax - x) * (newMax - newMin) / (oldMax - oldMin)

        result = portion + newMin
        if reverseOutput:
            result = newMax - portion

        return result

    def report_out(self, value):
        self.raspi.set_report_out(value)

    def sensor_thread(self):
        self.sensors_running = True
        last_cs = 0
        log.info("Sensors Started.")
        sf = False
        while self.sensors_running:
            # cycle through sensor list...
            sf = False
            if not self.emulate:
                for si in self.sensor_inputs.keys():
                    if self.sensor_inputs[si]["type"] == "T":
                        if self.sensor_inputs[si]["channel"] == "MAX31855":
                            cs = self.sensor_inputs[si]["cs"]
                            self.raspi.chip_select(cs)

                        try:
                            data = self.raspi.read_thermo(self.sensor_inputs[si]["channel"])
                            if self.raspi.thermo_flag:
                                sf = True
                            self.sensorvalues[si].set_value(data)
                        except Exception as ex:
                            log.error(ex)
                    elif self.sensor_inputs[si]["type"] == "D":
                        pin = self.sensor_inputs[si]["pin"]
                        data = self.raspi.read_digital(pin)
                        self.sensorvalues[si].set_value(data)
                    elif self.sensor_inputs[si]["type"] == "A":
                        cs = self.sensor_inputs[si]["cs"]
                        self.raspi.chip_select(cs)
                        dmin = float(self.sensor_inputs[si]["min"])
                        dmax = float(self.sensor_inputs[si]["max"])

                        data = self.raspi.read_adc(self.sensor_inputs[si]["channel"])
                        data = self.remap(data, 0, 1023, dmin, dmax)

                        self.raspi.chip_select(15)
                        self.sensorvalues[si].set_value(data)
                    elif self.sensor_inputs[si]["type"] == "F":
                        ch = self.sensor_inputs[si]["channel"]
                        if ch != "T":
                            self.sensorvalues[si].set_value(self.fanboard.rpm_values[int(ch)])
                        else:
                            self.sensorvalues[si].set_value(self.fanboard.temperature)

                self.sensor_flag = sf
                time.sleep(0.1)
            else:
                time.sleep(1)

    def get_sensor_dict(self):
        sensor_data = {}
        for ch in self.sensorvalues.keys():
            sensor_data[ch] = self.sensorvalues[ch].get_value()

        return sensor_data

    def set_sensor_emulation(self, sdict):
        for ch in self.sensorvalues.keys():
            self.sensorvalues[ch].value = sdict[ch]

        sensor_data = self.get_sensor_dict()
        return sensor_data
