import logging

from time import sleep

test_config = {
    "adc_manager": {
        "update_interval": 1,
        "devices": {
            "adc1": {
                "device_type": "emulated",
                "chip_select": 11,
                "input_file": "test.txt",
                "resolution": 1024,
                "devices": {
                    "leak_1": {"channel": 3, "min_val": 0, "max_val": 1024}
                }
            }
        }
    },
    "dio": {
        "input_pins": [6, 16],
        "output_pins": [5, 17, 22, 23, 26, 27]
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
    "spi": {
        "input_file": "spi_stdin.txt",
        "output_file": "spi_stdout.txt"
    }
}

hardware_cfg = {
    "update_interval": 1,
    "devices": {
        "adc1": {
            "device_type": "max1168",
            "chip_select": 10,
            "devices": {
                "i1": {"channel": 0, "min_val": 0, "max_val": 25},
                "i2": {"channel": 1, "min_val": 0, "max_val": 25},
                "i3": {"channel": 2, "min_val": 0, "max_val": 25},
                "i4": {"channel": 3, "min_val": 0, "max_val": 25},
                "v1": {"channel": 4, "min_val": 0, "max_val": 60},
                "v2": {"channel": 5, "min_val": 0, "max_val": 60},
                "v3": {"channel": 6, "min_val": 0, "max_val": 60},
                "v4": {"channel": 7, "min_val": 0, "max_val": 60}
            }
        },
        "adc2": {
            "device_type": "max1168",
            "chip_select": 11,
            "devices": {
                "t11": {"channel": 0, "min_val": 0, "max_val": 150},
                "t12": {"channel": 1, "min_val": 0, "max_val": 150},
                "a1": {"channel": 2, "min_val": 0, "max_val": 1024},
                "l1": {"channel": 3, "min_val": 0, "max_val": 65535},
                "t13": {"channel": 4, "min_val": 0, "max_val": 150},
                "t14": {"channel": 5, "min_val": 0, "max_val": 150},
                "i5": {"channel": 6, "min_val": 0, "max_val": 2000}
            }
        }
    }
}

spi_cfg = {
    "input_file": "spi_stdin.txt",
    "output_file": "spi_stdout.txt"
}


def test():
    from system_control import ControllerDeviceTypes
    from devices.bus_manager import BusManager, BusType
    from devices.dio_devices.emulated import EmulatedIO
    from devices.chip_select import ChipSelector
    from devices.adc_manager import AdcManager

    dio = EmulatedIO(**test_config["dio"])
    cs = ChipSelector(dio, **test_config["chip_select"])
    cfg = test_config["spi"]
    spi_mgr = BusManager(BusType.spi, ControllerDeviceTypes.emulated, **cfg)
    i2c_mgr = BusManager(BusType.i2c, ControllerDeviceTypes.emulated, **cfg)
    am = AdcManager(
        spi=spi_mgr, i2c=i2c_mgr, ch_sel=cs, **test_config["adc_manager"]
    )

    am.start_manager()

    sleep(5)
    for dev_id in am.data.keys():
        print(f"{am.get_values(dev_id)}")

    am.stop_manager()

    am = None


def hardware_test():
    log = logging.getLogger(__name__)
    from tests.dio_tests import hardware_cfg as dio_cfg
    from tests.chip_select_test import hardware_cfg as ch_sel_cfg
    try:
        from system_control import ControllerDeviceTypes
        from devices.bus_manager import BusManager, BusType
        from devices.dio_devices import DioInterface, loader as dio_loader
        from devices.chip_select import ChipSelector
        from devices.adc_manager import AdcManager
    except Exception as ex:
        log.info("Failure on import")
        log.error(ex)
        return False

    try:
        log.info("Initializing Hardware")
        dio = dio_loader(ControllerDeviceTypes.raspi, dio_cfg)
        cs = ChipSelector(dio, **ch_sel_cfg)

        cfg = spi_cfg

        spi_mgr = BusManager(BusType.spi, ControllerDeviceTypes.raspi, **cfg)
        i2c_mgr = BusManager(BusType.i2c, ControllerDeviceTypes.emulated, **cfg)

        am = AdcManager(spi=spi_mgr, i2c=i2c_mgr, ch_sel=cs, **hardware_cfg)
    except Exception as ex:
        log.info("Failure on init")
        log.error(ex)
        return False

    log.info("Starting update loop")
    try:
        am.start_manager()

        for _ in range(8):
            for dev_id in am.data.keys():
                log.debug(f"{am.get_values(dev_id)}")
            sleep(1)

        log.info("Stopping adc manager...")
        am.stop_manager()

        am = None
        log.info("done.")
    except Exception as ex:
        log.info("Failure on interface usage")
        log.error(ex)
        return False
    return True
