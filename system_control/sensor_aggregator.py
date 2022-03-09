import logging

log = logging.getLogger(__name__)


class SensorAggregator(object):
    def __init__(self, sensor_group, sample_size):
        self.max_size = sample_size
        self.sensor_group = sensor_group
        self.sensor_data = []
        self.last_value = 0
        self.value = 0
        self.delta = 0

    def add_data_point(self, sensor_dict):
        self.last_value = self.get_running_mean()
        avg = 0.0
        cnt = 0
        for sg in self.sensor_group:
            if sg in sensor_dict.keys():
                avg += sensor_dict[sg]
                cnt += 1
        if cnt > 0:
            avg = avg / cnt
        else:
            avg = 0.0

        if len(self.sensor_data) == self.max_size:
            self.sensor_data.pop(0)

        self.sensor_data.append(avg)
        self.value = self.get_running_mean()
        self.delta = self.value - self.last_value

    def get_running_mean(self):
        mean = 0
        if len(self.sensor_data) > 0:
            mean = sum(self.sensor_data) / len(self.sensor_data)
        return mean

    def get_delta(self):
        return abs(self.last_value - self.value)

    def get_range(self):
        l_min = min(self.sensor_data)
        l_max = max(self.sensor_data)
        return l_max - l_min
