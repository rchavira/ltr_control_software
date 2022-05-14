"""
Bus Queue
This will take in a queue request with a callback to update data once retrieved.
"""
import logging

from devices.communication import BusInterface, BusType
from queue import Queue
from threading import Thread

log = logging.getLogger(__name__)


class BusRequest:
    dev_id: str
    args: dict
    read_function: classmethod
    call_back_function: classmethod
    data = object


class BusQueue(object):
    q: Queue
    bus_type: BusType
    q_thread: Thread
    q_running = bool

    def __init__(self, bus_type, **kwargs):
        self.q = Queue(maxsize=100)
        self.sig_dict = {}
        self.q_thread = Thread(target=self.q_monitor)
        self.q_running = False
        self.bus_type = bus_type

    def add_to_queue(self, dev_id, args, read, rtn):
        br = BusRequest()
        br.dev_id = dev_id
        br.args = args
        br.read_function = read
        br.call_back_function = rtn
        self.q.put(br, True)

    def q_start(self):
        self.q_thread = Thread(target=self.q_monitor)
        self.q_thread.isDaemon = True
        self.q_running = True
        self.q_thread.start()

    def q_stop(self):
        self.q_running = False
        if self.q_thread is not None:
            self.q_thread.join(2)
        self.q_thread = None

    def q_monitor(self):
        while self.q_running:
            if not self.q.empty():
                br = self.q.get()  # type: BusRequest
                br.data = br.read_function(**br.args)
                br.call_back_function(br.dev_id, br.data)
                self.q.task_done()

