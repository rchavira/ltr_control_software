import sys
from driver_hardware import DriverHardware

cfg = {
    "driver_config": {
        "device_address": 64,
        "device_frequency": 60
    },
}

drv = DriverHardware(**cfg)

if len(sys.argv) == 2:
    try:
        dc = int(sys.argv[1])
        with open("./ttv_state", "w") as outfile:
            outfile.write(f"{dc}")

        if dc >=0 and dc <=100:
            drv.set_duty_cycle(0, dc)
            drv.set_duty_cycle(1, dc)
            drv.set_duty_cycle(2, dc)
            drv.set_duty_cycle(3, dc)
        else:
            print(f"Invalid range, must be between 0-100. {dc}")
    except Exception as ex:
        print(f"{ex}")
elif len(sys.argv) == 3:
    try:
        dc = int(sys.argv[1])
        ch = int(sys.argv[2])
        with open("./ttv_state", "w") as outfile:
            outfile.write(f"{dc}")

        if dc >=0 and dc <=100:
            drv.set_duty_cycle(ch, dc)

        else:
            print(f"Invalid range, must be between 0-100. {dc}")
    except Exception as ex:
        print(f"{ex}")
elif len(sys.argv) == 1:
    with open("./ttv_state") as infile:
        dc = infile.read()
        print(f"Last set value={dc}")
