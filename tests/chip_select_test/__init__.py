import logging
from time import sleep


test_config = {
    "dio": {
        "input_pins": [1,2,3,4],
        "output_pins": [10,24,35]
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
    }
}


hardware_cfg = {
    "device_type": "cd451x",
    "cs_reset": 15,
    "config": {
        "pinA": 17,
        "pinB": 27,
        "pinC": 22,
        "pinD": 5,
        "strobe": 23,
        "strobe_delay": 0.5
    }
}


def test():
    from system_control import ControllerDeviceTypes

    from devices.dio_devices.emulated import EmulatedIO
    from devices.chip_select import ChipSelector

    dio = EmulatedIO(**test_config["dio"])
    cs = ChipSelector(dio, **test_config["chip_select"])

    cs.chip_select(10)
    sleep(2)
    cs.cs_reset()


def hardware_test():
    log = logging.getLogger(__name__)
    from tests.dio_tests import hardware_cfg as dio_cfg
    try:
        from system_control import ControllerDeviceTypes
        from devices.dio_devices import loader as dio_loader
        from devices.chip_select import ChipSelector
    except Exception as ex:
        log.info("Failure on import")
        log.error(ex)
        return False

    try:
        dio = dio_loader(ControllerDeviceTypes.raspi, **dio_cfg)
        ch = ChipSelector(dio, **hardware_cfg)
    except Exception as ex:
        log.info("Failure on init")
        log.error(ex)
        return False

    try:
        ch.chip_select(1)
        sleep(1)
        ch.reset()
    except Exception as ex:
        log.info("Failure on interface usage")
        log.error(ex)
        return False
    return True
