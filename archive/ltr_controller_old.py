# Copyright 2004-present Facebook. All Rights Reserved.

# @lint-ignore-every PYTHON3COMPATIMPORTS1

# @nolint
"""
LTR Interface board control software
"""


#  raspi board imports
from board import SCL, SDA
import busio
import spidev
import RPi.GPIO as GPIO

#  pwm PCA9685 imports
from adafruit_pca9685 import PCA9685

#  pymodbus imports
from pymodbus.version import version
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

import threading
import queue
import time

OFF_CMD = 0
PWM_SET_CMD = 1
TEMP_SET_CMD = 2
CURRENT_SET_CMD = 3
SPEED_SET_CMD = 4

TTV_TARGET = 0
FAN_TARGET = 1
TORRENT_TARGET = 2

config = {
    "modbus_server_address": "localhost",
    "modbus_server_port" : 502,
    "pwm_device_address": 64,
    "pwm_device_frequency": 60,
    "gpio_config": {
        "mux": { "pins": (17, 22, 27, 5), "strobe": 23, "strobe_delay": 0.1},
        "leak": { "ext": 6, "report": 26, "threshold": 400, "leak_ain": "leak_sensor"},
        "manual": { "pin": 16, "ain": "ttv_ain"}
    },
    "input_channels" : {
        "tc1": { "data": "T", "cs": 1},
        "tc2": { "data": "T", "cs": 2},
        "tc3": { "data": "T", "cs": 3},
        "tc4": { "data": "T", "cs": 4},
        "tc5": { "data": "T", "cs": 5},
        "tc6": { "data": "T", "cs": 6},
        "tc7": { "data": "T", "cs": 7},
        "tc8": { "data": "T", "cs": 8},
        "tc9": { "data": "T", "cs": 9},
        "tc10": { "data": "T", "cs": 10},
        "ttv_vi_1": {"data": "0", "cs": 11},
        "ttv_vi_2": {"data": "1", "cs": 11},
        "ttv_vi_3": {"data": "2", "cs": 11},
        "ttv_vi_4": {"data": "3", "cs": 11},
        "ttv_vs_1": {"data": "4", "cs": 11},
        "ttv_vs_2": {"data": "5", "cs": 11},
        "ttv_vs_3": {"data": "6", "cs": 11},
        "ttv_vs_4": {"data": "7", "cs": 11},
        "outlet_t1": {"data": "0", "cs": 12},
        "outlet_t2": {"data": "1", "cs": 12},
        "ttv_ain": {"data": "2", "cs": 12},
        "leak_sensor": {"data": "3", "cs": 12},
        "outlet_temp1": {"data": "4", "cs": 12},
        "outlet_temp1": {"data": "5", "cs": 12},
        "system_vi": {"data": "6", "cs": 12}
    },
    "ttv_channels": {
        "ttv_bus_1": {
            "channel": 0,
            "active_dc_range": (40, 80),
            "max_current": 20.0,
            "voltage": 48.0
        },
        "ttv_bus_2": {
            "channel": 1,
            "active_dc_range": (40, 80),
            "max_current": 20.0,
            "voltage": 48.0
        },
        "ttv_bus_3": {
            "channel": 2,
            "active_dc_range": (40, 80),
            "max_current": 20.0,
            "voltage": 48.0
        },
        "ttv_bus_4": {
            "channel": 3,
            "active_dc_range": (40, 80),
            "max_current": 20.0,
            "voltage": 48.0
        }
    }
}


def remap( x, oMin, oMax, nMin, nMax ):

    #range check
    if oMin == oMax:
        print ("Warning: Zero input range")
        return None

    if nMin == nMax:
        print ("Warning: Zero output range")
        return None

    #check reversed input range
    reverseInput = False
    oldMin = min( oMin, oMax )
    oldMax = max( oMin, oMax )
    if not oldMin == oMin:
        reverseInput = True

    #check reversed output range
    reverseOutput = False
    newMin = min( nMin, nMax )
    newMax = max( nMin, nMax )
    if not newMin == nMin :
        reverseOutput = True

    portion = (x-oldMin)*(newMax-newMin)/(oldMax-oldMin)
    if reverseInput:
        portion = (oldMax-x)*(newMax-newMin)/(oldMax-oldMin)

    result = portion + newMin
    if reverseOutput:
        result = newMax - portion

    return result


