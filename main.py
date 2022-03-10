import logging
import sys
import argparse
from time import sleep

from system_control.system_manager import SystemManager


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ltr_control",
        usage='%(prog)s [options]',
        description="LTR Control Software.  A modbus TCP interface to LTR Chassis hardware.",
        epilog='Meta Copyright 2022'
    )
    parser.add_argument('--service', help='Run Controller as a Service', action="store_true")
    parser.add_argument('--emulate', help='Emulate all hardware on the system.', action="store_true")
    parser.add_argument('--loglevel', default=1, help='Log level [DEBUG (1-5) CRITICAL]')
    args = parser.parse_args()

    run_as_service = args.service
    if args.emulate:
        config_file = "emulate_config.json"
    else:
        config_file = "emulate_config.json"

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

    if run_as_service:
        logging.basicConfig(filename="system.log", level=loglevel, format="%(asctime)s - %(message)s")
    else:
        logging.basicConfig(level=loglevel, format="%(asctime)s - %(message)s")

    log = logging.getLogger(__name__)

    log.info("Loading System...")
    ltr_system = SystemManager(config_file)

    log.info("*************Starting System****************")
    ltr_system.start_system()

    while ltr_system.running:
        try:
            sleep(5)
        except KeyboardInterrupt:
            break

    log.info("*************Stopping System****************")
    ltr_system.stop_system()
    sys.exit()
