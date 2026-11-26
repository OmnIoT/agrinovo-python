"""Read Agrinovo water, soil and air sensors over RS485 Modbus RTU.

    import agrinovo

    with agrinovo.Bus("/dev/ttyUSB0") as bus:
        probe = agrinovo.NO3100(bus)
        print(probe.read())
"""

from .bus import (
    MAX_REGISTERS,
    AgrinovoError,
    BadCRC,
    BadReply,
    BadRequest,
    Bus,
    NoReply,
    SensorRefused,
    crc16,
    scan,
)
from .sensor import TYPES, Field, GenericSensor, Sensor
from .sensors import *  # noqa: F401,F403  one class per sensor, generated
from .sensors import SENSORS
from .sensors import __all__ as _sensor_classes

__version__ = "0.9.0"

__all__ = [
    "Bus",
    "scan",
    "crc16",
    "Sensor",
    "GenericSensor",
    "Field",
    "TYPES",
    "SENSORS",
    "MAX_REGISTERS",
    "AgrinovoError",
    "NoReply",
    "BadCRC",
    "BadReply",
    "SensorRefused",
    "BadRequest",
    *_sensor_classes,
]
