import requests
import time
import asyncio
from adafruit_mlx90614 import MLX90614
import board
import busio
from datetime import datetime
from bleak import BleakScanner, BleakClient
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

API_KEY = "AIzaSyDcmVBTt3zT0eJUf97tFkX50u9KyqHzlo"
DATABASE_URL = "https://cognitive-load-default-rtdb.asia-southeast1.firebasedatabase.app"
SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "00002A37-0000-1000-8000-00805F9B34FB"

# I2C setup for temperature sensor
i2c = busio.I2C(board.SCL, board.SDA)
mlx = MLX90614(i2c)

# I2C setup for EMG sensor
adc = ADS.ADS1115(i2c, data_rate=860, gain=1)
chan = AnalogIn(adc, ADS.P0)

class HeartRateDelegate:
    def __init__(self):
        self.heart_rate = None

    def handleNotification(self, characteristic, value):
        self.heart_rate = value[1] if len(value) > 1 else value[0]
        print(f"Heart Rate: {self.heart_rate} bpm")
        send_heart_rate_and_temp(self.heart_rate)

def send_heart_rate_and_temp(heart_rate):
    temperature = round(mlx.object_temperature, 2)  # Read temperature

    # Data payload for heart rate and temperature
    data = {
        "BPM": heart_rate,
        "Temp": temperature,
    }

    # Get current timestamp for data
    current_time = datetime.now().strftime("%A, %B %d %H:%M:%S")

    # Firebase path for heart rate and temperature data
    url = f"{DATABASE_URL}/Data/{current_time}.json?auth={API_KEY}"

    # Send data to Firebase
    response = requests.put(url, json=data)
    if response.status_code == 200:
        print("Heart rate and temperature sent successfully")
    else:
        print(f"Failed to send heart rate/temperature data, Error: {response.status_code}, {response.text}")

# Function to send EMG data to Firebase
def send_emg_data(emg_value, voltage):
    current_time = datetime.now().strftime("%A, %B %d %H:%M:%S")

    # Data payload for EMG
    data = {
        "EMG_Value": emg_value,
        "Voltage": voltage,
    }

    # Firebase path for EMG data
    url = f"{DATABASE_URL}/EMG_Data/{current_time}.json?auth={API_KEY}"

    # Send data to Firebase
    response = requests.put(url, json=data)
    if response.status_code == 200:
        print("EMG data sent successfully")
    else:
        print(f"Failed to send EMG data, Error: {response.status_code}, {response.text}")

async def scan_for_devices():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=10.0)

    found_device = None    
    for device in devices:
        print(f"Device {device.address} ({device.rssi} dBm)")
        if SERVICE_UUID in device.metadata["uuids"]:
            print(f"Found target device: {device.address}")
            found_device = device.address
            break
    return found_device

async def connect_to_device(address):
    print(f"Connecting to device {address}...")
    try:
        client = BleakClient(address)
        await client.connect()
        delegate = HeartRateDelegate()
        await client.start_notify(CHAR_UUID, delegate.handleNotification)
        return client
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

async def main():
    device_address = await scan_for_devices()
    if device_address:
        client = await connect_to_device(device_address)    
        if client:
            try:
                # Loop for EMG data sending
                while True:
                    emg_value = chan.value
                    voltage = emg_value * (4096 / 32767) / 1000
                    if voltage > 1.4 and emg_value > 11900 and voltage < 3:
                        print('EMG:', emg_value)
                        print('Voltage:', voltage)
                        send_emg_data(emg_value, voltage)  # Send EMG data
                    await asyncio.sleep(0.1)  # Use asyncio.sleep for non-blocking wait

            except KeyboardInterrupt:
                print("Stopped")
                await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

