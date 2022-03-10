import logging
from time import sleep


test_config = {
    "dio": {
        "input_pins": [1,2,3,4],
        "output_pins": [10,24,35]
    }
}

hardware_cfg = {
    "input_pins": [6, 16],
    "output_pins": [5, 17, 22, 23, 26, 27]
}


def test():
    from system_control import ControllerDeviceTypes

    from devices.dio_devices.emulated import EmulatedIO

    dio = EmulatedIO(**test_config["dio"])


def hardware_test():
    log = logging.Logger(__name__, level=logging.DEBUG)
    log.info("Starting DIO hardware test...")
    result = True
    try:
        from devices.dio_devices import loader
        from system_control import ControllerDeviceTypes
    except Exception as ex:
        # log.debug("Failure on imports")
        log.error(ex)
        result = False
        return result

    try:
        dio = loader(ControllerDeviceTypes.raspi, **hardware_cfg)
    except Exception as ex:
        # log.debug("Failure on dio init")
        log.error(ex)
        result = False
        return result

    try:
        for p in dio.output_pins:
            if dio.read_digital(p):
                dio.write_digital(p, False)
            else:
                dio.write_digital(p, True)
            sleep(0.1)
        for p in dio.input_pins:
            v = dio.read_digital(p)
            log.info(f"Pin {p}: {v}")
            sleep(0.5)
    except Exception as ex:
        # log.debug("Failure on interface usage")
        log.error(ex)
        result = False
        return result
    return result