class ChannelInfo(object):
    name = ""
    value = 0
    max_current = 0
    current = 0
    voltage = 0
    power = 0
    estimated_current = 0
    estimated_voltage = 0
    estimated_power = 0
    channel = 0

    def __init__(self, name, channel, group, max_current, voltage):
        self.name = name
        self.channel = channel
        self.max_current = max_current
        self.estimated_voltage = voltage

    def set_pwm(self, pwm):
        self.value = pwm
        self.estimated_current = remap(pwm, 0, 100, 0, self.max_current)
        self.estimated_power = self.estimated_voltage * self.estimated_current

    def set_voltage(self, voltage):
        self.voltage = voltage
        self._update_power()

    def set_current(self, current):
        self.current = current
        self._update_power()

    def _update_power(self):
        c = self.estimated_current
        v = self.estimated_voltage
        self.estimated_power = self.estimated_voltage * self.estimated_current

        if self.current > 0 and self.voltage > 0:
            self.power = self.current * self.voltage

class ModBusServer(object):
    class command_data(object):
        type = 0
        target = 0
        channel = 0
        value = 0

        def __init__(self, type, target, channel, value):
            self.type = type
            self.target = target
            self.channel = channel
            self.value = value

    def __init__(self, address, port):
        self.store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0] * 20),
            co=ModbusSequentialDataBlock(0, [0] * 20),
            hr=ModbusSequentialDataBlock(0, [0] * 350),
            ir=ModbusSequentialDataBlock(0, [0] * 350)
        )
        self.context = ModbusServerContext(slaves=self.store, single=True)
        self.command_q = queue.Queue()
        self.kill_ttvs = False
        self.kill_fans = False
        self.kill_torrents = False

        identity = ModbusDeviceIdentification()
        identity.VendorName = 'Facebook'
        identity.ProductCode = 'LTR'
        identity.ProductName = 'LTR Telemetry Server'
        identity.ModelName = 'LTR Interconnect Board'
        identity.MajorMinorRevision = "1.0.0"

        self.server_started = False

        self.mb_thread = threading.Thread(target=self.server_thread)
        self.mb_thread.isDaemon = True

        self.address = address
        self.port = port

        print("Starting Modbus TCP Server...")
        self.mb_thread.start()

        # set fw version
        values = [0x31, 0x30, 0x30]
        address = 0x96
        self.context[0].setValues(3, address, values)

        self.command_thread = threading.Thread(target=self.command_monitor)
        self.command_thread.isDaemon = True

        self.command_thread.start()


    def command_monitor(self):
        while True:
            self.get_commands()
            time.sleep(0.5)

    def server_thread(self):
        self.server_started = True
        try:
            StartTcpServer(self.context)
            # StartTcpServer(self.context, address=(self.address, self.port))
        except Exception as ex:
            print("Modbus Server Not Started!")
            print(ex)
            self.server_started = False

    def update_ttv_temperature(self, t_data, j_data):
        values = [0] * 8
        address = 0x14
        for idx in range(8):
            values[idx] = int(j_data[idx] * 100)

        self.context[0].setValues(3, address, values)

        address = 0x1e
        for idx in range(8):
            values[idx] = int(t_data[idx] * 100)

        self.context[0].setValues(3, address, values)

    def update_inlet_temperature(self, t_data, j_data):
        values = [0] * 2
        address = 0x1c
        for idx in range(2):
            values[idx] = int(j_data[idx] * 100)

        self.context[0].setValues(3, address, values)

        address = 0x26
        for idx in range(2):
            values[idx] = int(t_data[idx] * 100)

        self.context[0].setValues(3, address, values)

    def update_outlet_temperature(self, t_data):
        values = [0] * 2
        address = 0x28
        for idx in range(2):
            values[idx] = int(t_data[idx] * 10)

        self.context[0].setValues(3, address, values)

    def update_ttv_current(self, data):
        values = [0] * 4
        address = 0x32
        for idx in range(4):
            values[idx] = int(data[idx] * 100)

        self.context[0].setValues(3, address, values)

    def update_system_current(self, current):
        values = [int(current * 10)]
        address = 0x37
        self.context[0].setValues(3, address, values)

    def update_voltage(self, data):
        values = [0] * 4
        address = 0x46
        for idx in range(4):
            values[idx] = int(data[idx] * 100)

        self.context[0].setValues(3, address, values)

    def update_fan_speed(self, data):
        values = [0] * 8
        address = 0x64
        for idx in range(8):
            values[idx] = int(data[idx])

        self.context[0].setValues(3)

    def update_manual_commands(self, ttv_pwm):
        # set run mode
        address = 0xc8
        values = [1]
        self.context[0].setValues(3, address, values)

        address = 0xd2
        values = [ttv_pwm]
        self.context[0].setValues(3, address, values)

    def update_flags(self, flags):
        """
        flags[0] = internal leak detection
        flags[1] = external leak detection
        flags[2] = system active
        flags[3] = ttvs active
        flags[4] = fans active
        flags[5] = torrents active
        """
        values = [0] * 6
        address = 0
        for idx in flags:
            if flags[idx]:
                values[idx] = 0xff
        self.context[0].setValues(1, address, values)

    def shutdown(self):
        address = 10
        values = [0xff]
        self.context[0].setValues(address, values)

    def get_commands(self):
        address = 10
        values = self.context[0].getValues(1, address, count=4)
        self.kill_ttvs = False
        self.kill_fans = False
        self.kill_torrents = False

        if values[0] != 0:
            self.kill_ttvs = True
            self.kill_fans = True
            self.kill_torrents = True
        if values[1] != 0:
            self.kill_ttvs = True
        if values[2] != 0:
            self.kill_fans = True
        if values[3] != 0:
            self.kill_torrents = True

        if self.kill_ttvs:
            address = 0xc8
            values = [0] * 40
            self.context[0].setValues(3, address, values)
            print("Killing TTV Power")

        if self.kill_fans:
            address = 0xfa
            values = [0] * 40
            self.context[0].setValues(3, address, values)

        if self.kill_torrents:
            address = 0x12c
            values = [0] * 40
            self.context[0].setValues(3, address, values)

        #  get run modes...
        address = 0xc8
        values = self.context[0].getValues(3, address, count=5)
        run_modes = [0] * 4
        if values[0] != 0xff:
            for idx in range(4):
                run_modes[idx] = values[0]
                values[idx+1] = values[0]
            values[0] = 0xff  # reset command
            self.context[0].setValues(3, address, values)
        else:
            for idx in range(4):
                run_modes[idx] = values[idx+1]

        #  get DC values
        address = 0xd2
        values = self.context[0].getValues(3, address, count=5)
        dc_values = [0] * 4
        if values[0] != 0xff:
            for idx in range(4):
                dc_values[idx] = values[0]
                values[idx + 1] = values[0]
            values[0] = 0xff  # reset command
            self.context[0].setValues(3, address, values)
        else:
            for idx in range(4):
                dc_values[idx] = values[idx + 1]

        for idx in range(4):
            if run_modes[idx] == OFF_CMD:
                cmd = self.command_data(OFF_CMD, TTV_TARGET, idx, None)
                self.command_q.put_nowait(cmd)
                # print("Received OFF Command")
            elif run_modes[idx] == PWM_SET_CMD:
                cmd = self.command_data(PWM_SET_CMD, TTV_TARGET, idx, dc_values[idx])
                self.command_q.put_nowait(cmd)
                # print("Receved SET PWM Command")

        #  get Temp target values
        address = 0xdc
        values = self.context[0].getValues(3, address, count=5)
        t_values = [0] * 4
        if values[0] != 0xff:
            for idx in range(4):
                t_values[idx] = values[0]
                values[idx + 1] = values[0]
            values[0] = 0xff  # reset command
            self.context[0].setValues(3, address, values)
        else:
            for idx in range(4):
                t_values[idx] = values[idx + 1]

        for idx in range(4):
            if run_modes[idx] == TEMP_SET_CMD:
                cmd = self.command_data(TEMP_SET_CMD, TTV_TARGET, idx, t_values[idx])
                self.command_q.put_nowait(cmd)

        #  get current target values
        address = 0xdc
        values = self.context[0].getValues(3, address, count=5)
        c_values = [0] * 4
        if values[0] != 0xff:
            for idx in range(4):
                c_values[idx] = values[0]
                values[idx + 1] = values[0]
            values[0] = 0xff  # reset command
            self.context[0].setValues(3, address, values)
        else:
            for idx in range(4):
                c_values[idx] = values[idx + 1]

        for idx in range(4):
            if run_modes[idx] == CURRENT_SET_CMD:
                cmd = self.command_data(CURRENT_SET_CMD, TTV_TARGET, idx, c_values[idx])
                self.command_q.put_nowait(cmd)

