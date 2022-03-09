from time import sleep


test_config = {
    "spi": {
        "input_file": "spi_stdin.txt",
        "output_file": "spi_stdout.txt"
    }
}


def test():
    from system_control import ControllerDeviceTypes
    from devices.bus_manager import BusManager, BusType

    cfg = test_config["spi"]
    spi_mgr = BusManager(BusType.spi, ControllerDeviceTypes.emulated, **cfg)
    i2c_mgr = BusManager(BusType.i2c, ControllerDeviceTypes.emulated, **cfg)

    spi_mgr.blocker("test", True)
    spi_mgr.blocker("test", False)

