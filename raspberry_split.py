import requests
import asyncio
import csv
import matplotlib.pyplot as plt
from collections import deque
from datetime import datetime
from adafruit_mlx90614 import MLX90614
import board
import busio
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

# Initialize plot
plt.ion()
fig, ax = plt.subplots()
y_data = deque([1.5] * 100, maxlen=100)  # Store the latest 100 readings
line, = ax.plot(y_data)
ax.set_ylim([1.4, 2])  # Adjust based on expected voltage range

# Open CSV file to log data
csv_file = open("emg_data.csv", mode="w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Timestamp", "Voltage (V)"])  # Write header

async def send_heart_rate_and_temp(heart_rate):
    temperature = round(mlx.object_temperature, 2)
    data = {"BPM": heart_rate, "Temp": temperature}
    current_time = datetime.now().strftime("%A, %B %d %H:%M:%S")
    url = f"{DATABASE_URL}/Data/{current_time}.json?auth={API_KEY}"

    try:
        response = requests.put(url, json=data)
        if response.status_code == 200:
            print("Heart rate and temperature sent successfully")
    except Exception as e:
        print(f"Failed to send heart rate/temperature data, Error: {e}")

async def handle_heart_rate_notification(characteristic, data):
    heart_rate = data[1] if len(data) > 1 else data[0]
    print(f"Heart Rate: {heart_rate} bpm")
    await send_heart_rate_and_temp(heart_rate)

async def monitor_emg():
    # Continuously reads EMG data without delay
    while True:
        emg_value = chan.value
        voltage = emg_value * (4.096 / 32767)

        # Update plot and data
        y_data.append(voltage)
        line.set_ydata(y_data)
        ax.draw_artist(line)
        fig.canvas.blit(ax.bbox)
        fig.canvas.flush_events()
        
        
        # Log EMG data to CSV with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        csv_writer.writerow([timestamp, round(voltage, 3)])
        csv_file.flush()  # Ensure data is written to file immediately


        await asyncio.sleep(0.1)

async def scan_for_devices():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=10.0)
    for device in devices:
        if SERVICE_UUID in device.metadata["uuids"]:
            print(f"Found target device: {device.address}")
            return device.address
    return None

async def connect_to_device(address):
    print(f"Connecting to device {address}...")
    try:
        client = BleakClient(address)
        await client.connect()
        await client.start_notify(CHAR_UUID, handle_heart_rate_notification)
        return client
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

async def monitor_heart_rate(client):
    while client.is_connected:
        await asyncio.sleep(1)

async def main():
    device_address = await scan_for_devices()
    if device_address:
        client = await connect_to_device(device_address)
        if client:
            try:
                await asyncio.gather(
                    monitor_emg(),
                    monitor_heart_rate(client)
                )
            except KeyboardInterrupt:
                print("Stopped")
            finally:
                await client.disconnect()
                csv_file.close()  # Close CSV file on exit

if __name__ == "__main__":
    asyncio.run(main())

