import logging

log = logging.getLogger(__name__)


class SensorAggregator(object):
    def __init__(self, sensor_group, sample_size):
        self.max_size = sample_size
        self.sensor_group = sensor_group
        self.sensor_data = []

    def add_data_point(self, sensor_dict):
        avg = 0.0
        for sg in self.sensor_group:
            avg += sensor_dict[sg]

        avg = avg / len(self.sensor_group)

        if len(self.sensor_data) == self.max_size:
            self.sensor_data.pop(0)

        self.sensor_data.append(avg)

    def get_running_mean(self):
        mean = 0
        if len(self.sensor_data) > 0:
            mean = sum(self.sensor_data) / len(self.sensor_data)
        return mean
