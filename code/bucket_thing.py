#!/usr/bin/env python

"""
This script is meant to run as a Raspberry Pi Service.
It connects to the Bucket Thing and continuously look for data to upload.
"""

import numpy as np
import os, glob
from os.path import join
import time

# Import Thing from the Data-Centric Design
from dcd.bucket.thing import Thing

COMPLETE_DATA_PATH = os.getenv("COMPLETE_DATA_PATH", os.path.abspath(os.getcwd())+'/data/' + '*.complete.npz')
ARCHIVE_PATH = os.getenv("ARCHIVE_PATH", os.path.abspath(os.getcwd())+'/archive/')
UPLOAD_FREQUENCY = int(os.getenv("UPLOAD_FREQUENCY", "10"))

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
        "fsr": thing.find_or_create_property("Wheelchair Force Distribution 10", "WHEELCHAIR_FORCE_DISTRIBUTION_10"),
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
            file_list = glob.glob(COMPLETE_DATA_PATH)
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
                    ts = start_timestamp + round(values[0]*1000)
                    # Inject data in each property
                    properties["acc_left"].update_values(values[1:4], ts, mode='a')
                    properties["acc_right"].update_values(values[7:10], ts, mode='a')
                    properties["gyro_left"].update_values(values[4:7], ts, mode='a')
                    properties["gyro_right"].update_values(values[10:13], ts, mode='a')
                    properties["fsr"].update_values(values[13:25], ts, mode='a')
                    properties["label"].update_values([label], ts, mode="a")
                # Upload data to the server
                for property in properties:
                    property.sync()
                # Move file to the archive folder
                os.rename(file_path, ARCHIVE_PATH + os.path.basename(file_path))
            thing.logger.info("Done uploading data.")
        except Exception as error:
            thing.logger.error(error)
        time.sleep(UPLOAD_FREQUENCY)