# tests/unit/test_tee.py
import io
import os
import sys
import unittest

# Ensure src/ is on sys.path when running via discover
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from arc.tee import Tee  # noqa: E402


class TestTee(unittest.TestCase):
    def test_write_writes_to_all_streams(self):
        buf1 = io.StringIO()
        buf2 = io.StringIO()

        tee = Tee(buf1, buf2)
        tee.write("hello")
        tee.write(" world")

        self.assertEqual(buf1.getvalue(), "hello world")
        self.assertEqual(buf2.getvalue(), "hello world")

    def test_flush_flushes_all_streams(self):
        class DummyStream:
            def __init__(self):
                self.flushed = False
                self.data = ""

            def write(self, s):
                self.data += s

            def flush(self):
                self.flushed = True

        s1 = DummyStream()
        s2 = DummyStream()

        tee = Tee(s1, s2)
        tee.write("x")
        tee.flush()

        self.assertTrue(s1.flushed)
        self.assertTrue(s2.flushed)
        self.assertEqual(s1.data, "x")
        self.assertEqual(s2.data, "x")


if __name__ == "__main__":
    unittest.main()
