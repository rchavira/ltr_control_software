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
        "t1": {"device_type": "mcp960x", "i2c_addr": 96},
        "t2": {"device_type": "mcp960x", "i2c_addr": 97},
        "t3": {"device_type": "mcp960x", "i2c_addr": 98},
        "t4": {"device_type": "mcp960x", "i2c_addr": 99},
        "t5": {"device_type": "mcp960x", "i2c_addr": 100},
        "t6": {"device_type": "mcp960x", "i2c_addr": 101},
        "t7": {"device_type": "mcp960x", "i2c_addr": 102},
        "t8": {"device_type": "mcp960x", "i2c_addr": 103},
        "t9": {"device_type": "max31855", "cs": 9},
        "t10": {"device_type": "max31855", "cs": 8}
    }
}

spi = {}
i2c = {}


def hardware_test():
    log = logging.getLogger()
    from tests.dio_tests import hardware_cfg as dio_cfg
    from tests.chip_select_test import hardware_cfg as ch_sel_cfg

    try:
        from system_control import ControllerDeviceTypes
        from devices.bus_manager import BusManager, BusType
        from devices.chip_select import ChipSelector
        from devices.dio_devices import loader
        from devices.thermo_manager import ThermoManager

    except Exception as ex:
        # log.debug("Failure on imports")
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
        tm = ThermoManager(spi=spi_mgr, i2c=i2c_mgr, chip_sel=ch_sel, **hardware_cfg)
    except Exception as ex:
        # log.debug("Failure on init")
        log.error(ex)
        return False

    try:
        tm.start_manager()

        for _ in range(8):
            for dev_id in tm.device_data.keys():
                log.info(f"{dev_id}:{tm.get_values(dev_id)}")
            sleep(1)

        tm.stop_manager()
        tm = None
    except Exception as ex:
        # log.debug("Failure on interface usage")
        log.error(ex)
        return False
    return True
