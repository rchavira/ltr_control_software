import logging
from time import sleep

test_config = {
    "thermo_manager": {
        "update_interval": 1,
        "temp_decimals": 2,
        "devices": {
            "t1": {
                "device_type": "emulated",
                "config": {
                    "junction_values_file": "test.txt",
                    "internal_values_file": "test2.txt",
                    "flag_values_file": "test3.txt"
                }
            },
            "t2": {
                "device_type": "emulated",
                "config": {
                    "junction_values_file": "test.txt",
                    "internal_values_file": "test2.txt",
                    "flag_values_file": "test3.txt"
                }
            }
        }
    },
    "chip_select": {
        "device_type": "emulated",
        "cs_reset": 15,
        "config": {
            "pinA": 17,
            "pinB": 27,
            "pinC": 22,
            "pinD": 5,
            "strobe": 23,
            "strobe_delay": 0.5
        }
    },
    "dio": {
        "input_pins": [1,2,3,4],
        "output_pins": [10,24,35]
    },
}

hardware_cfg = {
    "update_interval": 0.1,
    "temp_decimals": 2,
    "devices": {
        "t9": {"device_type": "max31855", "cs": 9},
        "t10": {"device_type": "max31855", "cs": 8}
    }
}

spi = {}
i2c = {}


def hardware_test():
    log = logging.getLogger()

    from config import read_config

    from tests.dio_tests import hardware_cfg as dio_cfg
    from tests.chip_select_test import hardware_cfg as ch_sel_cfg

    try:
        from system_control import ControllerDeviceTypes
        from devices.bus_manager import BusManager, BusType
        from devices.chip_select import ChipSelector
        from devices.dio_devices import loader
        from devices.thermo_manager import ThermoManager

    except Exception as ex:
        log.debug("Failure on imports")
        log.error(ex)
        return False

    try:
        dio_cfg = read_config("dio_config.json")
        ch_sel_config = read_config("chip_select_config.json")
        thermo_config = read_config("thermocouple_config.json")
        thermo_config = hardware_cfg
    except Exception as ex:
        log.debug("Failure on loading config")
        log.error(ex)
        return False


    try:
        i2c_mgr = BusManager(BusType.i2c, ControllerDeviceTypes.raspi, **i2c)
        spi_mgr = BusManager(BusType.spi, ControllerDeviceTypes.raspi, **spi)
        dio = loader(ControllerDeviceTypes.raspi, **dio_cfg)
        ch_sel = ChipSelector(dio, **ch_sel_cfg)
    except Exception as ex:
        # log.debug("Failure on dependancy init")
        log.error(ex)
        return False

    try:
        tm = ThermoManager(spi=spi_mgr, i2c=i2c_mgr, chip_sel=ch_sel, **thermo_config)
    except Exception as ex:
        # log.debug("Failure on init")
        log.error(ex)
        return False

    try:
        tm.start_manager()

        while True:
            for dev_id in tm.device_data.keys():
                log.debug(f"{dev_id}:{tm.get_values(dev_id)}")
            try:
                sleep(1)
            except KeyboardInterrupt:
                break

        tm.stop_manager()
        tm = None
    except Exception as ex:
        # log.debug("Failure on interface usage")
        log.error(ex)
        return False
    return True
