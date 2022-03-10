import logging

from time import sleep

hardware_config = {
    "fan_group": ["fan1", "fan2"],
    "driver_group": ["ttv1", "ttv2", "ttv3", "ttv4"],
    "inlet_group": ["t9", "t10"],
    "outlet_group": ["t10", "t11"],
    "monitor_group": ["t1", "t2", "t3", "t4"],
    "monitor_threshold_temp": 70,
    "outlet_threshold_temp": 45,
    "inlet_threshold_temp": 45,
    "fan_table": [
            (45, 60),
            (44, 45),
            (42, 30),
            (40, 20),
    ],
    "default_fan_value": 70,
    "sample_size": 10,
    "fan_run_mode": "fan_table"
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
        from devices.driver_manager import DriverManager
        from system_control.thermal_management import ThermalManager
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
        driver_cfg = read_config("driver_config.json")
    except Exception as ex:
        log.debug("Error during config load")
        log.error(ex)
        return False

    try:
        spi_mgr = BusManager(BusType.spi, ControllerDeviceTypes.raspi, **spi_cfg)
        i2c_mgr = BusManager(BusType.i2c, ControllerDeviceTypes.raspi, **spi_cfg)

        dm = DriverManager(spi_mgr, i2c_mgr, **driver_cfg)
        dio = dio_loader(ControllerDeviceTypes.raspi, **dio_cfg)
        ch_sel = ChipSelector(dio, **ch_sel_cfg)

        adc = AdcManager(spi_mgr, i2c_mgr, ch_sel, **adc_cfg)
        thermo = ThermoManager(spi_mgr, i2c_mgr, ch_sel, **thermo_cfg)

        fans = fan_loader(FanDevType.fan_control_board, **fans_cfg)

        sm = SensorManager(spi_mgr, i2c_mgr, ch_sel, dio, adc, thermo, fans, **sensor_cfg)

        tm = ThermalManager(sm, dm, **hardware_config)

    except Exception as ex:
        log.debug("Error during init")
        log.error(ex)
        return False

    try:
        log.info("Starting managers")
        dm.start_manager()
        fans.start_updater()
        adc.start_manager()
        thermo.start_manager()
        sm.start_manager()
        tm.start_manager()
        sleep(5)
        log.info("reading sensors...")
        for _ in range(8):
            for dev_id in sm.sensor_data.keys():
                log.debug(f"{dev_id}: {sm.sensor_data[dev_id]}")
            sleep(1)

        dm.stop_manager()
        fans.stop_updater()
        adc.stop_manager()
        thermo.stop_manager()
        tm.stop_manager()
        sm.stop_manager()

        dm = None
        fans = None
        adc = None
        thermo = None
        tm = None
        sm = None
        log.info("Thermal Manager Test Complete")
    except Exception as ex:
        log.debug("Error during interface")
        log.error(ex)
        return False
    return True
