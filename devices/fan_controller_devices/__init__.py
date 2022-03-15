import sys
from enum import Enum


class FanDevType(Enum):
    emulated = 0
    fan_control_board = 1


class FanData(object):
    def __init__(self):
        self.fan_rpm = 0


class FanSpeedInterface(object):
    channels = {}

    def __init__(self, **kwargs):
        pass

    def init_device(self):
        pass

    def close_device(self):
        pass

    def get_fan_speed(self, channel):
        pass

    def set_fan_speed(self, channel, fan_speed):
        pass

    def start_updater(self):
        pass

    def stop_updater(self):
        pass


def loader(dev_type, **cfg):
    device = None
    if dev_type == FanDevType.emulated:
        if "EmulatedFanSpeed" not in sys.modules:
            from devices.fan_controller_devices.emulated import EmulatedFanSpeed
        device = EmulatedFanSpeed(**cfg)
    elif dev_type == FanDevType.fan_control_board:
        if "FCBv1Interface" not in sys.modules:
            from devices.fan_controller_devices.fan_control_board_v1 import (
                FCBv1Interface,
            )
        device = FCBv1Interface(**cfg)
    return device
