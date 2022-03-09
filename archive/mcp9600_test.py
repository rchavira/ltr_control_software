import time
import mcp9600
from raspi_hardware import RaspiGPIO
from digitalio import DigitalInOut
import board
import sys

spi = board.SPI()

cfg = {
        "mux_pins": [17, 27, 22,5],
        "strobe": 23,
        "report": 26,
        "input_pins": [6, 16]
    }
rp = RaspiGPIO(**cfg)

max_t_count = 8
base_addr = 0x60

if len(sys.argv) == 2:
    max_t_count = int(sys.argv[1])
else:
    cs = 0

while(True):
    try:
        for i in range(max_t_count):
            rp.read_thermo_mcp9600(address=(base_addr + i))
            print(f"T{(i+1)}: {tmp} C")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nShutting down...")
        break
    except Exception as ex:
        print(f"T{(cs+1)}: {ex}")

rp.shutdown()
