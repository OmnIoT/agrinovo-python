"""RS485 Modbus RTU master used by every Agrinovo sensor class.

One Bus per RS485 line. Several sensors can share it, each with its own
Modbus address.
"""

from __future__ import annotations

import sys
import time
from typing import Any, Callable, Iterable, List, Optional, Union

__all__ = [
    "Bus",
    "scan",
    "crc16",
    "AgrinovoError",
    "NoReply",
    "BadCRC",
    "BadReply",
    "SensorRefused",
    "BadRequest",
    "MAX_REGISTERS",
]

#: Largest number of registers one request may read (the Modbus limit).
MAX_REGISTERS = 125

_EXCEPTION_TEXT = {
    1: "function not supported",
    2: "register not available",
    3: "value not accepted",
    4: "sensor fault",
    6: "sensor busy",
}


class AgrinovoError(Exception):
    """Base class of every error this package raises."""


class NoReply(AgrinovoError):
    """Nothing came back before the timeout."""

    def __init__(self, message: str = "no reply from the sensor") -> None:
        super().__init__(message)


class BadCRC(AgrinovoError):
    """The reply failed its checksum."""

    def __init__(self, message: str = "the reply failed its checksum") -> None:
        super().__init__(message)


class BadReply(AgrinovoError):
    """The reply was cut short or does not match the request."""

    def __init__(self, message: str = "unexpected reply") -> None:
        super().__init__(message)


class SensorRefused(AgrinovoError):
    """The sensor refused the request. ``code`` is the Modbus exception code."""

    def __init__(self, code: int) -> None:
        self.code = code
        detail = _EXCEPTION_TEXT.get(code)
        text = "the sensor refused the request (Modbus exception %d" % code
        super().__init__(text + (", %s)" % detail if detail else ")"))


class BadRequest(AgrinovoError, ValueError):
    """The request itself is not valid, so nothing was sent."""


def crc16(frame: bytes) -> int:
    """The Modbus RTU checksum of ``frame``. It goes on the wire low byte first."""
    crc = 0xFFFF
    for byte in frame:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def _with_crc(frame: bytes) -> bytes:
    crc = crc16(frame)
    return frame + bytes((crc & 0xFF, crc >> 8))


def _hex(frame: bytes) -> str:
    return " ".join("%02X" % byte for byte in frame)


