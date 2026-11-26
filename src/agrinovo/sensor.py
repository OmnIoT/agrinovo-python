"""Base class of every Agrinovo sensor: reads a block of registers and decodes
it into values with a small table. The classes in ``sensors.py`` add named
values and commands on top; GenericSensor takes a table of your own.
"""

from __future__ import annotations

import math
import struct
from typing import Any, ClassVar, Dict, Iterable, NamedTuple, Sequence, Tuple, Union

from .bus import BadRequest, Bus, _check_range

__all__ = ["Field", "Sensor", "GenericSensor", "TYPES"]

#: How a value is stored in the registers, and the number of registers it
#: spans. The letters give the order in which the four bytes of a 32-bit value
#: arrive, A being the most significant.
TYPES: Dict[str, int] = {
    "u16": 1,  # one register, unsigned
    "i16": 1,  # one register, signed
    "sm16": 1,  # one register, top bit is the sign, the rest the size
    "u16_dec": 2,  # one register, then a register holding its decimal places
    "u32_abcd": 2,  # two registers, unsigned
    "u32_cdab": 2,  # two registers, unsigned, low word first
    "f32_abcd": 2,  # float
    "f32_cdab": 2,  # float, low word first
    "f32_dcba": 2,  # float, least significant byte first
}


class Field(NamedTuple):
    """One value in a register table."""

    name: str  #: the name the value is returned under
    offset: int  #: register offset from the first register read
    type: str  #: one of TYPES
    scale: float = 1.0  #: the raw value is multiplied by this
    unit: str = ""
    label: str = ""
    decimals: int = 2  #: decimal places worth printing


def _decode(data: bytes, kind: str) -> float:
    if kind == "u16":
        return float(struct.unpack_from(">H", data)[0])
    if kind == "i16":
        return float(struct.unpack_from(">h", data)[0])
    if kind == "sm16":
        raw = struct.unpack_from(">H", data)[0]
        return float(-(raw & 0x7FFF) if raw & 0x8000 else raw)
    if kind == "u16_dec":
        raw, decimals = struct.unpack_from(">HH", data)
        return raw / 10**decimals if decimals <= 9 else math.nan
    if kind == "u32_abcd":
        return float(struct.unpack_from(">I", data)[0])
    if kind == "u32_cdab":
        return float(struct.unpack(">I", data[2:4] + data[0:2])[0])
    if kind == "f32_abcd":
        return struct.unpack_from(">f", data)[0]
    if kind == "f32_cdab":
        return struct.unpack(">f", data[2:4] + data[0:2])[0]
    if kind == "f32_dcba":
        return struct.unpack_from("<f", data)[0]
    raise BadRequest("unknown storage type %r" % kind)


def _scaled(value: float, scale: float) -> float:
    if scale == 1:
        return value
    # 486 * 0.1 is 48.6 only to fifteen digits; dividing by 10 gives 48.6.
    inverse = 1.0 / scale
    if scale < 1 and abs(inverse - round(inverse)) < 1e-9:
        return value / round(inverse)
    return value * scale


def _decode_fields(data: bytes, count: int, fields: Iterable[Field]) -> Tuple[float, ...]:
    values = []
    for field in fields:
        if field.offset + TYPES[field.type] > count:
            values.append(math.nan)  # outside the block read
        else:
            values.append(_scaled(_decode(data[2 * field.offset :], field.type), field.scale))
    return tuple(values)


def _raw(name: str, value: Union[int, float], low: int, high: int, scale: float = 0) -> int:
    """A command argument as the 16-bit number that goes in the register."""
    if scale:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
            raise BadRequest("%s must be a number, not %r" % (name, value))
        # Scaled and rounded; a negative value goes out as two's complement.
        number = int(value * scale + (-0.5 if value < 0 else 0.5))
        if not low <= number <= high:
            raise BadRequest("%s must be %g to %g, not %g" % (name, low / scale, high / scale, value))
    else:
        number = _check_range(name, value, low, high)  # type: ignore[arg-type]
    return number & 0xFFFF


