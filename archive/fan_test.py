import time
from fanboard_hardware import FanBoardHardware
fbg = {"port":"/dev/ttyUSB0","baudrate":115200,"timeout":0.5}
fb = FanBoardHardware(**fbg)
fb.start_monitor()
for i in range(5):
    print(fb.rpm_values)
    print(fb.temperature)
    time.sleep(1)
fb.stop_monitor()
