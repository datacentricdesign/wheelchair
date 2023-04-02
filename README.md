# Wheelchair Prototyping Platform

## Step 1 Get the code on your Raspberry Pi

To get all the resources of this repository on your Raspberry Pi, open a terminal and enter the following command:

```bash
git clone https://github.com/datacentricdesign/wheelchair.git
```

We assume that your Raspberry Pi user is 'pi'. Thus, after running this command, all files of this repository be in `/home/pi/wheelchair`. You can check via the graphical interface.

On the terminal, you can check by navigating to the folder (`cd`) and listing the files (`ls`):

```bash
cd /home/pi/wheelchair
ls
```

## Step 2 Data Upload

In this step, we want to set up a mechanism for continuously uploading data on a server. It makes it easier to backup, visualize, share and use for machine learning activities. For this, we will set up a Python script that runs automatically when the Raspberry Pi starts. It will look for data files ending with `.complete.npz`, meaning that other scripts are not adding more data to this file anymore. For each file, it uploads data and moves the file to an archive folder.

### Step 2.1 Generate a public/private key set

To upload your data to the server, the device (e.g. Raspberry Pi) needs to authenticate itself. For this, it uses a public/private key set: the private key stays on the device, and the public key is shared with anyone who needs to receive messages from the device.

On the terminal, type in:

```bash
cd /home/pi/wheelchair
openssl genrsa -out private.pem 4096
openssl rsa -in private.pem -outform PEM -pubout -out public.pem
```

Explanation: first we go to the folder containing all our code. Then, we generate a private key. This creates a file `private.pem` the folder. Finally, it extracts the public key and creates a file `public.pem`.

## Step 2.2 Create a _Thing_ on the server

To set up the continuous data upload, you need to create an account on [https://dcdlab.org](https://dcdlab.org).

Once you are signed in, you create a new `Thing`, i.e. the digital representation of your prototype. You give is a name (e.g. 'My Wheelchair'), a description, and select type 'Generic'. It asks you for the public key of your device. Open the file `public.pem` created in the previous step, copy its content and paste it into the web form. Make sure to remove the empty line if there is any.

Then, press the blue button 'Create' to create the `Thing`.

## Step 2.3 Set up environment variables

The code you need to upload data on the server is in the folder `code`. It includes the python script `bucket_thing.py` and the service file `bucket_thing.service`. This code is generic and needs some additional information to upload data to your `Thing` on the server. For this, we create a file `.env` in `/home/pi/wheelchair`. You can do this via the terminal:

```bash
cd /home/pi/wheelchair
nano .env
```

Enter the following information:

```
THING_ID=dcd:things:...
PRIVATE_KEY_PATH=/home/pi/wheelchair/private.pem
COMPLETE_DATA_PATH=/home/pi/wheelchair/data/*.complete.npz
ARCHIVE_PATH=/home/pi/wheelchair/archive/
LOG_PATH=/home/pi/wheelchair/logs
UPLOAD_FREQUENCY=10
```

Explanation:
* THING_ID is the identifier of your thing. You can find it on the dcdlab.org (once signed in). On the left panel, click on the name of your `Thing` and scroll down to 'Settings'. It appears as 'ID' and starts with `dcd:things:`.
* PRIVATE_KEY_PATH is the path to the file containing the private key generated in Step 2.1.
* COMPLETE_DATA_PATH is the folder where the data from sensors is collected, and waiting to be uploaded.
* ARCHIVE_PATH is the folder in which we archive the data once it has been uploaded
* LOG_PATH is the folder where the script will store all details of its execution. This is helpful to debug when something is not working as expected.
* UPLOAD_FREQUENCY defines how often the data folder should be checked for new data to upload. The default is 10 seconds.

## Step 2.4 Install dependencies

The Python script relies on a Python module that we develop to make the interaction with the server easier. You can find more detail about it on the [module web page](https://pypi.org/project/dcd-sdk/). We need to install this module for the Raspberry Pi:

```bash
sudo pip install dcd-sdk
```

## Step 2.5 Set up the data upload service

To run the Python script automatically when the Raspberry Pi starts, we need to set up a `service`. We provide the specification of this in the file `bucket_thing.service`. Thus, we first copy this file into the folder of system scripts, by typing in the terminal

```bash
sudo cp /home/pi/wheelchair/code/bucket_thing.service /lib/systemd/system/bucket_thing.service
```

Explanation: `cp` is the command to copy. `sudo` means we take admin superpowers to (consciously, and carefully) write a file in the system files. 

Then, we enable the script as follows:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bucket_thing.service
```

Explanation: we first reload the service system so that it takes the new service into account. Then, we enable our service, running the script automatically when the Raspberry Pi starts.

You can reboot the Raspberry Pi to check.
```
sudo systemctl start bucket_thing.service