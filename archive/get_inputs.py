import time
from raspi_hardware import RaspiGPIO
import sys

cfg = {
        "mux_pins": [17, 22, 27,5],
        "strobe": 23,
        "report": 26,
        "input_pins": [6, 16]
    }

rp = RaspiGPIO(**cfg)

for p in cfg["input_pins"]:
    print(f"pin {p} - value:{rp.read_digital(p)}")

rp.shutdown()
