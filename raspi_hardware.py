import logging
import time

import struct
import RPi.GPIO as GPIO
import busio
from board
import adafruit_max31855
# from adafruit_mcp9600 import MCP9600
import mcp9600

from raspi_interface import RaspiInterface
from digitalio import DigitalInOut
from adafruit_bus_device.spi_device import SPIDevice

log = logging.getLogger(__name__)


class RaspiGPIO(RaspiInterface):
    def __init__(self, **kwargs):
        self.bus = 0
        self.device = 0
        # self.spi = spidev.SpiDev()
        # self.spi = SPI.SpiDev(self.bus, self.device)
        # self.thermo = MAX31855.MAX31855(spi=self.spi)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        for p in kwargs["mux_pins"]:
            GPIO.setup(p, GPIO.OUT)
        GPIO.setup(kwargs["strobe"], GPIO.OUT)
        GPIO.setup(kwargs["report"], GPIO.OUT)

        for p in kwargs["input_pins"]:
            GPIO.setup(p, GPIO.IN)

        super().__init__(**kwargs)

        self.thermo_scale = 1 #41.276 / 52.18
        self.thermo_offset = 0

        self.spi = board.SPI()
        self.cs = DigitalInOut(board.D4)

        self.set_digital(23, 0)

        self.thermo_device = None
        self.adc_device = None

        self.thermo_flag = False

        # self.i2c = busio.I2C(board.SCL, board.SDA)

    def shutdown(self):
        #self.spi.close()
        GPIO.cleanup()

    def chip_select(self, channel):
        # TODO: work on making this abstract instead of hard coded.
        # A  B  C  D
        # 17 27 22 5
        dA = dB = dC = dD = 0

        if channel == 0: # S3 U700
            dA = dB = 1
        elif channel == 1: # S7 U701
            dA = dB = dC = 1
        elif channel == 2: # S1 U702
            dA = 1
        elif channel == 3: # S6 U703
            dB = dC = 1
        elif channel == 4: # S2 U704
            dB == 1
        elif channel == 5: # S5 U705
            dA = dC = 1
        elif channel == 6: # S0 U706
            pass
        elif channel == 7: # S4 U707
            dC = 1
        elif channel == 8: # S9 U708
            dA = dD = 1
        elif channel == 9: # S8 U709
            dD = 1
        elif channel == 10: # S10 U600
            dB = dD = 1
        elif channel == 11: # S11 U601
            dA = dB = dD = 1
        elif channel == 15:
            dA = dB = dC = dD = 1

        self.set_digital(23, 1)  #strobe HIGH
        time.sleep(0.5)

        self.set_digital(17, dA)  # A
        self.set_digital(27, dB)  # B
        self.set_digital(22, dC)  # C
        self.set_digital(5, dD)   # D

        self.set_digital(23, 0) # strobe LOW
        time.sleep(0.5)

    def read_thermo(self, t_type):
        result = 0
        if t_type == "MCP9600":
            result = self.read_thermo_mcp9600()
        elif t_type == "MAX31855":
            result = self.read_thermo_max31855()

        result = (result * self.thermo_scale) + self.thermo_offset
        return result

    def read_thermo_mcp9600(self):
        result = 0
        self.thermo_flag = False
        try:
            self.thermo_device = mcp9600.MCP9600()
            result = (self.thermo_device.get_hot_junction_temperature())
            self.thermo_device = None
        except Exception as ex:
            log.error(ex)
            self.thermo_flag = True
        return result

    def read_thermo_max31855(self):
        result = 0
        self.thermo_flag = False
        try:
            self.thermo_device = adafruit_max31855.MAX31855(self.spi, self.cs)
            result = self.thermo_device.temperature
            self.thermo_device = None
        except Exception as ex:
            log.error(ex)
            self.thermo_flag = True
        return result


    def read_adc(self, channel):
        """
        bits 5-7 are channel select
        bits 3,4 are scan mode
        bits 1,2 are reference mode
        bit 0 is clock mode
        """
        with SPIDevice(self.spi, self.cs) as spi: #, baudrate=4800000)

            value = 0

            #if self.adc_device is not None:

            ch = (int(channel) << 5 | 3 << 3)
            cmd = struct.pack("<H", ch)
            #cmd = bytearray([0,(int(channel) << 5 | 3 << 3)])
            spi.write(cmd)
            time.sleep(0.5)

            raw = bytearray(3)

            spi.readinto(raw)

            value, _ = struct.unpack("<HB", raw)

        return value

    def read_digital(self, pin):
        return GPIO.input(pin)

    def set_digital(self, pin, value):
        GPIO.output(pin, value)
