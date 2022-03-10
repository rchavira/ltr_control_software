import logging

from threading import Thread
from time import time, sleep

from config import check_path, read_config

from system_control import ControllerDeviceTypes
from system_control.sensor_manager import SensorManager
from devices.bus_manager import BusManager, BusType
from devices.chip_select import ChipSelector
from devices.dio_devices import DioInterface, loader as dio_loader
from devices.adc_manager import AdcManager
from devices.thermo_manager import ThermoManager
from devices.fan_controller_devices import FanSpeedInterface, FanDevType, loader as fan_loader
from devices.driver_manager import DriverManager
from system_control.thermal_management import ThermalManager
from system_control.modbus_server import ModbusServer

log = logging.getLogger(__name__)


class SystemManager(object):
    spi: BusManager
    i2c: BusManager
    dm: DriverManager
    dio: DioInterface
    ch_sel: ChipSelector
    adc: AdcManager
    thermo: ThermoManager
    fans: FanSpeedInterface
    sm: SensorManager
    tm: ThermalManager
    mb: ModbusServer
    main_thread: Thread

    def __init__(self, config_file_name):
        self.adc = None
        self.spi = None
        self.i2c = None
        self.dm = None
        self.ch_sel = None
        self.fans = None
        self.thermo = None
        self.sm = None
        self.tm = None
        self.mb = None
        self.cfg = read_config(config_file_name)

        self.main_thread = None
        self.running = False

        self.power_on_target = self.cfg["power_on_target"]
        self.max_power_target = self.cfg["max_power_target"]

        ctype = ControllerDeviceTypes[self.cfg['controller_type']]

        cfg = read_config(self.cfg['spi_config'])
        self.spi = BusManager(BusType.spi, ctype, **cfg)

        cfg = read_config(self.cfg['i2c_config'])
        self.i2c = BusManager(BusType.i2c, ctype, **cfg)

        cfg = read_config(self.cfg['driver_config'])
        self.dm = DriverManager(self.spi, self.i2c, **cfg)

        cfg = read_config(self.cfg['dio_config'])
        self.dio = dio_loader(ctype, **cfg)

        cfg = read_config(self.cfg['chip_select_config'])
        self.ch_sel = ChipSelector(self.dio, **cfg)

        cfg = read_config(self.cfg['adc_config'])
        self.adc = AdcManager(self.spi, self.i2c, self.ch_sel, **cfg)

        cfg = read_config(self.cfg['thermocouple_config'])
        self.thermo = ThermoManager(self.spi, self.i2c, self.ch_sel, **cfg)

        cfg = read_config(self.cfg['fan_speed_device_config'])
        ftype = FanDevType[self.cfg['fan_dev_type']]
        self.fans = fan_loader(ftype, **cfg)

        cfg = read_config(self.cfg['sensor_manager'])
        self.sm = SensorManager(self.spi, self.i2c, self.ch_sel, self.dio, self.adc, self.thermo, self.fans, **cfg)

        cfg = read_config(self.cfg['thermal_manager'])
        self.tm = ThermalManager(self.sm, self.dm, **cfg)

        cfg = read_config(self.cfg['modbus_config'])
        self.mb = ModbusServer(**cfg)

    def start_system(self):
        self.mb.start_server()
        self.mb.set_info_registers()

        self.dm.start_manager()

        self.thermo.start_manager()

        self.adc.start_manager()

        self.fans.start_updater()
        self.sm.start_manager()
        self.tm.start_manager()

        self.main_thread = Thread(target=self.main)
        self.main_thread.isDaemon = True
        self.running = True
        self.main_thread.start()

    def stop_system(self):
        self.running = False
        self.mb.stop_server()
        self.tm.stop_manager()
        self.sm.stop_manager()
        self.fans.stop_updater()
        self.thermo.stop_manager()
        self.adc.stop_manager()
        self.dm.stop_manager()
        if self.main_thread is not None:
            self.main_thread.join(2)

    def main(self):
        pt_dc = 0
        power_target = self.power_on_target
        run_ttv = 1 if power_target > 0 else 0
        shutdown = 0
        log.debug(f"PT:{power_target} Run:{run_ttv}")
        self.mb.set_power_target(power_target)
        self.mb.set_run_status(run_ttv)

        while self.running:
            power_target = self.mb.get_power_target()
            run_ttv = self.mb.get_run_status()
            shutdown = self.mb.get_shutdown_cmd()

            if shutdown != 0:
                self.stop_system()
                break

            # convert power target to dc %
            pt_dc = int((power_target / self.max_power_target) * 100)
            # log.debug(f"PT:{power_target} DC:{pt_dc} Run:{run_ttv}")
            if run_ttv > 0:
                for dev_id in self.tm.driver_group:
                    # log.debug(f"{dev_id}: {pt_dc}")
                    self.dm.set_output(dev_id, pt_dc)
            else:
                for dev_id in self.tm.driver_group:
                    self.dm.set_output(dev_id, 0)

            self.mb.update_sensor_info(self.sm.sensor_data)

            self.mb.update_temp_registers(self.tm.monitor_temp, self.tm.inlet_temp, self.tm.outlet_temp)

            current_power_dc = self.dm.device_data[self.tm.driver_group[0]].current_dc
            time_at_power = time() - self.dm.device_data[self.tm.driver_group[0]].current_dc_time_stamp
            current_power = (current_power_dc/100) * self.max_power_target

            self.mb.update_system_flags(
                running=(run_ttv == 1),
                system_stop=(shutdown != 0),
                leak_detect=self.sm.leak_flag,
                thermal_fault=self.tm.thermal_flag,
                sensor_fault=self.sm.sensor_flag,
                current_power=current_power,
                on_time=time_at_power
            )

            ddict = {}
            for dev_id in self.tm.driver_group:
                ddict[dev_id] = self.dm.device_data[dev_id].current_dc

            for dev_id in self.tm.fan_group:
                ddict[dev_id] = self.dm.device_data[dev_id].current_dc

            self.mb.update_driver_states(ddict)
            sleep(0.5)

