import sys
from driver_hardware import DriverHardware


if len(sys.argv) == 2:
    cfg = {
        "driver_config": {
            "device_address": 64,
            "device_frequency": 60
        },
    }

    drv = DriverHardware(**cfg)

    try:
        dc = int(sys.argv[1])
        with open("./fan_state", "w") as outfile:
            outfile.write(f"{dc}")

        if dc >=0 and dc <=100:
            drv.set_duty_cycle(4, dc)
            drv.set_duty_cycle(5, dc)
        else:
            print(f"Invalid range, must be between 0-100. {dc}")

    except Exception as ex:
        print(f"{ex}")
elif len(sys.argv) == 1:
    with open("./fan_state") as infile:
        dc = infile.read()
        print(f"Last set value={dc}")
