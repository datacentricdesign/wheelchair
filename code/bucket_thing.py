import numpy as np
import os, glob
from os.path import join
import time
import logging
from dotenv import load_dotenv

# Import Thing from the Data-Centric Design
from dcd.bucket.thing import Thing

# Create an instance of Thing
my_thing = Thing()

# Retrieve or create properties
property_acc_left = my_thing.find_or_create_property("Accelerometer Left", "ACCELEROMETER")
property_acc_right = my_thing.find_or_create_property("Accelerometer Right", "ACCELEROMETER")
property_gyro_left = my_thing.find_or_create_property("Gyroscope Left", "GYROSCOPE")
property_gyro_right = my_thing.find_or_create_property("Gyroscope Right", "GYROSCOPE")
property_fsr = my_thing.find_or_create_property("Wheelchair Force Distribution", "WHEELCHAIR_FORCE_DISTRIBUTION")
property_label = my_thing.find_or_create_property("Test Label", "TEXT")


DATA_PATH = os.path.abspath(os.getcwd())+'/data/' + '*.complete.npz'
ARCHIVE_PATH = os.path.abspath(os.getcwd())+'/archive/'

file_list = glob.glob(DATA_PATH)

while True:
    try:
        logging.log("Checking for data files to upload...")
        for file_path in file_list:
            logging.log("Found " + file_path)
            # Retrieve timestamp from file
            file_name = os.path.basename(file_path)
            start_timestamp = int(file_name.split(".")[0].split("-")[1])
            label = file_name.split(".")[0].split("-")[0]
            data = np.load(file_path)['data']
            for values in data:
                # Retrieve time from 
                ts = start_timestamp + round(values[0]*1000)
                # Inject data in each property
                property_acc_left.update_values(values[1:4], ts, mode='a')
                property_acc_right.update_values(values[7:10], ts, mode='a')
                property_gyro_left.update_values(values[4:7], ts, mode='a')
                property_gyro_right.update_values(values[10:13], ts, mode='a')
                property_fsr.update_values(values[13:25], ts, mode='a')
                property_label.update_values([label], ts, mode="a")
            # Upload data
            property_acc_left.sync()
            property_acc_right.sync()
            property_gyro_left.sync()
            property_gyro_right.sync()
            property_fsr.sync()
            property_label.sync()
            os.rename(file_path, ARCHIVE_PATH + os.path.basename(file_path))
        logging.log("Done uploading data.")
    except Exception as error:
        logging.error(error)
    time.sleep(10)