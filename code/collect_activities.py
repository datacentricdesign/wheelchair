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

import asyncio, logging, os # system functions

from fsr import FSR
from bluetooth import BLE_Devices
from save import DataAggregator
from timekeeper import TimerKeeper, count_down, colors

from dotenv import load_dotenv
load_dotenv()

# use light blue in your phone to find the mac address of your seeeduino xiao
BLE_MAC_DEVICE_LEFT = os.getenv("BLE_MAC_DEVICE_LEFT", None)
BLE_MAC_DEVICE_RIGHT = os.getenv("BLE_MAC_DEVICE_RIGHT", None)
NUMBER_FSR = int(os.getenv("NUMBER_FSR", 0))
COMPLETE_DATA_PATH = os.getenv("COMPLETE_DATA_PATH", os.path.abspath(os.getcwd())+'/data/')
SAMPLING_FREQUENCY = float(os.getenv("SAMPLING_FREQUENCY", 0.1))
COLLECTION_DURATION = int(os.getenv("COLLECTION_DURATION", 10))

if __name__ == "__main__":

    # Show the settings provided in the .env file    
    print(colors.BLUE + "\n= = = = = = = = = = = = = = = = = = = = = = = =\n")
    print("Data collection script. Setting found in .env:")
    print(f"Number of FSR: {NUMBER_FSR}")
    print(f"BLE MAC device left: {BLE_MAC_DEVICE_LEFT}")
    print(f"BLE MAC device right: {BLE_MAC_DEVICE_RIGHT}")
    
    # for each activity
    while True:
        print("\n= = = = = = = = = = = = = = = = = = = = = = = =\n" + colors.ENDC)
        
        activity_name = input("Please type in the name of the activity\nto collect (press ENTER to quit):")
        
        # If the user input is empty (Pressed ENTER), quit the loop, i.e. emd the program
        if (activity_name == ""):
            break
        
        # set up FSR readings
        fsr = FSR(NUMBER_FSR)
        # Set up BLE devices
        ble_devices = BLE_Devices(BLE_MAC_DEVICE_LEFT, BLE_MAC_DEVICE_RIGHT)
        
        # logging for debug
        #logging.basicConfig(level=logging.ERROR)
        
        # Start timer thread
        timeKeeper = TimerKeeper(0, "Timer Keeper Thread", 0, COLLECTION_DURATION, activity_name, ble_devices)
        timeKeeper.start()

        # Start data thread
        dataAggregator = DataAggregator(0, "Data Aggregator Thread", 0, fsr, ble_devices,  COMPLETE_DATA_PATH, SAMPLING_FREQUENCY, timeKeeper)
        dataAggregator.start()
        
        loop = asyncio.new_event_loop()
        loop.run_until_complete(ble_devices.connect())
        loop.close()
