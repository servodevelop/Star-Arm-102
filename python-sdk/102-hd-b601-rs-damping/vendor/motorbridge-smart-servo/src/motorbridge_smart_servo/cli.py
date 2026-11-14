from __future__ import annotations

import argparse

from .bus import SmartServoBus


def _add_common_bus_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--vendor", default="fashionstar")
    parser.add_argument("--port", required=True)
    parser.add_argument("--baudrate", type=int, default=1_000_000)


def main() -> None:
    parser = argparse.ArgumentParser(prog="motorbridge-smart-servo")
    sub = parser.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan")
    _add_common_bus_args(scan)
    scan.add_argument("--max-id", type=int, default=20)

    read = sub.add_parser("read-angle")
    _add_common_bus_args(read)
    read.add_argument("--id", type=int, required=True)
    read.add_argument("--multi-turn", action="store_true")

    monitor = sub.add_parser("monitor")
    _add_common_bus_args(monitor)
    monitor.add_argument("--id", type=int, required=True)
    monitor.add_argument("--multi-turn", action="store_true")
    monitor.add_argument("--interval-s", type=float, default=0.02)

    move = sub.add_parser("set-angle")
    _add_common_bus_args(move)
    move.add_argument("--id", type=int, required=True)
    move.add_argument("--angle", type=float, required=True)
    move.add_argument("--multi-turn", action="store_true")
    move.add_argument("--interval-ms", type=int, default=0)

    args = parser.parse_args()

    with SmartServoBus.open(vendor=args.vendor, port=args.port, baudrate=args.baudrate) as bus:
        if args.cmd == "scan":
            for servo_id in bus.scan(args.max_id):
                print(servo_id)
        elif args.cmd == "read-angle":
            sample = bus.read_angle(args.id, multi_turn=args.multi_turn)
            print(
                f"raw={sample.raw_deg:9.3f} "
                f"filtered={sample.filtered_deg:9.3f} "
                f"reliable={sample.reliable}"
            )
        elif args.cmd == "monitor":
            for sample in bus.monitor(args.id, multi_turn=args.multi_turn, interval_s=args.interval_s):
                print(
                    f"raw={sample.raw_deg:9.3f} "
                    f"filtered={sample.filtered_deg:9.3f} "
                    f"reliable={sample.reliable}"
                )
        elif args.cmd == "set-angle":
            bus.set_angle(args.id, args.angle, multi_turn=args.multi_turn, interval_ms=args.interval_ms)


if __name__ == "__main__":
    main()
