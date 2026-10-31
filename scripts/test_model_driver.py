"""Host-only checks: signed register I/O, stale done, busy and timeout."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'src/ps/replay_models.py'
spec = importlib.util.spec_from_file_location('driver', path)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
OFFSETS = {'control': 0, 'return': 16, 'input': 256, 'output': 32}


class FakeIP:
    def __init__(self, control):
        self.control = iter(control)
        self.writes = []

    def read(self, offset):
        if offset == 0:
            return next(self.control)
        return {16: 3, 32: 0xffffffff, 36: 0x80000000}[offset]

    def write(self, offset, value):
        self.writes.append((offset, value))


class DriverTest(unittest.TestCase):
    def test_stale_done_and_signed(self):
        ip = FakeIP([6, 0, 2])
        self.assertEqual(driver.infer(ip, OFFSETS, [-1, 32767], 2), (3, [-1, -2147483648]))
        self.assertEqual(ip.writes, [(256, 0xffffffff), (260, 32767), (0, 1)])

    def test_busy(self):
        ip = FakeIP([0])
        with self.assertRaises(RuntimeError):
            driver.infer(ip, OFFSETS, [1], 1)
        self.assertEqual(ip.writes, [])

    def test_timeout(self):
        ip = FakeIP([4, 0])
        with self.assertRaises(TimeoutError):
            driver.infer(ip, OFFSETS, [1], 1, timeout=0)


if __name__ == '__main__':
    unittest.main()
