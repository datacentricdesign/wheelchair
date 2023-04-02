#!/usr/bin/env python

"""
This script allows to collect data for each activity.

Authors: Wolf Song, Jacky Bourgeois
License: MIT

Environment variables (.env file):
COMPLETE_DATA_PATH=/home/pi/wheelchair/data/
SAMPLING_FREQUENCY=0.1
COLLECTION_DURATION=5

BLE_MAC_DEVICE_LEFT=
BLE_MAC_DEVICE_RIGHT=
NUMBER_FSR=
"""

import asyncio, logging, time, os, signal # system functions
import RPi.GPIO as GPIO #GPIO for mux selection
import Adafruit_ADS1x15 #AD converter
from ble_serial.bluetooth.ble_interface import BLE_interface #bluetooth
import numpy as np #numpy for save files
import threading # for parallel process

from dotenv import load_dotenv
load_dotenv()

# None uses default/autodetection, insert values if needed
ADAPTER = "hci0"
SERVICE_UUID = None
WRITE_UUID = None
READ_UUID = None
# use light blue in your phone to find the mac address of your seeeduino xiao
BLE_MAC_DEVICE_LEFT = os.getenv("BLE_MAC_DEVICE_LEFT", None)
BLE_MAC_DEVICE_RIGHT = os.getenv("BLE_MAC_DEVICE_RIGHT", None)
NUMBER_FSR = int(os.getenv("NUMBER_FSR", 0))
COMPLETE_DATA_PATH = os.getenv("COMPLETE_DATA_PATH", os.path.abspath(os.getcwd())+'/data/')
SAMPLING_FREQUENCY = float(os.getenv("SAMPLING_FREQUENCY", 0.1))
COLLECTION_DURATION = int(os.getenv("COLLECTION_DURATION", 10))

def set_up_fsr(ad_chanel, mux_pins):
    adc = Adafruit_ADS1x15.ADS1115() #pls check ADS1115
    GAIN = 1 #pls check ADS1115
    adc.start_adc(ad_chanel, gain=GAIN) #pls check ADS1115
    GPIO.setmode(GPIO.BCM)  # use BCM layout, check Raspberry Pi
    GPIO.setwarnings(False) # disable warnings
    for each in mux_pins:   # all mux pin in output mode
        GPIO.setup(each, GPIO.OUT)
    return adc # return the handle of adc
        
def read_fsrs(adc,s_number,mux_pins,mux_selection):
    fsr_values = [0]*s_number # array of fsr values
    for chanel in range(0,s_number):  # for each chanel
        for pin_index in range (0,4): # set the ri9ght selection
            GPIO.output(mux_pins[pin_index],mux_selection[pin_index][chanel])
        #time.sleep(0.001) # for stable input, you can also delete it
        fsr_values[chanel] = adc.get_last_result() # AD converstion 
    return fsr_values

def save_data_to_file():
    global output_data, start_time
    logging.debug(output_data)
    try:
        timestr_filename = f"{activity_name}-{start_time}.npz" #create a file name
        #timestr_filename = time.strftime(activity_name+"-%Y%m%d-%H%M%S", start_time)+".npz" #create a file name
        data = np.array(output_data) # change data to numpy
        data[:,0] = data[:,0] - data[0,0] 
        np.savez(COMPLETE_DATA_PATH + timestr_filename, data = data) # save npz file
        print("Data saved into file: " + timestr_filename)
    except Exception as error:
        logging.error(error)

def update_imu_data(value, imu_data):
    res = value.split(b"#")# split input
    if len(res) == 2: #if there are two parts
        index_string = res[0].decode("utf-8");index = int(index_string)  # first is index and value
        value_string = res[1].decode("utf-8");value = float(value_string)# second is value
        imu_data[index] = value 
    return  imu_data
    
def receive_callback_left(value: bytes):
    global imu_left, ble_left
    imu_left = update_imu_data(value, imu_left)

def receive_callback_right(value: bytes):
    global imu_right, ble_right
    imu_right = update_imu_data(value, imu_right)

# a parallel thread
class updating_data_Thread(threading.Thread):
   def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
   def run(self):
      #print("Starting " + self.name)
      update_data()
      #print("Exiting " + self.name)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# update data at a frequency 
def update_data():
    
    global output_data, imu_left, imu_right, fsr_values, s_number,stop_flag,start_recording, stop_recording
    
    while True:
        if start_recording:
            # output = timestamp + 6 left + 6 right + all pressures
            temp = [None] * ( 1 + 6 + 6 + NUMBER_FSR)
            temp[0]    = time.monotonic() #timestamp
            temp[1:7]  = imu_left
            temp[7:13] = imu_right
            if NUMBER_FSR > 0:
                fsr_values = read_fsrs(adc, NUMBER_FSR,mux_pins,mux_selection)
                temp[13:13+NUMBER_FSR] = fsr_values
            output_data.append(temp)
        
        if stop_recording:
            break
        # Frequency, now 10 hz
        time.sleep(SAMPLING_FREQUENCY)
    save_data_to_file()

      
# a parallel thread
class Timer_Thread(threading.Thread):
   def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
   def run(self):
      #print("Starting " + self.name)
      check_time()
      #print("Exiting " + self.name)
      
