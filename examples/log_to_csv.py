"""Logs a sensor to a CSV file once a minute, with a timestamp.

This script uses the nitrate probe. Change the class to match your sensor.
A reading that fails is printed and skipped, so the log keeps running.

    python log_to_csv.py /dev/ttyUSB0 nitrate.csv
"""

import csv
import os
import sys
import time
from datetime import datetime

import agrinovo

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
FILE = sys.argv[2] if len(sys.argv) > 2 else "readings.csv"
INTERVAL = 60  # seconds

with agrinovo.Bus(PORT) as bus, open(FILE, "a", newline="") as file:
    probe = agrinovo.NO3100(bus)
    writer = csv.writer(file)
    if os.path.getsize(FILE) == 0:
        writer.writerow(["time"] + [f"{name} ({unit})" for name, unit in probe.units().items()])
    while True:
        try:
            reading = probe.read()
            writer.writerow([datetime.now().isoformat(timespec="seconds"), *reading])
            file.flush()
        except agrinovo.AgrinovoError as error:
            print(error)
        time.sleep(INTERVAL)
