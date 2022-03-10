import logging
import time

log = logging.getLogger(__name__)


class RaspiInterface(object):
    def __init__(self, **kwargs):
        self.mux_pins = kwargs["mux_pins"]
        self.mux_strobe = int(kwargs["strobe"])
        self.report_pin = int(kwargs["report"])

    def chip_select(self, channel):
        bstr = "{0:04b}".format(channel)[::-1]

        for idx in range(4):
            self.set_digital(self.mux_pins[idx], int(bstr[idx]))

        self.set_digital(self.mux_strobe, 1)
        time.sleep(0.1)
        self.set_digital(self.mux_strobe, 0)

    def set_report_out(self, value):
        self.set_digital(self.report_pin, value)

    def read_thermo(self):
        pass

    def read_adc(self, channel):
        pass

    def read_digital(self, pin):
        pass

    def set_digital(self, pin, value):
        pass

    def shutdown(self):
        pass


class RaspiEmulate(RaspiInterface):
    def __init__(self, **kwargs):
        self.therm_value = 0x3261900
        self.adc_value = 512
        self.dig_value = 0

        super().__init__(**kwargs)

    def read_thermo(self):
        return self.therm_value

    def read_adc(self, channel):
        return self.adc_value

    def read_digital(self, pin):
        return self.dig_value

    def set_thermo_value(self, value):
        self.therm_value = value

    def set_adc_value(self, value):
        self.adc_value = value

    def set_dig_value(self, value):
        self.dig_value = value
