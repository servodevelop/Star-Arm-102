"""Native SDK tests against PTYs only; no physical serial device is opened."""
import os
import select
import struct
import threading
import unittest

from motorbridge_smart_servo import FashionStarServo, ServoBusError


def packet(code, params):
    frame = bytes((0x12, 0x4c, code, len(params))) + params
    return frame + bytes((sum(frame) & 255,))


class DampingTransportTests(unittest.TestCase):
    def setUp(self):
        self.master, self.slave = os.openpty()
        self.bus = FashionStarServo(os.ttyname(self.slave))

    def tearDown(self):
        self.bus.close()
        os.close(self.master)
        os.close(self.slave)

    def receive(self, count):
        data = b''
        while len(data) < count:
            ready, _, _ = select.select([self.master], [], [], 1)
            self.assertTrue(ready, 'missing PTY request')
            data += os.read(self.master, count - len(data))
        return data

    def test_all_seven_unloaded_commands_match_script(self):
        for servo_id in range(7):
            self.bus.set_damping(servo_id, 100)
            self.assertEqual(self.receive(8), packet(9, struct.pack('<BH', servo_id, 100)))

    def test_boundaries_and_little_endian_power(self):
        for servo_id, power in ((0, 0), (0, 1200), (253, 65535)):
            self.bus.set_damping(servo_id, power)
            self.assertEqual(self.receive(8), packet(9, struct.pack('<BH', servo_id, power)))

    def test_invalid_values_never_reach_serial(self):
        for servo_id, power in ((-1, 100), (254, 100), (True, 100), (1.0, 100),
                                ('1', 100), (0, -1), (0, 65536), (0, True),
                                (0, 100.0), (0, '100')):
            with self.subTest(servo_id=servo_id, power=power):
                with self.assertRaises(ValueError):
                    self.bus.set_damping(servo_id, power)
        ready, _, _ = select.select([self.master], [], [], .01)
        self.assertFalse(ready)

    def test_hold_release_and_damping_share_one_connection(self):
        self.bus.set_damping(6, 100)
        self.bus.set_stop_mode(6, 0x11, 1200)
        self.bus.unlock(6)
        expected = (packet(9, struct.pack('<BH', 6, 100))
                    + packet(24, struct.pack('<BBH', 6, 0x11, 1200))
                    + packet(24, struct.pack('<BBH', 6, 0x10, 0)))
        self.assertEqual(self.receive(len(expected)), expected)

    def test_damping_waits_for_pending_monitor_transaction(self):
        result, errors = [], []
        writer_started = threading.Event()
        writer_done = threading.Event()

        def read_monitor():
            try:
                result.append(self.bus.sync_monitor([0]))
            except Exception as exc:
                errors.append(exc)

        def write_damping():
            writer_started.set()
            try:
                self.bus.set_damping(0, 100)
            except Exception as exc:
                errors.append(exc)
            finally:
                writer_done.set()

        reader = threading.Thread(target=read_monitor)
        writer = threading.Thread(target=write_damping)
        reader.start()
        request = self.receive(9)
        self.assertEqual(request[2], 25)
        writer.start()
        self.assertTrue(writer_started.wait(1))
        self.assertFalse(writer_done.wait(.01), 'damping bypassed native controller mutex')
        ready, _, _ = select.select([self.master], [], [], 0)
        self.assertFalse(ready, 'command interleaved with pending monitor read')
        params = struct.pack('<BHHHHBih', 0, 12000, 30, 360, 250, 0, 100, 0)
        response = bytes((5, 28, 22, len(params))) + params
        os.write(self.master, response + bytes((sum(response) & 255,)))
        reader.join(1)
        writer.join(1)
        self.assertFalse(reader.is_alive())
        self.assertFalse(writer.is_alive())
        self.assertEqual(errors, [])
        self.assertTrue(result[0][0].reliable)
        self.assertEqual(self.receive(8), packet(9, struct.pack('<BH', 0, 100)))

    def test_closed_bus_uses_existing_error_contract(self):
        self.bus.close()
        with self.assertRaisesRegex(ServoBusError, 'closed'):
            self.bus.set_damping(0, 100)


if __name__ == '__main__':
    unittest.main()