class PwmDriver(object):

    def __init__(self, address, frequency):
        i2c_bus = busio.I2C(SCL, SDA)
        address = address
        try:
            self.pca = PCA9685(i2c_bus)
        except Exception as ex:
            print(ex)
            self.pca = None

        # self.pca.i2c_device.device_address = address
        if self.pca is not None:
            self.pca.frequency = frequency


    def set_pwm(self, channel, pwm):
        raw_v = remap(pwm, 0, 100, 0, 0xffff)
        if self.pca is not None:
            self.pca.channels[channel].duty_cycle = raw_v

class RaspiIoDriver(object):
    class ThermoInfo(object):
        internalC = 0
        tempC = 0
        openCircuit = False
        shortGround = False
        shortVCC = False
        fault = False

        def __init__(self, data):
            v = data >> 4
            v = v & 0x7ff
            if v & 0x800:
                v -= 4096

            self.internalC = v * 0.0625

            v = data
            if v & 0x7:
                return float('NaN')
            if v & 0x80000000:
                v >>= 18
                v -= 16384
            else:
                v >>= 18

            self.tempC = v * 0.25

            v = data
            self.openCircuit = (v & (1 << 0)) > 0
            self.shortGround = (v & (1 << 1)) > 0
            self.shortVCC = (v & (1 << 2)) > 0
            self.fault = (v & (1 << 16)) > 0

    class AnalogInputInfo(object):
        name = ""
        data = ""
        cs = 0
        value = 0
        value_ext = 0

        def __init__(self, name, data, cs):
            self.name = name
            self.data = data,
            self.cs = cs

        def set_value(self, value):
            self.value = value

        def get_value(self):
            return self.value

        def set_value_ext(self, value):
            self.value = value[0]
            self.value_ext  = value[1]

        def get_value_ext(self, idx):
            if idx == 0:
                return self.value
            else:
                return self.value_ext

    def __init__(self, input_channels, gpio_config):
        self.spi = spidev.SpiDev(0, 0)

        self.mux_pins = gpio_config["mux"]["pins"]
        self.mux_strobe = gpio_config["mux"]["strobe"]
        self.mux_strobe_delay = gpio_config["mux"]["strobe_delay"]

        self.leak_monitor = threading.Thread(target=self.leak_sensor_thread)
        self.leak_monitor.isDaemon = True
        self.leak_sensor_running = False
        self.input_monitor = threading.Thread(target=self.input_monitor_thread)
        self.input_monitor.isDaemon = True
        self.input_monitor_running = False

        self.leak_detected_callback = None

        self.leak_ext_gpio = gpio_config["leak"]["ext"]
        self.leak_report_gpio = gpio_config["leak"]["report"]
        self.leak_threshold = gpio_config["leak"]["threshold"]
        self.leak_ain = gpio_config["leak"]["leak_ain"]

        self.channels = {}

        self.manual_gpio = gpio_config["manual"]["pin"]
        self.manual_toggle = False

        for ch in input_channels:
            self.channels[ch] = self.AnalogInputInfo(ch, input_channels[ch]["data"], input_channels[ch]["cs"])

        for mp in self.mux_pins:  # + [self.mux_strobe, self.leak_report_gpio]:
            GPIO.setup(mp, GPIO.OUT)

        GPIO.setup(self.mux_strobe, GPIO.OUT)
        GPIO.setup(self.leak_report_gpio, GPIO.OUT)
        GPIO.setup(self.manual_gpio, GPIO.IN)
        GPIO.setup(self.leak_ext_gpio, GPIO.IN)

        self.input_monitor.start()
        self.leak_monitor.start()

    def leak_sensor_thread(self):
        self.leak_sensor_running = True
        while self.leak_sensor_running:
            if GPIO.input(self.leak_ext_gpio) == 0:
                if self.leak_detected_callback is not None:
                    self.leak_detected_callback()
            if self.channels[self.leak_ain].get_value() > self.leak_threshold:
                GPIO.output(self.leak_report_gpio, 1)
                if self.leak_detected_callback is not None:
                    self.leak_detected_callback()

            time.sleep(1)

    def chip_select(self, channel):
        #  bstr = format(channel, "b")
        bstr = '{0:04b}'.format(channel)
        for idx in range(4):
            GPIO.output(self.mux_pins[idx], int(bstr[idx]))

        GPIO.output(self.mux_strobe, 1)
        time.sleep(0.1)
        GPIO.output(self.mux_strobe, 0)

    def read_thermo(self):
        data = self._read32()
        return ThermoInfo(data)

    def _read32(self):
        raw = self.spi.read(4)
        if raw is None or len(raw) != 4:
            pass
        value = raw[0] << 24 | raw[1] << 16 | raw[2] << 8 | raw[3]
        return value

    def read_adc(self, channel):
        cmd = b''

        reply = spi.xfer2(cmd)
        adc = 0
        for n in reply:
            adc = (adc << 8) + n
        return adc

    def input_monitor_thread(self):
        self.input_monitor_running = True
        cs = 0
        while self.input_monitor_running:
            self.manual_toggle = (GPIO.input(self.manual_gpio) == 1)
            for ch in self.channels.keys():
                if self.channels[ch].cs != cs:
                    cs = self.channels[ch].cs
                    self.chip_select(cs)
                if self.channels[ch].data == "T":
                    thermo = self.read_thermo()  # type: ThermoInfo
                    self.channels[ch].set_value(thermo.tempC)
                    self.channels[ch].set_value_ext(thermo.internalC)
                else:
                    self.channels[ch].set_value(0)
            time.sleep(1)


