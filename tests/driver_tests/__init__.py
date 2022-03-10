import logging
from time import sleep

hardware_cfg = {
    "update_interval": 1,
    "devices": {
        "ttv_group": {
            "device_type": "pca9685",
            "config": {
                "ramp_up_dc_step": 2,
                "ramp_up_delay_seconds": 2,
                "frequency": 60,
                "i2c_addr": 68,
                "drivers": {
                    "ttv1": {
                        "channel": 0,
                        "offset": 0,
                        "resolution": 65535
                    },
                    "ttv2": {
                        "channel": 1,
                        "offset": 0,
                        "resolution": 65535
                    },
                    "ttv3": {
                        "channel": 2,
                        "offset": 0,
                        "resolution": 65535
                    },
                    "ttv4": {
                        "channel": 3,
                        "offset": 0,
                        "resolution": 65535
                    }

                }
            }
        },
        "fan_group": {
            "device_type": "pca9685",
            "config": {
                "ramp_up_dc_step": 0,
                "ramp_up_delay_seconds": 0,
                "frequency": 60,
                "i2c_addr": 68,
                "drivers": {
                    "fan1": {
                        "channel": 4,
                        "offset": 0,
                        "resolution": 65535
                    },
                    "fan2": {
                        "channel": 5,
                        "offset": 0,
                        "resolution": 65535
                    }

                }
            }
        }
    }
}


spi_cfg = {}


def test():
    log = logging.getLogger(__name__)

    try:
        from system_control import ControllerDeviceTypes
        from system_control.sensor_manager import SensorManager
        from devices.bus_manager import BusManager, BusType
        from devices.driver_manager import DriverManager
    except Exception as ex:
        # log.debug("Error during imports")
        log.error(ex)
        return False

    try:
        spi_mgr = BusManager(BusType.spi, ControllerDeviceTypes.raspi, **spi_cfg)
        i2c_mgr = BusManager(BusType.i2c, ControllerDeviceTypes.raspi, **spi_cfg)

        dm = DriverManager(spi_mgr, i2c_mgr, **hardware_cfg)
    except Exception as ex:
        # log.debug("Error during init")
        log.error(ex)
        return False

    try:
        log.info("Starting sensors manager...")
        dm.start_manager()
        sleep(5)
        dm.set_group('fan_group', 20)
        dm.set_group("ttv_group", 40)
        for _ in range(8):
            for dev_id in dm.device_data.keys():
                log.debug(f"{dev_id}:{dm.get_values(dev_id)}")
            sleep(1)
        dm.stop_manager()
        dm = None
    except Exception as ex:
        # log.debug("Error during interface")
        log.error(ex)
        if dm is not None:
            dm.stop_manager()
            dm = None
        return False
    return True