def check_time():    
    global start_time
    while True:
        time_left = start_time + COLLECTION_DURATION*1000 - time.time()*1000
        if start_time > 0 and time_left < 0:
            print(f"\r{bcolors.WARNING}Stop recording !{bcolors.ENDC}{(' ' * 50)}")
            stop()
            break
        elif start_time > 0:
            total = COLLECTION_DURATION*1000
            remaining = int(30 * time_left/total)
            complete = int(30 * (total-time_left)/total)
            print(f"\r[{bcolors.OKGREEN}{('#' * complete)}{(' ' * remaining)}{bcolors.ENDC}] {round(time_left/1000)} seconds left", end="")
        time.sleep(1)
       
def stop():
    global stop_recording
    stop_recording = True
    if BLE_MAC_DEVICE_LEFT:
        ble_left.stop_loop()
    if BLE_MAC_DEVICE_RIGHT:
        ble_right.stop_loop()
        
async def ble_disconnect():
    if BLE_MAC_DEVICE_LEFT:
        await ble_left.disconnect()
    if BLE_MAC_DEVICE_RIGHT:
        await ble_right.disconnect()

async def main():

    global ble_left,ble_right, start_recording, start_recording, stop_recording, start_time

    if BLE_MAC_DEVICE_LEFT:
        ble_left = BLE_interface(ADAPTER, SERVICE_UUID)
        ble_left.set_receiver(receive_callback_left)

    if BLE_MAC_DEVICE_RIGHT:
        ble_right= BLE_interface(ADAPTER, SERVICE_UUID)
        ble_right.set_receiver(receive_callback_right)

    try:
        if BLE_MAC_DEVICE_LEFT:
            await ble_left.connect(BLE_MAC_DEVICE_LEFT, "public", 10.0)
            await ble_left.setup_chars(WRITE_UUID, READ_UUID, "rw")
        
        if BLE_MAC_DEVICE_RIGHT:
            await ble_right.connect(BLE_MAC_DEVICE_RIGHT, "public", 10.0)
            await ble_right.setup_chars(WRITE_UUID, READ_UUID, "rw")
         
        start_recording = True #start data recording
        start_time = round(time.time() * 1000)
        
        if BLE_MAC_DEVICE_LEFT and BLE_MAC_DEVICE_RIGHT:
            await asyncio.gather(ble_left.send_loop(), ble_right.send_loop()) #triger bluetooth
        elif BLE_MAC_DEVICE_LEFT:
            await asyncio.gather(ble_left.send_loop())
        elif BLE_MAC_DEVICE_RIGHT: 
            await asyncio.gather(ble_right.send_loop())
 
    except Exception as error:
        print(error)
 
    finally:
        stop_recording = True # stop recording
        await ble_disconnect()

if __name__ == "__main__":
    
    # we use the easiest "process coding", feel free to adjust to loop

    # global variables setup
    # activity _name
    
    print(bcolors.OKBLUE + "\n= = = = = = = = = = = = = = = = = = = = = = = =\n")
    print("Data collection script. Setting found in .env:")
    print(f"Number of FSR: {NUMBER_FSR}")
    print(f"BLE MAC device left: {BLE_MAC_DEVICE_LEFT}")
    print(f"BLE MAC device right: {BLE_MAC_DEVICE_RIGHT}")
    
    while True:
        print("\n= = = = = = = = = = = = = = = = = = = = = = = =\n" + bcolors.ENDC)
        
        activity_name = input("Please type in the name of the activity to collect.\n(press ENTER to quit):")
        
        if (activity_name == ""):
            break
        count=0
        MAX=3
        while count<MAX:
            complete = int(50 * count/MAX)
            remaining = int(50 * (MAX-count)/MAX)
            print(f"\r[{('#' * complete)}{(' ' * remaining)}]", end="")
            time.sleep(1)
            count += 1
        print(f"{bcolors.WARNING}\r[{('#' * 50)}]{bcolors.ENDC}", end="")
        print(f"\r{bcolors.WARNING}Recording!{(' ' * 50)}{bcolors.ENDC}")
        
        
        # setup fsr readings
        if NUMBER_FSR > 0:
            fsr_values = [0] * NUMBER_FSR # sensor value array
            ad_chanel = 0 # ad chanel
            mux_pins = [5,6,14,19] # we connect mux 4 pins to 5,6,14,19, feel free to change
            
            #adc setup
            adc = set_up_fsr(ad_chanel, mux_pins)

            #array for mux address, 4 pins, 16 channels 
            mux_selection    = [[0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1]]*4 
            mux_selection[1] =  [0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1] 
            mux_selection[2] =  [0,0,0,0,1,1,1,1,0,0,0,0,1,1,1,1] 
            mux_selection[3] =  [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1] 
        
        # bluetooth left and right
        ble_left = None
        ble_right = None
        
        imu_left = [0]*6 # IMU data
        imu_right = [0]*6 # IMU data
        
        output_data = [] #output data
        
        start_recording = False # we don't record data
        start_time = 0
        stop_recording = False # we don't stop recoding
        
        # logging for debug
        logging.basicConfig(level=logging.ERROR)
        
        #start data thread
        thread_update_data = updating_data_Thread(0, "Thread-0", 0)
        thread_update_data.start()
        
        
        #start data thread
        thread_timer = Timer_Thread(0, "Timer Thread", 0)
        thread_timer.start()

        #run bluetooth
        #asyncio.run(main())
        
        loop = asyncio.new_event_loop()
        loop.run_until_complete(main())
        loop.close()
    
