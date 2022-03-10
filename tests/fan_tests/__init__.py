import logging

from time import sleep


hardware_cfg = {
    "port": "/dev/ttyUSB0",
    "baudrate": 115200,
    "timeout": 0.5,
    "channel_count": 8
}


def test():
    log = logging.getLogger(__name__)

    try:
        from system_control import ControllerDeviceTypes
        from devices.fan_controller_devices import FanDevType, loader as fan_loader
    except Exception as ex:
        # log.debug("Error during imports")
        log.error(ex)
        return False

    try:
        fans = fan_loader(FanDevType.fan_control_board, **hardware_cfg)
    except Exception as ex:
        # log.debug("Error during init")
        log.error(ex)
        return False

    try:
        log.info("Starting sensors manager...")
        fans.start_updater()
        sleep(2)
        for _ in range(10):
            for i in range(8):
                log.debug(f"{i}: {fans.channels[i]}")
            log.debug(f"{fans.temperature}")
            sleep(5)
        fans.stop_updater()
        fans = None
    except Exception as ex:
        # log.debug("Error during interface")
        log.error(ex)
        return False
    return True
