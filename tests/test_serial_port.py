"""The bus over a real serial device: pyserial on one end of a pseudo
terminal, a stand-in sensor on the other."""

import os
import threading

import pytest

import agrinovo
from conftest import with_crc

pty = pytest.importorskip("pty")


class Line:
    """Answers each 8-byte request on the other end of a pseudo terminal."""

    def __init__(self, answers):
        self.master, slave = pty.openpty()
        self.path = os.ttyname(slave)
        self._slave = slave
        self.requests = []
        self._answers = list(answers)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        for answer in self._answers:
            request = b""
            while len(request) < 8:
                request += os.read(self.master, 8 - len(request))
            self.requests.append(request)
            if answer:
                os.write(self.master, answer)

    def close(self):
        self._thread.join(timeout=2)
        os.close(self.master)
        os.close(self._slave)


def test_read_over_a_serial_device():
    line = Line([with_crc("01 03 04 01 E6 FF 9F")])
    try:
        with agrinovo.Bus(line.path, timeout=1.0) as bus:
            reading = agrinovo.THS100(bus).read()
    finally:
        line.close()
    assert reading == (-9.7, 48.6)
    assert line.requests == [with_crc("01 03 00 00 00 02")]


def test_silence_then_an_answer_over_a_serial_device():
    line = Line([b"", with_crc("01 03 02 02 AE")])
    try:
        with agrinovo.Bus(line.path, timeout=0.2) as bus:
            assert agrinovo.PH100(bus).read().ph == 6.86
    finally:
        line.close()
    assert len(line.requests) == 2


def test_no_reply_over_a_serial_device():
    line = Line([b""])
    try:
        with agrinovo.Bus(line.path, timeout=0.2, retries=0) as bus:
            with pytest.raises(agrinovo.NoReply):
                agrinovo.PH100(bus).read()
    finally:
        line.close()
