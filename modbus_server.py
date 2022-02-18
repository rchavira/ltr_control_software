import logging
import threading
import time

#  pymodbus imports
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.server.asynchronous import StartTcpServer, StopServer


log = logging.getLogger(__name__)
logging.getLogger("pymodbus").setLevel(logging.WARNING)


class ModbusServer(object):
    def __init__(self, **kwargs):
        self.modbus_config = kwargs["modbus_config"]

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
        self.driver_state_register = self.modbus_config["system_registers"]["driver_state_register"]
        self.current_power_register = self.modbus_config["system_registers"]["current_power"]

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
        self.set_emulated_default()
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
            StartTcpServer(self.context)
        except Exception as ex:
            log.error(f"{ex}")
            self.server_started = False

    def get_shutdown_cmd(self):
        values = self.context[0].getValues(
            3, self.shutdown_reg, count=1
        )
        return values[0]

    def get_run_status(self):
        values = self.context[0].getValues(
            3, self.run_reg, count=1
        )
        return values[0]

    def get_power_target(self):
        values = self.context[0].getValues(
            3, self.power_reg, count=1
        )
        return values[0]

    def set_emulated_default(self):
        for si in self.modbus_config["emulation_registers"].keys():
            v = self.modbus_config["emulation_registers"][si]["default"]
            values = [v]
            self.context[0].setValues(
                3, self.modbus_config["emulation_registers"][si]["address"], values
            )

    def get_emulated_values(self):
        sdict = {}
        for si in self.modbus_config["emulation_registers"].keys():
            values = self.context[0].getValues(
                3, self.modbus_config["emulation_registers"][si]["address"], 1
            )
            dec_p = int(self.modbus_config["emulation_registers"][si]["decimal_places"])
            sdict[si] = values[0] / (10 ** dec_p)
        return sdict

    def update_sensor_info(self, sdict):
        for si in sdict.keys():
            try:
                v = float(sdict[si])
                dec_p = int(self.modbus_config["sensor_registers"][si]["decimal_places"])
                values = [int(v * (10 ** dec_p))]
                self.context[0].setValues(
                    4, self.modbus_config["sensor_registers"][si]["address"], values
                )
            except Exception as ex:
                log.error(f"{si}: {sdict[si]} - {ex}")


    def update_system_flags(self, running, system_stop, leak_detect, thermal_fault, sensor_fault, current_power, on_time):
        self.set_flag(running, self.running_reg)
        self.set_flag(system_stop, self.system_stop_reg)
        self.set_flag(leak_detect, self.leak_detected_reg)
        self.set_flag(thermal_fault, self.thermal_fault_reg)
        self.set_flag(sensor_fault, self.sensor_fault_reg)
        self.context[0].setValues(4, self.current_power_register, [current_power])

    def set_flag(self, flag, flag_reg):
        self.context[0].setValues(4, flag_reg, [1 if flag else 0])

    def update_driver_states(self, driver_dict):
        values = []
        for ch in driver_dict.keys():
            values.append(driver_dict[ch])

        self.context[0].setValues(
            4, self.driver_state_register, values
        )
