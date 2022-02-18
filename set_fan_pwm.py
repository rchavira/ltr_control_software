from driver_hardware import DriverHardware

cfg = {
	"driver_config": {
        "device_address": 64,
        "device_frequency": 60
    },
}

drv = DriverHardware(**cfg)

dc = 0

def set_fans(dc):
	drv.set_duty_cycle(4, dc)
	drv.set_duty_cycle(5, dc)

set_fans(dc)

while(True):
   inp = input("Fan DC %:")
   dc = int(inp)
   set_fans(dc)

