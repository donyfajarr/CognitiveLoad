import requests
import asyncio
from adafruit_mlx90614 import MLX90614
import board
import busio
from datetime import datetime
from bleak import BleakScanner, BleakClient
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Firebase Configuration
API_KEY = "AIzaSyDcmVBTt3zT0eJUf97tFkX50u9KyqHzlo"
DATABASE_URL = "https://cognitive-load-default-rtdb.asia-southeast1.firebasedatabase.app"
SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "00002A37-0000-1000-8000-00805F9B34FB"

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
mlx = MLX90614(i2c)
adc = ADS.ADS1115(i2c, data_rate=860, gain=1)
chan = AnalogIn(adc, ADS.P0)

async def send_heart_rate_and_temp(heart_rate):
    # Read the temperature from the MLX90614 sensor
    temperature = round(mlx.object_temperature, 2)
    
    # Data payload for heart rate and temperature
    data = {"BPM": heart_rate, "Temp": temperature}
    current_time = datetime.now().strftime("%A, %B %d %H:%M:%S")
    url = f"{DATABASE_URL}/Data/{current_time}.json?auth={API_KEY}"

    try:
        # Send data to Firebase
        response = requests.put(url, json=data)
        if response.status_code == 200:
            print("Heart rate and temperature sent successfully")
    except Exception as e:
        print(f"Failed to send heart rate/temperature data, Error: {e}")

async def handle_heart_rate_notification(characteristic, data):
    # Parse heart rate value
    heart_rate = data[1] if len(data) > 1 else data[0]
    print(f"Heart Rate: {heart_rate} bpm")
    
    # Send the heart rate and temperature data to Firebase
    await send_heart_rate_and_temp(heart_rate)

async def send_emg_data(emg_value, voltage):
    current_time = datetime.now().strftime("%A, %B %d %H:%M:%S")
    data = {"EMG_Value": emg_value, "Voltage": voltage}
    url = f"{DATABASE_URL}/EMG_Data/{current_time}.json?auth={API_KEY}"

    try:
        response = requests.put(url, json=data)
        if response.status_code == 200:
            print("EMG data sent successfully")
    except Exception as e:
        print(f"Failed to send EMG data, Error: {e}")

async def scan_for_devices():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=10.0)

    for device in devices:
        print(f"Device {device.address} ({device.rssi} dBm)")
        if SERVICE_UUID in device.metadata["uuids"]:
            print(f"Found target device: {device.address}")
            return device.address
    return None

async def connect_to_device(address):
    print(f"Connecting to device {address}...")
    try:
        client = BleakClient(address)
        await client.connect()

        # Start heart rate notification handler
        await client.start_notify(CHAR_UUID, handle_heart_rate_notification)
        return client
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

async def monitor_emg():
    # Continuously reads EMG data without delay
    while True:
        emg_value = chan.value
        voltage = emg_value * (4.096 / 32767)
        if 1.4 <= voltage <= 3.3:
            print('Voltage:', voltage)
            await send_emg_data(emg_value, round(voltage, 2))
        await asyncio.sleep(0.1)  # Small delay for stability

async def monitor_heart_rate(client):
    # Continuously monitor heart rate as long as the client is connected
    while client.is_connected:
        await asyncio.sleep(1)  # No need to add any additional code as notifications will be handled automatically

async def main():
    device_address = await scan_for_devices()
    if device_address:
        client = await connect_to_device(device_address)
        if client:
            try:
                # Run EMG monitoring and handle heart rate notifications in parallel
                await asyncio.gather(
                    monitor_emg(),
                    monitor_heart_rate(client)
                )
            except KeyboardInterrupt:
                print("Stopped")
            finally:
                await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

