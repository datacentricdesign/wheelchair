import logging, threading, time
import numpy as np

from timekeeper import TimerKeeper
from fsr import FSR
from bluetooth import BLE_Devices

class DataAggregator(threading.Thread):
    """ A parallel thread to merge data from IMUs and FSRs """
    def __init__(self, threadID, name, counter, fsr: FSR, ble_devices: BLE_Devices, folder, frequency, timeKeeper: TimerKeeper):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.fsr: FSR = fsr
        self.ble_devices: BLE_Devices = ble_devices
        self.timeKeeper: TimerKeeper = timeKeeper
        if self.timeKeeper is not None:
            self.label = self.timeKeeper.activity
        else:
            self.label = "continuous"
            self.start_time = round(time.time()*1000)
        self.folder = folder
        self.frequency = frequency
        self.enabled = True

    def run(self):
        self.update_data()

    def stop_collection(self):
        self.enabled = False

    # update data at a frequency 
    def update_data(self):
        output_data = []
        logging.info('Recording...')
        while self.enabled:
            # If no timekeeper, collect forever
            if self.timeKeeper is None or self.timeKeeper.start_recording:
                # output = timestamp + 6 left + 6 right + all pressures
                temp = [None] * ( 1 + 6 + 6 + self.fsr.number_fsr)
                temp[0]    = time.monotonic() #timestamp
                temp[1:7]  = self.ble_devices.imu_left
                temp[7:13] = self.ble_devices.imu_right
                if self.fsr.number_fsr > 0:
                    temp[13:13+self.fsr.number_fsr] = self.fsr.read_fsrs()
                output_data.append(temp)
            
            # If no timekeeper, save in chuncks of 1000 records
            if self.timeKeeper is None:
                if len(output_data) == 100:
                    print(output_data)
                    to_save = output_data
                    output_data = []
                    save = Save(0, "Save", 0, to_save, self.label, self.start_time, self.folder)
                    save.start()

            elif self.timeKeeper.stop_recording:
                self.enabled = False
            # Frequency, now 10 hz
            time.sleep(self.frequency)
        # Flush remaining data
        if self.timeKeeper is not None:
            self.start_time = self.timeKeeper.start_time
        save = Save(0, "Save", 0, output_data, self.label, self.start_time, self.folder)
        save.start()

class Save(threading.Thread):
    """ Save data in file """
    def __init__(self, threadID, name, counter, data, label, start_time, folder):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.data = data
        self.label = label
        self.start_time = start_time
        self.folder = folder

    def run(self):
        self.save_data_to_file()

    def save_data_to_file(self):
        logging.info('Saving...')
        try:
            timestr_filename = f"{self.label}-{self.start_time}.npz" #create a file name
            #timestr_filename = time.strftime(activity_name+"-%Y%m%d-%H%M%S", start_time)+".npz" #create a file name
            data = np.array(self.data) # change data to numpy
            data[:,0] = data[:,0] - data[0,0] 
            np.savez(self.folder + timestr_filename, data = data) # save npz file
            logging.info("Data saved into file: " + timestr_filename)
        except Exception as error:
            logging.error(error)