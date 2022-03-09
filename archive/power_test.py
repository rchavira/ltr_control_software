import time
import threading


class PowerTest(object):
    def __init__(self):
        self.power_target = 0
        self.power_target = 0
        self.time_at_current_power = 0
        self.current_power = 0
        self.running = False

        self.updater = None
        self.power = None

    def update_thread(self):
        st = time.time()
        while(self.running):
            dt = int(time.time() - st)
            if dt == 5:
                self.power_target = 3000
            elif dt == 60:
                self.power_target = 4000
            elif dt == 90:
                self.power_target = 2000
            elif dt > 120:
                self.power_target = 0
            time.sleep(0.5)

    def main_thread(self):
        last_change = 0
        last_power = 0

        change_delay = 10

        while(self.running):
            if self.current_power < self.power_target:
                if last_power != self.current_power or self.current_power == 0:
                    step = 800
                    if self.power_target - self.current_power < step:
                        step = self.power_target - self.current_power
                    self.current_power += step
                    last_power = self.current_power
                    last_change = time.time()
                else:
                    if time.time() - last_change >= change_delay:
                        step = 800
                        if self.power_target - self.current_power < step:
                            step = self.power_target - self.current_power
                        self.current_power += step
                        last_power = self.current_power
                        last_change = time.time()
            else:
                self.current_power = self.power_target
                last_power = self.current_power
                # last_change = time.time()

            if time.time() - last_change > change_delay:
                last_change = time.time() - change_delay

            self.time_at_current_power = int(time.time() - last_change)
            time.sleep(0.25)

    def start(self):
        self.updater = threading.Thread(target=self.update_thread)
        self.updater.isDaemon = False

        self.power = threading.Thread(target=self.main_thread)
        self.power.isDaemon = False

        self.running = True
        print("Starting Power Test")

        self.updater.start()
        self.power.start()


    def stop(self):
        self.running = False
        time.sleep(1)
        if self.updater is not None:
            self.updater.join(2)
        if self.power is not None:
            self.power.join(2)
        print("Power Test Stopped")

pt = PowerTest()

pt.start()

while(True):
    try:
        print(f"PT: {pt.power_target}, CT: {pt.current_power}, T: {pt.time_at_current_power}")
        time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Test...")
        pt.stop()
        break
