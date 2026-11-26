"""Test helpers: a serial port that plays back scripted replies."""

import json
from collections import deque
from pathlib import Path

import pytest

from agrinovo import crc16

DEFINITIONS = json.loads((Path(__file__).parent / "definitions.json").read_text(encoding="utf-8"))


def hexbytes(text):
    return bytes(int(part, 16) for part in text.split())


def with_crc(frame):
    frame = hexbytes(frame) if isinstance(frame, str) else bytes(frame)
    crc = crc16(frame)
    return frame + bytes((crc & 0xFF, crc >> 8))


class FakeSerial:
    """Stands in for serial.Serial. Each request (ended by flush) releases the
    next scripted reply. With ``confirm_writes`` set, a write request gets the
    reply a sensor would send. Nothing here sleeps: a read that finds no bytes
    returns at once, as a real port does when its timeout runs out.
    """

    def __init__(self, confirm_writes=False):
        self.written = b""
        self.replies = deque()
        self.confirm_writes = confirm_writes
        self.requests = 0
        self.timeout = None
        self.closed = False
        self._incoming = b""
        self._pending = b""

    def reply(self, frame):
        self.replies.append(hexbytes(frame) if isinstance(frame, str) else bytes(frame))

    def write(self, data):
        self.written += data
        self._pending += data
        return len(data)

    def flush(self):
        self.requests += 1
        answer = b""
        if self.confirm_writes and len(self._pending) >= 8 and self._pending[1] in (0x06, 0x10):
            answer = with_crc(self._pending[:6])
        elif self.replies:
            answer = self.replies.popleft()
        self._incoming += answer
        self._pending = b""

    def reset_input_buffer(self):
        self._incoming = b""

    def read(self, size=1):
        data, self._incoming = self._incoming[:size], self._incoming[size:]
        return data

    def close(self):
        self.closed = True


@pytest.fixture
def serial_port():
    return FakeSerial()
