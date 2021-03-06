import logging

from time import sleep

hardware_config = {
    "fan_speed_device_type": "fan_control_board",
    "internal_leak_dev_id": "leak_1",
    "leak_detection_mode": "delta",
    "leak_detection_value": 100,
    "external_leak_pin": 1,
    "leak_report_out_pin": 2,
    "leak_report_active": 0,
    "leak_report_inactive": 1,
    "leak_sample_rate": 10
}

spi_cfg = {}


def test():
    log = logging.getLogger(__name__)

    from config import read_config

    try:
        from system_control import ControllerDeviceTypes
        from system_control.sensor_manager import SensorManager
        from devices.bus_manager import BusManager, BusType
        from devices.chip_select import ChipSelector
        from devices.dio_devices import loader as dio_loader
        from devices.adc_manager import AdcManager
        from devices.thermo_manager import ThermoManager
        from devices.fan_controller_devices import FanDevType, loader as fan_loader
    except Exception as ex:
        log.debug("Error during imports")
        log.error(ex)
        return False

    try:
        adc_cfg = read_config("adc_config.json")
        dio_cfg = read_config("dio_config.json")
        ch_sel_cfg = read_config("chip_select_config.json")
        thermo_cfg = read_config("thermocouple_emulate.json")
        fans_cfg = read_config("fan_speed_device_config.json")
        sensor_cfg = read_config("sensor_manager.json")
    except Exception as ex:
        log.debug("Error during config load")
        log.error(ex)
        return False


    try:
        spi_mgr = BusManager(BusType.spi, ControllerDeviceTypes.raspi, **spi_cfg)
        i2c_mgr = BusManager(BusType.i2c, ControllerDeviceTypes.raspi, **spi_cfg)

        dio = dio_loader(ControllerDeviceTypes.raspi, **dio_cfg)
        ch_sel = ChipSelector(dio, **ch_sel_cfg)

        adc = AdcManager(spi_mgr, i2c_mgr, ch_sel, **adc_cfg)
        thermo = ThermoManager(spi_mgr, i2c_mgr, ch_sel, **thermo_cfg)

        fans = fan_loader(FanDevType.fan_control_board, **fans_cfg)

        sm = SensorManager(spi_mgr, i2c_mgr, ch_sel, dio, adc, thermo, fans, **sensor_cfg)
    except Exception as ex:
        # log.debug("Error during init")
        log.error(ex)
        return False

    try:
        fans.start_updater()
        adc.start_manager()
        thermo.start_manager()
        log.info("Starting sensors manager...")
        sm.start_manager()
        sleep(5)
        log.info("reading sensors...")
        for _ in range(8):
            # for dev_id in sm.sensor_data.keys():
            #     log.debug(f"{dev_id}: {sm.sensor_data[dev_id]}")
            sleep(5)

        sm.stop_manager()
        sm = None
    except Exception as ex:
        # log.debug("Error during interface")
        log.error(ex)
        return False
    return True
