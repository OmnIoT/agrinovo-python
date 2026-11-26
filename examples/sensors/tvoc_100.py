"""Agrinovo TVOC-100 TVOC air quality sensor.

Prints TVOC and CO2 equivalent every 5 seconds.

Sensor terminals
  V+   supply +, 5-12 V DC
  GND  supply ground
  A+   RS485 A
  B-   RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python tvoc_100.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/environmental/tvoc-100-rs485-air-quality-sensor/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    sensor = agrinovo.TVOC100(bus)  # Modbus address 1
    while True:
        try:
            reading = sensor.read()
            print(f"TVOC: {reading.tvoc:.0f} ppb")
            print(f"CO2 equivalent: {reading.co2_equivalent:.0f} ppm")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
