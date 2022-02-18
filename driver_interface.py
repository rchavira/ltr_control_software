import logging

log = logging.getLogger(__name__)


class PwmInfo(object):
    dc = 0
    pwm = 0


class DriverInterface(object):
    def __init__(self, **kwargs):
        self.address = kwargs["driver_config"]["device_address"]
        self.frequency = kwargs["driver_config"]["device_frequency"]
        self.channels = [PwmInfo()] * 16
        self.pwm = [0] * 16
        self.dc = [0] * 16

    @staticmethod
    def remap(x, oMin, oMax, nMin, nMax):
        # range check
        if oMin == oMax:
            print("Warning: Zero input range")
            return None

        if nMin == nMax:
            print("Warning: Zero output range")
            return None

        # check reversed input range
        reverseInput = False
        oldMin = min(oMin, oMax)
        oldMax = max(oMin, oMax)
        if not oldMin == oMin:
            reverseInput = True

        # check reversed output range
        reverseOutput = False
        newMin = min(nMin, nMax)
        newMax = max(nMin, nMax)
        if not newMin == nMin:
            reverseOutput = True

        portion = (x - oldMin) * (newMax - newMin) / (oldMax - oldMin)
        if reverseInput:
            portion = (oldMax - x) * (newMax - newMin) / (oldMax - oldMin)

        result = portion + newMin
        if reverseOutput:
            result = newMax - portion

        return result

    def set_duty_cycle(self, channel, dc):
        #log.info(f"Set duty cycle on channel: {channel} to value: {dc}")
        pwm = int(self.remap(dc, 0, 100, 0, 0xFFFF))
        self.channels[channel].dc = dc
        self.channels[channel].pwm = pwm
