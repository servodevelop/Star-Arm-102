"""Check servo responses without changing torque, origin, or target position."""

import argparse
import sys

import fashionstar_uart_sdk as uservo
import serial


def probe(bus, ids):
    """Return missing IDs. Only the SDK ping operation is used."""
    missing = []
    for servo_id in ids:
        online = bus.ping(servo_id)
        print(f"ID {servo_id}: {'OK' if online else 'NO RESPONSE'}")
        if not online:
            missing.append(servo_id)
    return missing


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="serial port for one arm")
    parser.add_argument("--baudrate", type=int, default=1000000)
    parser.add_argument("--ids", type=int, nargs="+", default=list(range(7)),
                        help="IDs to ping (default: 0 1 2 3 4 5 6)")
    args = parser.parse_args(argv)
    if args.baudrate <= 0 or any(not 0 <= i <= 253 for i in args.ids):
        parser.error("use a positive baud rate and device IDs from 0 to 253")
    try:
        with serial.Serial(args.port, baudrate=args.baudrate, timeout=0) as uart:
            missing = probe(uservo.UartServoManager(uart), args.ids)
    except (serial.SerialException, OSError) as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 2
    if missing:
        print("Check power, port, baud rate, and wiring before commanding motion.", file=sys.stderr)
        return 1
    print("All requested IDs responded. No motion, torque, or origin commands were sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
