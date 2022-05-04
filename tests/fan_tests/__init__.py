import logging

from time import sleep


hardware_cfg = {
    "port": "/dev/ttyUSB0",
    "baudrate": 115200,
    "timeout": 0.5,
    "channel_count": 8
}

spi_cfg = {}


def test():
    log = logging.getLogger(__name__)

    try:
        from system_control import ControllerDeviceTypes
        from devices.fan_controller_devices import FanDevType, loader as fan_loader
        from system_control import ControllerDeviceTypes
        from system_control.sensor_manager import SensorManager
        from devices.bus_manager import BusManager, BusType
        from devices.driver_manager import DriverManager
    except Exception as ex:
        # log.debug("Error during imports")
        log.error(ex)
        return False

    try:
        fans = fan_loader(FanDevType.fan_control_board, **hardware_cfg)

        spi_mgr = BusManager(BusType.spi, ControllerDeviceTypes.raspi, **spi_cfg)
        i2c_mgr = BusManager(BusType.i2c, ControllerDeviceTypes.raspi, **spi_cfg)

        dm = DriverManager(spi_mgr, i2c_mgr, **hardware_cfg)
    except Exception as ex:
        # log.debug("Error during init")
        log.error(ex)
        return False

    try:
        log.info("Starting driver manager...")
        dm.start_manager()

        sleep(2)

        log.info("Starting fan monitor...")

        fans.start_updater()
        sleep(2)
        for fan_dc in range(10):
            dm.set_group('fan_group', fan_dc * 10)
            for i in range(8):
                log.debug(f"{i}: {fans.channels[i]}")
            log.debug(f"{fans.temperature}")
            sleep(5)
        fans.stop_updater()
        dm.set_group('fan_group', 0)
        dm.stop_manager()
        fans = None
    except Exception as ex:
        # log.debug("Error during interface")
        log.error(ex)
        if dm is not None:
            dm.stop_manager()
            dm = None

        return False
    return True
