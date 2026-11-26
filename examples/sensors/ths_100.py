"""Agrinovo THS-100 temperature and humidity sensor.

Prints temperature and humidity every 5 seconds.

Sensor cable
  Red     supply +, 5-28 V DC
  Black   supply ground
  Yellow  RS485 A
  Green   RS485 B

The computer talks to the sensor through a USB to RS485 adapter: A to A,
B to B. Run this file with the adapter's port, for example:

    python ths_100.py /dev/ttyUSB0

https://agrinovo.io/products/sensors/environmental/ths-100-rs485-temperature-humidity-sensor/
"""

import sys
import time

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

with agrinovo.Bus(PORT, baudrate=9600) as bus:
    sensor = agrinovo.THS100(bus)  # Modbus address 1
    while True:
        try:
            reading = sensor.read()
            print(f"Temperature: {reading.temperature:.1f} °C")
            print(f"Humidity: {reading.humidity:.1f} % RH")
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(5)
