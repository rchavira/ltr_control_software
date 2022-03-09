import logging
from tests.adc_test import hardware_test as adc_test
from tests.dio_tests import hardware_test as dio_test
from tests.chip_select_test import hardware_test as ch_sel_test
from tests.thermo_tests import hardware_test as thermo_test
from tests.sensor_tests import test as sensors_test
from tests.fan_tests import test as fan_test
from tests.driver_tests import test as driver_test
from tests.thermal_manager_test import test as thermal_manager_test

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(message)s"
    #level=logging.DEBUG, format="%(asctime)s - %(message)s"
)


def main():
    # result = True
    result = False
    if result:
        logging.info("Starting DIO Test...")
        result = dio_test()

    result = False
    if result:
        logging.info("Starting CH Select Test...")
        result = ch_sel_test()

    result = False
    if result:
        logging.info("Starting Fans Test...")
        result = fan_test()

    result = False
    if result:
        logging.info("Starting ADC Test...")
        result = adc_test()

    result = False
    if result:
        logging.info("Starting Driver Test...")
        result = driver_test()

    result = False
    if result:
        logging.info("Starting Thermo Test...")
        result = thermo_test()

    result = False
    if result:
        logging.info("Starting Thermo Test...")
        result = thermo_test()

    result = False
    if result:
        logging.info("Starting Sensors Test...")
        result = sensors_test()

    result = True
    if result:
        logging.info("Starting Thermal Manager Test...")
        result = thermal_manager_test()


if __name__ == '__main__':
    main()
