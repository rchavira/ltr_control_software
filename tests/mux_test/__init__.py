from time import sleep


test_config = {
    "dio": {
        "input_pins": [1,2,3,4],
        "output_pins": [10,24,35]
    },
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
    from devices.mux_devices import MuxDeviceInterface, MuxDeviceTypes, loader
    from devices.dio_devices import DioInterface, loader as dio_loader

    dio = dio_loader(ControllerDeviceTypes.emulated, **test_config["dio"])

    mux = loader(MuxDeviceTypes.emulated, dio, **test_config["config"])

