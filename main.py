import logging

from time import sleep

from system_control.system_manager import SystemManager

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")


logging.info("Loading System...")
ltr_system = SystemManager()

logging.info("*************Starting System****************")
ltr_system.start_system()

while ltr_system.running:
    try:
        sleep(1)
    except KeyboardInterrupt:
        break

logging.info("*************Stopping System****************")
ltr_system.stop_system()
