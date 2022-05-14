import random
from time import sleep, time
import logging


from threading import Thread

from devices.communication import BusType

from devices.bus_queue import BusQueue


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")


def read_test():
    sleep(0.1)
    return random.random()


def callback(dev_id, data):
    data_dict[dev_id] = data
    logging.debug(f"updated {dev_id}: {data}")


def monitor_thread(prefix):
    while run_threads:
        for i in range(10):
            logging.debug(f"Adding {prefix}{i} to queue...")
            bq.add_to_queue(f"{prefix}{i}", {}, read_test, callback)
            sleep(0.2)


bq = BusQueue(BusType.spi)

data_dict = {}

run_threads = False
logging.debug("starting queue...")
bq.q_start()

t1 = Thread(target=monitor_thread, args=["a"])
t2 = Thread(target=monitor_thread, args=["b"])

run_threads = True

t1.start()
sleep(0.3)
t2.start()

for _ in range(20):
    sleep(1)
    print(f"{data_dict}")

bq.q_stop()
logging.debug("stopping queue...")
run_threads = False

if t1 is not None:
    t1.join(2)

if t2 is not None:
    t2.join(2)

bq = None

print("done")
