#!/usr/bin/env python

"""
This script allows to collect data continuously.

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

import asyncio, logging, os, signal, sys, time # system functions

from fsr import FSR
from bluetooth import BLE_Devices
from save import DataAggregator
from timekeeper import TimerKeeper

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)

# use light blue in your phone to find the mac address of your seeeduino xiao
BLE_MAC_DEVICE_LEFT = os.getenv("BLE_MAC_DEVICE_LEFT", None)
BLE_MAC_DEVICE_RIGHT = os.getenv("BLE_MAC_DEVICE_RIGHT", None)
NUMBER_FSR = int(os.getenv("NUMBER_FSR", 0))
COMPLETE_DATA_PATH = os.getenv("COMPLETE_DATA_PATH", os.path.abspath(os.getcwd())+'/data/')
SAMPLING_FREQUENCY = float(os.getenv("SAMPLING_FREQUENCY", 0.1))

def signal_handler(sig, frame):
    print("Disconnecting...")
    global enabled
    enabled = False
    dataAggregator.stop_collection()
    ble_devices.stop()
    sys.exit(0)

if __name__ == "__main__":
    
    logging.info('Data collection service')

    signal.signal(signal.SIGINT, signal_handler)

    enabled = True

    # As long as the Raspbeery Pi is running or an interruption is caught
    while enabled:
        try:
            logging.info('Set up sensor reading')
            # Set up FSR readings
            fsr = FSR(NUMBER_FSR)
            # Set up BLE devices
            ble_devices = BLE_Devices(BLE_MAC_DEVICE_LEFT, BLE_MAC_DEVICE_RIGHT)

            # Start data thread
            logging.info('Set up the data aggregator')
            dataAggregator = DataAggregator(0, "Data Aggregator Thread", 0, fsr, ble_devices, COMPLETE_DATA_PATH, SAMPLING_FREQUENCY, None)
            dataAggregator.start()
            
            if (BLE_MAC_DEVICE_LEFT is not None or BLE_MAC_DEVICE_RIGHT is not None):
                logging.info('Start BLE connections')
                loop = asyncio.new_event_loop()
                loop.run_until_complete(ble_devices.connect())
                loop.close()
            else:
                dataAggregator.join()
        except Exception as error:
            # catch errors and start again
            logging.error(error)
