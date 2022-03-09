import time
import adafruit_max31855
from raspi_hardware import RaspiGPIO
from digitalio import DigitalInOut
import board
import sys

spi = board.SPI()
cs = DigitalInOut(board.D4)

cfg = {
        "mux_pins": [17, 27, 22,5],
        "strobe": 23,
        "report": 26,
        "input_pins": [6, 16]
    }
rp = RaspiGPIO(**cfg)

sensor = adafruit_max31855.MAX31855(spi, cs)

#chip select
rp.set_digital(23, 0)

if len(sys.argv) == 2:
    cs = int(sys.argv[1])
else:
    cs = 0

while(True):
    try:
        if cs > 9:
            cs = 0
        if cs in [8, 9]:
            for _ in range(1):
                # input('Press Enter')
                # chip_select(15)
                rp.chip_select(cs)

                tmp = sensor.temperature
                rtmp = sensor.reference_temperature
                ntmp = sensor.temperature_NIST
                print(f"T{(cs+1)}: {tmp} C") #  - ref Temp: {rtmp} C  *** NIST: {ntmp}")

                # chip_select(11)
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nShutting down...")
        break
    except Exception as ex:
        print(f"T{(cs+1)}: {ex}")
    cs += 1


rp.shutdown()
