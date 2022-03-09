import time
from raspi_hardware import RaspiGPIO

cfg = {
        "mux_pins": [17, 27, 22, 5],
        "strobe": 23,
        "report": 26,
        "input_pins": [6, 16]
    }

rp = RaspiGPIO(**cfg)

chip = {
    10: "U600",
    11: "U601"
}

while(True):
    try:
        for cs in [10, 11]:
            for i in range(8):
                rp.chip_select(cs)
                v = rp.read_adc(i)
                print(f"{chip[cs]} ch[{i}] - Result:{v}")
                rp.chip_select(15)
    except KeyboardInterrupt:
        print("\nShutting down...")
        break
    time.sleep(0.5)


rp.shutdown()
