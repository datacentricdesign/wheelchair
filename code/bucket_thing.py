#!/usr/bin/env python

"""
This script is meant to run as a Raspberry Pi Service.
It connects to the Bucket Thing and continuously look for data to upload.

Authors: Wolf Song, Jacky Bourgeois
License: MIT

Environment variables (.env file):
THING_ID=dcd:things:...
PRIVATE_KEY_PATH=/home/pi/wheelchair/private.pem
LOG_PATH=/home/pi/wheelchair/logs

COMPLETE_DATA_PATH=/home/pi/wheelchair/data/
ARCHIVE_PATH=/home/pi/wheelchair/archive/
UPLOAD_FREQUENCY=10

"""

import numpy as np
import os, glob
from os.path import join
import time

# Import Thing from the Data-Centric Design
from dcd.bucket.thing import Thing

COMPLETE_DATA_PATH = os.getenv("COMPLETE_DATA_PATH", os.path.abspath(os.getcwd())+'/data/')
ARCHIVE_PATH = os.getenv("ARCHIVE_PATH", os.path.abspath(os.getcwd())+'/archive/')
UPLOAD_FREQUENCY = int(os.getenv("UPLOAD_FREQUENCY", "10"))
NUMBER_FSR = int(os.getenv("NUMBER_FSR", "0"))

def initialize_properties(thing):
    """Retrieve or create properties on the server
    Return dictionary of properties
    """
    thing.logger.info("Retrieve or create properties")
    properties = {
        "acc_left": thing.find_or_create_property("Accelerometer Left", "ACCELEROMETER"),
        "acc_right": thing.find_or_create_property("Accelerometer Right", "ACCELEROMETER"),
        "gyro_left": thing.find_or_create_property("Gyroscope Left", "GYROSCOPE"),
        "gyro_right": thing.find_or_create_property("Gyroscope Right", "GYROSCOPE"),
        "fsr": thing.find_or_create_property("Force Distribution 10", "FSR10"),
        "label": thing.find_or_create_property("Test Label", "TEXT")
    }
    return properties


if __name__ == "__main__":
    thing = None
    properties = None

    # Initialisation loop. Failures are likely to be network issues
    # (e.g. not yet connected to Internet) or a configuration issue.
    while thing is None or properties is None:
        try:
            # Create an instance of Thing
            thing = Thing()
            properties = initialize_properties(thing)
        except Exception as error:
            # Wait a moment and try again.
            print(error)
            time.sleep(5)

    # Main loop. check the data file and upload all files ending with .complete.npz
    while True:
        try:
            file_list = glob.glob(COMPLETE_DATA_PATH + '*.npz')
            thing.logger.info("Checking for data files to upload...")
            for file_path in file_list:
                thing.logger.info(f"Found file {file_path}.")
                # Retrieve timestamp and label from file name
                file_name = os.path.basename(file_path)
                start_timestamp = int(file_name.split(".")[0].split("-")[1])
                label = file_name.split(".")[0].split("-")[0]
                # Load the npz data file
                data = np.load(file_path)['data']
                for values in data:
                    # Convert relative time to absolute, in milliseconds
                    ts = start_timestamp + values[0]
                    # Inject data in each property
                    if (values[1:4].sum() != 0):
                        properties["acc_left"].update_values(values[1:4], ts, mode='a')
                        properties["acc_right"].update_values(values[7:10], ts, mode='a')
                    if (values[4:7].sum() != 0):
                        properties["gyro_left"].update_values(values[4:7], ts, mode='a')
                        properties["gyro_right"].update_values(values[10:13], ts, mode='a')
                    if (NUMBER_FSR>0 and values[13:13+NUMBER_FSR].sum() != 0):
                        properties["fsr"].update_values(values[13:13+NUMBER_FSR], ts, mode='a')
                    properties["label"].update_values([label], ts, mode="a")
                # Upload data to the server
                for name in properties:
                    properties[name].sync()
                # Move file to the archive folder
                os.rename(file_path, ARCHIVE_PATH + os.path.basename(file_path))
            thing.logger.info("Done uploading data.")
        except Exception as error:
            thing.logger.error(error)
        time.sleep(UPLOAD_FREQUENCY)