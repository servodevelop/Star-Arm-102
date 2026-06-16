import argparse
import time

from lerobot_teleoperator_stararm102 import Stararm102HD, Stararm102HDConfig
from lerobot_teleoperator_stararm102.config_stararm102_hd import ButtonConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read the optional Stararm102 HD button servo state.")
    parser.add_argument("--port", required=True, help="Leader serial port, e.g. /dev/ttyUSB0")
    parser.add_argument("--id", default="stararm102_hd")
    parser.add_argument("--baudrate", type=int, default=1_000_000)
    parser.add_argument("--button-id", type=int, default=7)
    parser.add_argument("--interval", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    leader = Stararm102HD(
        Stararm102HDConfig(
            id=args.id,
            port=args.port,
            baudrate=args.baudrate,
            button=ButtonConfig(enabled=True, id=args.button_id),
        )
    )

    leader.connect(calibrate=False)
    try:
        print("Reading button state. Press Ctrl+C to stop.")
        while True:
            angle = leader.bus.port_handler.read_servo_angle_monitor(args.button_id)
            if angle is None:
                print("button_angle=None  locked=unknown")
                time.sleep(args.interval)
                continue
            locked = angle >= leader.config.button.trigger_threshold
            print(f"button_angle={angle:7.2f}  locked={locked}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        leader.disconnect()


if __name__ == "__main__":
    main()

'''
PYTHONPATH=. /home/welt/miniconda3/envs/kian/bin/python /home/welt/kian/lerobot/rebot_102/stararm102_HD/examples/read_button_state.py --port=/dev/ttyUSB0
'''