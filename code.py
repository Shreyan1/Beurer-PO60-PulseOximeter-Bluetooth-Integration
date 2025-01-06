"""
[As per 2024 - 2025 device transmission protocols]
This code is for reading SPO2 and Pulse Rate data from PO60- Beurer Pulse Oximeter,
using BLE communication using the bleak library.

It includes the following functionalities:
1. Discover the BLE device and connect to it based on the device address.
2. Start receiving notifications from the device and parse the received data.
3. Extract SPO2 and Pulse Rate values from the received data packets.
4. Log the received data and parsed measurements.
5. Display the latest measurement data including SPO2 and Pulse Rate values.
"""

import asyncio  # Importing asyncio for asynchronous programming
from bleak import BleakClient  # Importing BleakClient for BLE communication
import logging  # Importing logging for logging messages
import os  # Importing os for operating system related functions
from datetime import datetime  # Importing datetime for date and time operations

# Logging setup
os.makedirs("logs", exist_ok=True)  # Create a directory for logs if it doesn't exist
log_file = f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"  # Generate a log file name with the current timestamp
logging.basicConfig(level=logging.DEBUG,  # Set logging level to DEBUG
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Define log message format
                    handlers=[logging.FileHandler(log_file), logging.StreamHandler()])  # Log to file and console

WRITE_UUID = "0000FF01-0000-1000-8000-00805f9b34fb"  # UUID for writing data to the BLE device
NOTIFY_UUID = "0000FF02-0000-1000-8000-00805f9b34fb"  # UUID for receiving notifications from the BLE device
measurements = []  # List to store parsed measurement data
raw_data = []  # List to store raw data received from notifications

MIN_PACKET_LENGTH = 23  # Minimum length for valid measurement data

def parse(data):
    if len(data) < MIN_PACKET_LENGTH or data[0] != 0xe9:  # Check if data is valid
        logging.warning("Invalid or incomplete data packet received.")  # Log a warning if data is invalid
        return None  # Return None for invalid data
    return {
        'packet': data[1] & 0x0F,  # Extract packet number
        'end_time': extract_time(data[8:14]),  # Extract end time from data
        'spo2': {k: data[i] & 0x7F for k, i in zip(['max', 'min', 'avg'], range(17, 20))}  # Extract SpO2 values
    }

def extract_time(data):
    return {'year': 2000 + (data[0] & 0x7F), 
            'month': data[1] & 0x0F,  # Extract year and month
            'day': data[2] & 0x1F, 
            'hour': data[3] & 0x1F,  # Extract day and hour
            'minute': data[4] & 0x3F, 
            'second': data[5] & 0x3F}  # Extract minute and second

async def handle_notification(sender, data):
    hex_data = data.hex()  # Convert data to hexadecimal string
    logging.debug(f"Received: {hex_data}")  # Log the received data
    raw_data.append(hex_data)  # Append raw data to the list

    # Note that e9 is the header for the measurement data packet
    if data[0] == 0xe9:  # Check if the data is a measurement packet
        measurement = parse(data)  # Parse the data
        if measurement:  # If parsing is successful
            measurements.append(measurement)  # Append the measurement to the list
    elif measurements and len(data) >= 3:  # Check if there are measurements and data length is sufficient
        # Append PR values from subsequent notifications
        try:
            measurements[-1]['pr'] = {
                'max': data[0] & 0x7F,  # Extract max PR value
                'min': data[1] & 0x7F,  # Extract min PR value
                'avg': data[2] & 0x7F  # Extract avg PR value
            }
            logging.info(f"Pulse Rate updated: {measurements[-1]['pr']}")  # Log the updated PR values
        except IndexError:
            logging.warning("PR values incomplete in notification.")  # Log a warning if PR values are incomplete

async def main():
    address = "XX:XX:XX:XX:XX:XX"  # Enter your BLE device address
    async with BleakClient(address) as client:  # Connect to the BLE device
        logging.info("Connected")  # Log connection success
        await client.start_notify(NOTIFY_UUID, handle_notification)  # Start receiving notifications
        await client.write_gatt_char(WRITE_UUID, bytearray([0x90, 0x05, 0x15]))  # Write command to BLE device
        await asyncio.sleep(0.5)  # Wait for 0.5 seconds
        await client.write_gatt_char(WRITE_UUID, bytearray([0x99, 0x00, 0x19]))  # Write another command to BLE device
        await asyncio.sleep(5)  # Wait for 5 seconds
        if measurements:  # If there are measurements
            latest = max(measurements, key=lambda x: x['end_time'])  # Get the latest measurement
            logging.info(f"Latest Measurement #{latest['packet']} - SpO2: {latest['spo2']} - PR: {latest.get('pr', 'N/A')}")  # Log the latest measurement
        else:
            logging.info("No measurements received.")  # Log if no measurements are received

if __name__ == "__main__":
    asyncio.run(main())  # Run the main function