class LtrServer(object):
    def __init__(self):
        self.channel_config = config["ttv_channels"]
        self.channels = {}
        self.channel_dict = []
        self.pwm = PwmDriver(config["pwm_device_address"], config["pwm_device_frequency"])
        for ch in self.channel_config:
            self.channels[ch] = ChannelInfo(
                name=ch,
                channel=self.channel_config[ch]["channel"],
                max_current=self.channel_config[ch]["max_current"],
                voltage=self.channel_config[ch]["voltage"],
                group=""
            )
            self.channel_dict.append(ch)

        self.raspi_io = RaspiIoDriver(config["input_channels"], config["gpio_config"])
        self.raspi_io.leak_detected_callback = self.leak_detected_callback
        self.svr_address = config["modbus_server_address"]
        self.svr_port = config["modbus_server_port"]
        self.loop = None
        self.mb_thread = None
        self.modbus_svr = ModBusServer(self.svr_address, self.svr_port)

        print("LTR Interface Modbus Server...")

    def start_server(self):
        self.loop = threading.Thread(target=self.run_thread)
        self.loop.isDaemon = True
        self.loop_delay = 1.0
        self.running = False
        self.loop.start()
        print("Started")

    def leak_detected_callback(self):
        self.modbus_svr.shutdown()

    def run_thread(self):
        time.sleep(1)
        self.running = True
        while self.running:
            if not self.modbus_svr.server_started:
                self.running = False
            else:
                self.update_inputs()
                self.run_commands()
                time.sleep(0.1)

    def update_inputs(self):
        #  get thermocouple inputs
        tc_list = ["tc1", "tc2", "tc3", "tc4", "tc5", "tc6", "tc7", "tc8"]
        tdata = [self.raspi_io.channels[tc].value for tc in tc_list]
        jdata = [self.raspi_io.channels[tc].value_ext for tc in tc_list]
        self.modbus_svr.update_ttv_temperature(tdata, jdata)

        tc_list = ["tc9", "tc10"]
        tdata = [self.raspi_io.channels[tc].value for tc in tc_list]
        jdata = [self.raspi_io.channels[tc].value_ext for tc in tc_list]
        self.modbus_svr.update_inlet_temperature(tdata, jdata)

        tc_list = ["outlet_t1", "outlet_t2"]
        tdata = [self.raspi_io.channels[tc].value for tc in tc_list]
        self.modbus_svr.update_outlet_temperature(tdata)

        tc_list = ["ttv_vi_1", "ttv_vi_2", "ttv_vi_3", "ttv_vi_4"]
        data = [self.raspi_io.channels[tc].value for tc in tc_list]
        self.modbus_svr.update_ttv_current(data)

        self.modbus_svr.update_system_current(self.raspi_io.channels["system_vi"].value)

        tc_list = ["ttv_vs_1", "ttv_vs_2", "ttv_vs_3", "ttv_vs_4"]
        data = [self.raspi_io.channels[tc].value for tc in tc_list]
        self.modbus_svr.update_voltage(data)

        #  update flags...

    def set_pwm(self, channel, pwm):
        ch = channel
        chname = self.channel_dict[ch]
        self.pwm.set_pwm(ch, pwm)
        self.channels[chname].set_pwm(pwm)

    def run_commands(self):
        while self.modbus_svr.command_q.not_empty:
            try:
                cmd = self.modbus_svr.command_q.get_nowait()   # type: ModBusServer.command_data
            except Exception as ex:
                pass

            if cmd.type == PWM_SET_CMD:
                if cmd.target == TTV_TARGET:
                    self.set_pwm(cmd.channel, cmd.value)
            elif cmd.type == OFF_CMD:
                if cmd.target == TTV_TARGET:
                    self.set_pwm(cmd.channel, 0)

svr = LtrServer()
svr.start_server()
#svr.run_thread()
