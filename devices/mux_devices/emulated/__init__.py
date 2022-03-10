import logging

from devices.mux_devices import MuxDeviceInterface

log = logging.getLogger(__name__)

default_configuration = {}


class EmulatedMux(MuxDeviceInterface):
    def __init__(self, dio, **kwargs):
        super().__init__(dio, **kwargs)

    def encode(self, output_ch):
        log.debug(f"MUX setting output {output_ch}")
