import logging
import sys
import argparse

from tests.adc_test import hardware_test as adc_test
from tests.dio_tests import hardware_test as dio_test
from tests.chip_select_test import hardware_test as ch_sel_test
from tests.thermo_tests import hardware_test as thermo_test
from tests.sensor_tests import test as sensors_test
from tests.fan_tests import test as fan_test
from tests.driver_tests import test as driver_test
from tests.thermal_manager_test import test as thermal_manager_test

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")


def main(dio=False, ch_Sel=False, fans=False, adc=False, driver=False, thermo=False, sensors=False, thermal=False):
    result = True

    if result and dio:
        logging.info("Starting DIO Test...")
        result = dio_test()

    if result and ch_Sel:
        logging.info("Starting CH Select Test...")
        result = ch_sel_test()

    if result and fans:
        logging.info("Starting Fans Test...")
        result = fan_test()

    if result and adc:
        logging.info("Starting ADC Test...")
        result = adc_test()

    if result and driver:
        logging.info("Starting Driver Test...")
        result = driver_test()

    if result and thermo:
        logging.info("Starting Thermo Test...")
        result = thermo_test()

    if result and sensors:
        logging.info("Starting Sensors Test...")
        result = sensors_test()

    if result and thermal:
        logging.info("Starting Thermal Manager Test...")
        result = thermal_manager_test()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="ltr_control",
        usage='%(prog)s [options]',
        description="LTR Control Software Interface Testing",
        epilog='Meta Copyright 2022'
    )
    parser.add_argument('--loglevel', default=1, help='Log level [DEBUG (1-5) CRITICAL]')
    parser.add_argument('--test', default="ALL", help='What to test.  DIO, ADC, FANS, TC, SENSORS, THERMAL, ALL')

    args = parser.parse_args()

    loglevel = logging.DEBUG

    if args.loglevel == 0:
        loglevel = logging.NOTSET
    elif args.loglevel == 1:
        loglevel = logging.DEBUG
    elif args.loglevel == 2:
        loglevel = logging.INFO
    elif args.loglevel == 3:
        loglevel = logging.WARNING
    elif args.loglevel == 4:
        loglevel = logging.ERROR
    elif args.loglevel == 5:
        loglevel = logging.CRITICAL
    logging.basicConfig(level=loglevel, format="%(asctime)s - %(message)s")

    logging.info(args.test)
    dio = adc = fans = thermo = sensors = thermal = False
    if args.test == "ALL":
        dio = adc = fans = thermo = sensors = thermal=True
    else:
        if "DIO" in args.test:
            dio = True
        elif args.test == "ADC":
            adc = True
        elif args.test == "FANS":
            fans = True
        elif args.test == "TC":
            thermo = True
        elif args.test == "SENSORS":
            sensors = True
        elif args.test == "THERMAL":
            thermal = True

    main(dio=dio, adc=adc, fans=fans, thermo=thermo, sensors=sensors, thermal=thermal)
