"""
This code is meant to run on the Seeed Xiao and serve
the IMU 3D Accelerometer and 3D Gyroscope on a 
BLE GATT Notification service.
"""

# general
import time
import board
import digitalio
import busio

#BLE
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

#IMU
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3

#here we define a new class of imu
#why? ref: https://forum.seeedstudio.com/t/imu-i2c-error-with-circuitpython-using-xiao-ble-sense/265020
class IMU(LSM6DS3):
    def __init__(self):
        dpwr = digitalio.DigitalInOut(board.IMU_PWR)
        dpwr.direction = digitalio.Direction.OUTPUT
        dpwr.value = 1
        time.sleep(1)
        i2c = busio.I2C(board.IMU_SCL, board.IMU_SDA)
        super().__init__(i2c)

#IMU
sensor = IMU()

#BLE
ble = BLERadio()
ble.name = "GroupXXLeft"
uart_server = UARTService()
advertisement = ProvideServicesAdvertisement(uart_server)

#LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

sendRate = 0.1

blinkRate = 0.5

blinkTime = time.monotonic() + blinkRate

# debug: True - print debug informatio, False: silent operation.
debug = True

def debugPrint(*p):  # * enables a list of arguments (tuple)
    if not (debug):
        return
    print(p)



data = [None] * 6

tag = [0,1,2,3,4,5]

while True:

    #switch off LED, donot be strange, it is True -> Off
    led.value = True

    # Advertise when not connected.
    debugPrint("Wait for connection")
    ble.start_advertising(advertisement)
    while not ble.connected:
        if time.monotonic() > blinkTime:
            led.value = not (led.value)
            blinkTime = time.monotonic() + blinkRate
            time.sleep(0.1)
        pass

     # Connected
    ble.stop_advertising()
    debugPrint("Connection established")

    # Loop and read packets
    sendTime = time.monotonic() + sendRate

    count = 0

    max_records = 30

    xx = ble.connections[0]

    while ble.connected:
        #switch on LED
        led.value = False

        uart_server.read(uart_server.in_waiting)
        time.sleep(0.05)

        '''
        # Here is for receieving, we donot use this function yet
        # INCOMING (RX) check for incoming text
        if uart_server.in_waiting:
            raw_bytes = uart_server.read(uart_server.in_waiting)
            text = raw_bytes.decode().strip()
            # print("raw bytes =", raw_bytes)
            debugPrint("RX:", text)
            if text == 'true':
                led.value = False # on
            else:
                led.value = True # off

        # OUTGOING (TX) periodically send text
        el
        '''
        if time.monotonic() > sendTime:

            data[0]  = sensor.acceleration[0]
            data[1]  = sensor.acceleration[1]
            data[2]  = sensor.acceleration[2]
            data[3]  = sensor.gyro[0]
            data[4]  = sensor.gyro[1]
            data[5]  = sensor.gyro[2]

            for i in range(0,6):
                #we use a # to seperate data
                text = "{}#{}".format(tag[i], data[i])
                uart_server.write(text.encode())
                debugPrint("TX:", text.strip())

            count += 1
            sendTime = time.monotonic() + sendRate
            led.value = not (led.value)
            time.sleep(0.01)

        #if count > max_records:
        #    xx.disconnect()
        #    break

    #switch off LED
    led.value = False
    time.sleep(0.05)
    # Disconnected
    debugPrint("DISCONNECTED")
