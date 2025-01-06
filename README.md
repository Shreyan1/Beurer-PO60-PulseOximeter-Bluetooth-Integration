[As per 2024 - 2025 device transmission protocols]
This code is for reading SPO2 and Pulse Rate data from PO60- Beurer Pulse Oximeter,
using BLE communication using the bleak library.

It includes the following functionalities:
1. Discover the BLE device and connect to it based on the device address.
2. Start receiving notifications from the device and parse the received data.
3. Extract SPO2 and Pulse Rate values from the received data packets.
4. Log the received data and parsed measurements.
5. Display the latest measurement data including SPO2 and Pulse Rate values.

Pulse Rate will be added
