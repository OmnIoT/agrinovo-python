"""Agrinovo GF-201-CH4 combustible gas detector.

Prints combustible gas every 5 seconds.

Sensor terminals
  24V+  supply +, 12-30 V DC
  GND   supply ground
  A+    RS485 A
  B-    RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python gf_201_ch4.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/environmental/gf-201-ch4-combustible-gas-sensor/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    sensor = agrinovo.GF201CH4(bus)  # Modbus address 1
    while True:
        try:
            reading = sensor.read()
            print(f"Combustible gas: {reading.combustible_gas:.1f} %LEL")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
