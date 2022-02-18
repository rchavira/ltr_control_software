import logging

log = logging.getLogger(__name__)


class OutputControl(object):
    def __init__(self, channel, default):
        self.channel = channel
        self.default = default
        self.locked = False
        self.lock_list = []
        self.value = 0

    def lock(self, locker):
        if locker not in self.lock_list:
            self.lock_list.append(locker)
        self.locked = True
        self.value = 0

    def set_output(self, value):
        # log.info(f"Setting Output: {self.channel}, locked: {self.locked}, requested value: {value}")
        if not self.locked:
            self.value = value
            return True
        else:
            return False

    def unlock(self, locker):
        if locker in self.lock_list:
            self.lock_list.remove(locker)
        if len(self.lock_list) == 0:
            self.locked = False

    def get_value(self):
        return self.value
