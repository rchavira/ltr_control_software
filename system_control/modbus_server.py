import logging
import threading
import time

from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.asynchronous import StartTcpServer, StopServer

#  pymodbus imports
from pymodbus.version import version

log = logging.getLogger(__name__)
logging.getLogger("pymodbus").setLevel(logging.WARNING)


class ModbusServer(object):
    def __init__(self, **kwargs):
        self.modbus_config = kwargs
        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(
                0, [0] * int(self.modbus_config["max_registers"]["di"])
            ),
            co=ModbusSequentialDataBlock(
                0, [0] * int(self.modbus_config["max_registers"]["co"])
            ),
            hr=ModbusSequentialDataBlock(
                0, [0] * int(self.modbus_config["max_registers"]["hr"])
            ),
            ir=ModbusSequentialDataBlock(
                0, [0] * int(self.modbus_config["max_registers"]["ir"])
            ),
        )
        self.context = ModbusServerContext(slaves=store, single=True)

        self.modbus_loop = None  # type: threading.Thread
        self.server_started = False

        self.run_reg = self.modbus_config["control_registers"]["run"]
        self.shutdown_reg = self.modbus_config["control_registers"]["shutdown"]
        self.power_reg = self.modbus_config["control_registers"]["power"]

        self.running_reg = self.modbus_config["system_registers"]["running_ttv"]
        self.system_stop_reg = self.modbus_config["system_registers"]["system_stop"]
        self.leak_detected_reg = self.modbus_config["system_registers"]["leak_detected"]
        self.thermal_fault_reg = self.modbus_config["system_registers"]["thermal_fault"]
        self.sensor_fault_reg = self.modbus_config["system_registers"]["sensor_fault"]
        self.driver_state_register = self.modbus_config["system_registers"][
            "driver_state_register"
        ]
        self.current_power_register = self.modbus_config["system_registers"][
            "current_power"
        ]
        self.run_time_register = self.modbus_config["system_registers"]["run_time"]

        self.info_registers = self.modbus_config["info_registers"]
        self.sensor_info = kwargs["sensor_registers"]
        self.version_register = self.info_registers["version"]
        self.monitor_temp = self.info_registers["monitor_temp"]
        self.inlet_temp = self.info_registers["inlet_temp"]
        self.outlet_temp = self.info_registers["outlet_temp"]

        self.version = 4

        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = "Meta"
        self.identity.ProductCode = "A404 LTR"
        self.identity.VendorUrl = "https://github.com/rchavira/ltr_control_software"
        self.identity.ProductName = "LTR Controller"
        self.identity.ModelName = "Pymodbus Server"
        self.identity.MajorMinorRevision = version.short()

        # self.context[0].setValues(1, 19, [b])  #  Input coil
        # self.context[0].setValues(2, 19, [0])  #  output coil
        # self.context[0].setValues(3, 19, [b])  #  holding register
        # self.context[0].setValues(4, 19, [0])  #  input register

    def start_server(self):
        log.info("Starting modbus server")
        self.modbus_loop = threading.Thread(target=self.modbus_thread)
        self.modbus_loop.isDaemon = True
        self.modbus_loop.start()
        time.sleep(1)
        log.info("Modbus Server Started")

    def stop_server(self):
        log.info("Stopping modbus server...")
        StopServer()
        if self.modbus_loop is not None:
            self.modbus_loop.join(2)
        self.modbus_loop = None
        log.info("modbus server Stopped")

    def modbus_thread(self):
        self.server_started = True
        try:
            StartTcpServer(self.context, identity=self.identity)
        except Exception as ex:
            log.error(f"{ex}")
            self.server_started = False

    def get_shutdown_cmd(self):
        values = self.context[0].getValues(3, self.shutdown_reg, count=1)
        return values[0]

    def get_run_status(self):
        values = self.context[0].getValues(3, self.run_reg, count=1)
        return values[0]

    def set_run_status(self, rs):
        self.update_holding_register(self.run_reg, [rs])

    def get_power_target(self):
        values = self.context[0].getValues(3, self.power_reg, count=1)
        return values[0]

    def set_power_target(self, pt):
        self.update_holding_register(self.power_reg, [pt])

    def update_sensor_info(self, sdict):
        for si in sdict.keys():
            try:
                v = float(sdict[si])
                dec_p = int(
                    self.modbus_config["sensor_registers"][si]["decimal_places"]
                )

                value = int(v * (10 ** dec_p))
                if value > (2**16) - 1:
                    value = (2**16) - 1
                self.update_input_register(
                    self.modbus_config["sensor_registers"][si]["address"], [value]
                )
            except Exception as ex:
                log.error(f"{si}: {sdict[si]} - {ex}")

    def update_temp_registers(self, monitor, inlet, outlet):
        self.update_input_register(self.monitor_temp, [int(monitor * 100)])
        self.update_input_register(self.inlet_temp, [int(inlet * 100)])
        self.update_input_register(self.outlet_temp, [int(outlet * 100)])

    def update_input_register(self, addr, values):
        self.context[0].setValues(4, addr, values)

    def update_holding_register(self, addr, values):
        self.context[0].setValues(3, addr, values)

    def update_system_flags(
        self,
        running,
        system_stop,
        leak_detect,
        thermal_fault,
        sensor_fault,
        current_power,
        on_time,
    ):
        self.set_flag(running, self.running_reg)
        self.set_flag(system_stop, self.system_stop_reg)
        self.set_flag(leak_detect, self.leak_detected_reg)
        self.set_flag(thermal_fault, self.thermal_fault_reg)
        self.set_flag(sensor_fault, self.sensor_fault_reg)
        log.debug(f"Current Power: {current_power}")
        log.debug(f"On Time: {on_time}")
        self.update_input_register(self.current_power_register, [int(current_power)])
        self.update_input_register(self.run_time_register, [int(on_time)])

    def set_info_registers(self):
        self.update_input_register(self.version_register, [self.version])

        for s in self.info_registers.keys():
            if s in self.sensor_info.keys():
                for a in self.sensor_info[s].keys():
                    if a in self.info_registers[s].keys():
                        d_str = f"{self.sensor_info[s][a]}"
                        d_filter = filter(str.isdigit, d_str)
                        data = int("".join(d_filter))
                        self.update_input_register(self.info_registers[s][a], [data])

    def set_flag(self, flag, flag_reg):
        self.update_input_register(flag_reg, [1 if flag else 0])

    def update_driver_states(self, driver_dict):
        values = []
        for ch in driver_dict.keys():
            values.append(int(driver_dict[ch]))

        self.update_input_register(self.driver_state_register, values)