def _check_range(name: str, value: int, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise BadRequest("%s must be a whole number, not %r" % (name, value))
    if not low <= value <= high:
        raise BadRequest("%s must be %d to %d, not %d" % (name, low, high, value))
    return value


class Bus:
    """An RS485 line with Agrinovo sensors on it.

    port
        The serial port of the RS485 adapter, for example ``"/dev/ttyUSB0"`` or
        ``"COM3"``. It is opened at 8N1. A port you opened yourself (any object
        with pyserial's ``read``, ``write`` and ``timeout``) is accepted too and
        is then left open by :meth:`close`.
    baudrate
        9600 unless you changed the sensor's own setting.
    timeout
        How long to wait for a reply, in seconds.
    retries
        How many times a failed request is sent again.
    debug
        ``True`` prints every frame sent and received to stderr. A function
        receives each line instead, for example ``debug=logging.debug``.
    frame_gap
        Quiet time kept between two frames, in seconds. The default suits 9600
        baud and faster. Use 0.01 at 4800, 0.02 at 2400, 0.04 at 1200.
    """

    def __init__(
        self,
        port: Union[str, Any],
        baudrate: int = 9600,
        timeout: float = 1.0,
        retries: int = 1,
        debug: Union[bool, Callable[[str], Any], None] = None,
        frame_gap: float = 0.005,
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self.frame_gap = frame_gap
        self.debug = debug
        self._last_activity = 0.0
        if isinstance(port, str):
            import serial  # pyserial

            self._serial = serial.Serial(port, baudrate=baudrate, bytesize=8, parity="N", stopbits=1)
            self._owns_port = True
        else:
            self._serial = port
            self._owns_port = False

    # ------------------------------------------------------------ housekeeping

    def close(self) -> None:
        """Closes the serial port, if this bus opened it."""
        if self._owns_port:
            self._serial.close()

    def __enter__(self) -> "Bus":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ---------------------------------------------------------------- requests

    def read_registers(self, address: int, function: int, start: int, count: int) -> bytes:
        """Reads ``count`` registers with function 0x03 or 0x04.

        Returns two bytes per register, in the order the sensor sent them.
        """
        _check_range("address", address, 0, 255)
        _check_range("start", start, 0, 0xFFFF)
        if function not in (0x03, 0x04):
            raise BadRequest("registers are read with function 0x03 or 0x04, not 0x%02X" % function)
        _check_range("count", count, 1, MAX_REGISTERS)
        request = _with_crc(bytes((address, function, start >> 8, start & 0xFF, count >> 8, count & 0xFF)))
        reply = self._transfer(request, 5 + 2 * count, 0)
        if reply[2] != 2 * count:
            raise BadReply()
        return reply[3 : 3 + 2 * count]

    def write_register(
        self, address: int, register: int, value: int, function: int = 0x06, reply_address: int = 0
    ) -> None:
        """Writes one register with function 0x06, or with 0x10 when asked.

        ``reply_address`` is a second address the reply may come from, used
        when the write changes the sensor's own address.
        """
        _check_range("address", address, 0, 255)
        _check_range("register", register, 0, 0xFFFF)
        _check_range("value", value, 0, 0xFFFF)
        head = bytes((address, function, register >> 8, register & 0xFF))
        if function == 0x06:
            request = head + bytes((value >> 8, value & 0xFF))
        elif function == 0x10:
            # one register, two data bytes
            request = head + bytes((0x00, 0x01, 0x02, value >> 8, value & 0xFF))
        else:
            raise BadRequest("a register is written with function 0x06 or 0x10, not 0x%02X" % function)
        request = _with_crc(request)
        reply = self._transfer(request, 8, reply_address)
        if reply[2:4] != request[2:4]:
            raise BadReply()

    def ping(self, address: int) -> bool:
        """True when a device answers at this address. Used to scan a line."""
        try:
            self.read_registers(address, 0x03, 0x0000, 1)
        except SensorRefused:
            return True  # a refusal is still an answer: something lives here
        except BadRequest:
            raise
        except AgrinovoError:
            return False
        return True

    # ---------------------------------------------------------------- transfer

    def _transfer(self, request: bytes, reply_length: int, reply_address: int) -> bytes:
        error: AgrinovoError = NoReply()
        for _ in range(max(0, int(self.retries)) + 1):
            try:
                return self._transfer_once(request, reply_length, reply_address)
            except SensorRefused:
                raise  # the sensor heard us; asking again changes nothing
            except AgrinovoError as caught:
                error = caught
        raise error

    def _transfer_once(self, request: bytes, reply_length: int, reply_address: int) -> bytes:
        port = self._serial
        # Keep the line quiet between frames, then drop anything left over.
        wait = self._last_activity + self.frame_gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        port.reset_input_buffer()

        port.write(request)
        port.flush()
        self._debug(">", request)

        # An address above 247 is a broadcast query: the sensor answers with the
        # broadcast address or with its own, so any first byte is accepted.
        address = request[0]
        any_address = address > 247
        deadline = time.monotonic() + self.timeout
        reply = bytearray()
        wanted = 5  # the shortest reply, and the length of a refusal
        while len(reply) < wanted:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            port.timeout = remaining
            chunk = port.read(wanted - len(reply))
            for value in chunk:
                # Skip noise ahead of the frame, common when the adapter turns around.
                if not reply and not any_address and value != address and not (
                    reply_address and value == reply_address
                ):
                    continue
                reply.append(value)
            if len(reply) == 5 and not reply[1] & 0x80:
                wanted = reply_length
        self._last_activity = time.monotonic()
        self._debug("<", reply)

        if not reply:
            raise NoReply()
        if len(reply) < wanted:
            raise BadReply()
        if crc16(reply[:-2]) != reply[-2] | (reply[-1] << 8):
            raise BadCRC()
        if reply[1] == request[1] | 0x80:
            raise SensorRefused(reply[2])
        if reply[1] != request[1]:
            raise BadReply()
        return bytes(reply)

    def _debug(self, direction: str, frame: bytes) -> None:
        if not self.debug:
            return
        line = "%s %s" % (direction, _hex(frame)) if frame else direction
        if callable(self.debug):
            self.debug(line)
        else:
            print(line, file=sys.stderr)


def scan(
    bus: Bus,
    addresses: Optional[Iterable[int]] = None,
    timeout: float = 0.1,
    found: Optional[Callable[[int], Any]] = None,
) -> List[int]:
    """Finds every sensor on the line and returns the addresses that answer.

    Use it when a sensor does not answer at the address you expect. All 247
    addresses take about 25 seconds on an empty line; pass ``addresses`` to
    look at fewer, and ``found`` to be told about each one as it turns up.
    """
    saved = (bus.timeout, bus.retries)
    bus.timeout, bus.retries = timeout, 0  # a sensor answers within a few milliseconds
    answered = []
    try:
        for address in range(1, 248) if addresses is None else addresses:
            if bus.ping(address):
                answered.append(address)
                if found:
                    found(address)
    finally:
        bus.timeout, bus.retries = saved
    return answered
