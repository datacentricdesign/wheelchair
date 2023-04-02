import threading, time

from bluetooth import BLE_Devices

class TimerKeeper(threading.Thread):
    """ A parallel thread to keep track of time """
    def __init__(self, threadID, name, counter, period: int, activity: str, ble_devices: BLE_Devices):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.start_recording = False # we don't record data
        self.stop_recording = False  # we don't stop recoding
        self.start_time = 0
        self.period = period*1000
        self.activity = activity
        self.ble_devices: BLE_Devices = ble_devices

    def run(self):
      self.check_time()
      
    def check_time(self):
        # Show a count down to the user so that they start the activity to record
        count_down(3)
        print(f"\r{colors.WARNING}Recording!{colors.ENDC}")
        self.start_recording = True # start data recording
        self.start_time = round(time.time() * 1000)
        while True:
            time_left = self.start_time + self.period - time.time()*1000
            if self.start_time > 0 and time_left < 0:
                print(f"\r{colors.WARNING}Stop recording !{colors.ENDC}{(' ' * 50)}")
                self.stop_recording = True
                self.ble_devices.stop()
                break
            elif self.start_time > 0:
                total = self.period
                remaining = int(40 * time_left/total)
                complete = int(40 * (total-time_left)/total)
                print(f"\r[{colors.GREEN}{('#' * complete)}{(' ' * remaining)}{colors.ENDC}] {round(time_left/1000)} seconds left", end="")
            time.sleep(1)

class colors:
    """ Define colors to use in the text. """
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def count_down(seconds):
    count=0
    MAX=3
    while count<MAX:
        complete = int(50 * count/MAX)
        remaining = int(50 * (MAX-count)/MAX)
        print(f"\r[{('#' * complete)}{(' ' * remaining)}]", end="")
        time.sleep(1)
        count += 1
    print(f"\r{colors.WARNING}{(' ' * 52)}{colors.ENDC}")