def _low_byte_first(value: int) -> int:
    return ((value & 0xFF) << 8) | (value >> 8)


class Sensor:
    """What every sensor class can do.

    ``address`` is the Modbus address this object talks to. Assigning to it
    only changes the object; it does not reprogram the sensor.
    """

    MODEL: ClassVar[str] = ""
    NAME: ClassVar[str] = ""
    DEFAULT_ADDRESS: ClassVar[int] = 1
    BAUDRATE: ClassVar[int] = 9600
    FUNCTION: ClassVar[int] = 0x03
    START: ClassVar[int] = 0x0000
    COUNT: ClassVar[int] = 1
    FIELDS: ClassVar[Tuple[Field, ...]] = ()
    Reading: ClassVar[Any] = tuple

    def __init__(self, bus: Bus, address: Union[int, None] = None) -> None:
        self.bus = bus
        self.address = self.DEFAULT_ADDRESS if address is None else address

    def __repr__(self) -> str:
        return "%s(address=%d)" % (type(self).__name__, self.address)

    def read(self) -> Any:
        """Reads the sensor and returns its values in engineering units.

        Raises a subclass of :class:`agrinovo.AgrinovoError` when the sensor
        did not answer correctly.
        """
        data = self.bus.read_registers(self.address, self.FUNCTION, self.START, self.COUNT)
        return self.Reading(*_decode_fields(data, self.COUNT, self.FIELDS))

    def units(self) -> Dict[str, str]:
        """The unit of each value, by name."""
        return {field.name: field.unit for field in self.FIELDS}

    # Direct register access, for settings a class has no method for.

    def read_register(self, register: int, function: int = 0x03) -> int:
        """Reads one register as an unsigned 16-bit number."""
        data = self.bus.read_registers(self.address, function, register, 1)
        return (data[0] << 8) | data[1]

    def write_register(self, register: int, value: int, function: int = 0x06) -> None:
        """Writes one register."""
        self.bus.write_register(self.address, register, value, function)

    def _write_address(self, register: int, value: int, function: int, new_address: int) -> None:
        # Writes the register that holds the sensor's address, then follows it.
        self.bus.write_register(self.address, register, value, function, new_address)
        self.address = new_address


FieldLike = Union[Field, Sequence[Any]]


class GenericSensor(Sensor):
    """A sensor described by your own table, for a model this package has no
    class for yet.

    ``fields`` lists the values, each as ``(name, offset, type)`` or
    ``(name, offset, type, scale)``: the register offset from ``start``, how
    the value is stored (one of ``agrinovo.TYPES``) and what to multiply it by.
    :meth:`read` returns a dict keyed by those names. A value that lies outside
    the registers read comes back as NaN.
    """

    def __init__(
        self, bus: Bus, address: int, function: int, start: int, count: int, fields: Iterable[FieldLike]
    ) -> None:
        super().__init__(bus, address)
        table = tuple(field if isinstance(field, Field) else Field(*field) for field in fields)
        names = [field.name for field in table]
        if len(set(names)) != len(names):
            raise BadRequest("two values share a name")
        for field in table:
            if field.type not in TYPES:
                raise BadRequest("%s: unknown storage type %r" % (field.name, field.type))
        # These shadow the class attributes a generated sensor class carries.
        self.FUNCTION = function  # type: ignore[misc]
        self.START = start  # type: ignore[misc]
        self.COUNT = count  # type: ignore[misc]
        self.FIELDS = table  # type: ignore[misc]

    def read(self) -> Dict[str, float]:
        data = self.bus.read_registers(self.address, self.FUNCTION, self.START, self.COUNT)
        values = _decode_fields(data, self.COUNT, self.FIELDS)
        return {field.name: value for field, value in zip(self.FIELDS, values)}
