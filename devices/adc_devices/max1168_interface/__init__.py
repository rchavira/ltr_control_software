"""
Max1168 interface
"""

import logging
import struct

from devices.adc_devices import AdcInfo, AdcInterface
from devices.bus_manager import BusManager
from devices.chip_select import ChipSelector

log = logging.getLogger(__name__)

default_config = {
    "chip_select": 9,
    "devices": {
        "t11": {"channel": 0, "min_val": 0, "max_val": 150},
        "t12": {"channel": 1, "min_val": 0, "max_val": 150},
    },
}


class Max1168Interface(AdcInterface):
    bus_mgr: BusManager
    chip_select: ChipSelector

    def __init__(self, dev_name, bus, ch_sel, **kwargs):
        super().__init__()
        self.chip_select = ch_sel
        self.bus_mgr = bus
        self.resolution = 65535
        self.cs = kwargs["chip_select"]
        for dev_id in kwargs["devices"].keys():
            self.channels[dev_id] = AdcInfo(
                kwargs["devices"][dev_id]["channel"],
                dev_name,
                kwargs["devices"][dev_id]["min_val"],
                kwargs["devices"][dev_id]["max_val"],
                self.resolution,
            )

    def read_channel_old(self, dev_id):

        if self.bus_mgr.bus_blocker(dev_id, True):
            self.chip_select.chip_select(self.cs)

            # cmd = struct.pack("<H", (int(self.channels[dev_id].channel) << 5 | 3 << 3))
            chdat = int(self.channels[dev_id].channel) << 5 | 3 << 3
            cmd = struct.pack("<B", chdat)
            # log.debug(f"{dev_id} :> {chdat}")
            response = self.bus_mgr.send_and_receive(cmd, 3)
            # log.debug(f"{dev_id} :< {struct.unpack('>HB', response)}")
            raw, _ = struct.unpack(">HB", response)
            self.channels[dev_id].set_value(raw)

            self.chip_select.reset()

            self.bus_mgr.bus_blocker(dev_id, False)

        return self.channels[dev_id].value

    def read_channel(self, dev_id):
        """
        Reads a channel from the selected device.  The chip_select must be set and then the MOSI data sent to specify
        the read channel.  The response is transmitted on MISO and read in as a response.
        The command format for MAX1168 is documented as follows:
        MSB                                                     LSB
        BIT7    BIT6    BIT5    BIT4    BIT3    BIT2    BIT1    BIT0
        CHSEL2  CHSEL1  CHSEL0  SCAN1   SCAN0   PD_SEL1 PD_SEL0 CLK

        Where
            CHSEL is a 3 bit value indicating the channel
            SCAN is the scan mode
            PD_SEL is the power-down mode
            CLK is the clock mode (internal/external)

        :param dev_id: the sensor device unique id

        :return: the raw A2D value unmapped 16bit value
        """
        # apply the chip select for this device
        self.chip_select.chip_select(self.cs)

        # bitshift the channel value 5 bits and Set bit4 and bit3 to true (scan mode)
        chdat = int(self.channels[dev_id].channel) << 5 | 3 << 3
        # command is one byte, fix endian for MSBLSB
        cmd = struct.pack("<B", chdat)
        response = self.bus_mgr.send_and_receive(cmd, 3)
        # 3 bytes are returned, Uint16 is data and the last byte is configuration and can be ignored
        raw, _ = struct.unpack(">HB", response)
        self.channels[dev_id].set_value(raw)

        # remove chip select (required before reading data from this device again)
        self.chip_select.reset()

        return self.channels[dev_id].value
