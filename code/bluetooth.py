
import asyncio, time
from ble_serial.bluetooth.ble_interface import BLE_interface

# None uses default/autodetection, insert values if needed
ADAPTER = "hci0"
SERVICE_UUID = None
WRITE_UUID = None
READ_UUID = None

class BLE_Devices:

    def __init__(self, mac_left, mac_right) -> None:
        self.mac_left = mac_left
        self.mac_right = mac_right
        # bluetooth left and right
        self.ble_left = None
        self.ble_right = None
        self.imu_left = [0]*6 # IMU data
        self.imu_right = [0]*6 # IMU data

    def update_imu_data(self, value, imu_data):
        res = value.split(b"#")# split input
        if len(res) == 2: #if there are two parts
            index_string = res[0].decode("utf-8");index = int(index_string)  # first is index and value
            value_string = res[1].decode("utf-8");value = float(value_string)# second is value
            imu_data[index] = value 
        return  imu_data
        
    def receive_callback_left(self, value: bytes):
        global imu_left, ble_left
        imu_left = self.update_imu_data(value, imu_left)

    def receive_callback_right(self, value: bytes):
        global imu_right, ble_right
        imu_right = self.update_imu_data(value, imu_right)

    def stop(self):
        if self.mac_left:
            # Stop listening to BLE notification, leading to BLE disconnection
            self.ble_left.stop_loop()
        if self.mac_right:
            # Stop listening to BLE notification, leading to BLE disconnection
            self.ble_right.stop_loop()

    async def ble_disconnect(self):
        if self.mac_left:
            await self.ble_left.disconnect()
        if self.ble_right:
            await self.ble_right.disconnect()

    async def connect(self):
        if self.mac_left:
            self.ble_left = BLE_interface(ADAPTER, SERVICE_UUID)
            self.ble_left.set_receiver(self.receive_callback_left)

        if self.mac_right:
            self.ble_right = BLE_interface(ADAPTER, SERVICE_UUID)
            self.ble_right.set_receiver(self.receive_callback_right)

        try:
            if self.ble_left:
                await self.ble_left.connect(self.mac_left, "public", 10.0)
                await self.ble_left.setup_chars(WRITE_UUID, READ_UUID, "rw")
            
            if self.mac_right:
                await self.ble_right.connect(self.mac_right, "public", 10.0)
                await self.ble_right.setup_chars(WRITE_UUID, READ_UUID, "rw")
            
            if self.mac_left and self.mac_right:
                await asyncio.gather(self.ble_left.send_loop(), self.ble_right.send_loop()) #triger bluetooth
            elif self.mac_left:
                await asyncio.gather(self.ble_left.send_loop())
            elif self.mac_right: 
                await asyncio.gather(self.ble_right.send_loop())
    
        except Exception as error:
            print(error)
    
        finally:
            # stop_recording = True # stop recording
            await self.ble_disconnect()