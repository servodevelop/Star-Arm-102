import argparse
import logging
import time

import cv2
from lerobot.cameras.opencv import OpenCVCameraConfig

from lerobot_teleoperator_stararm102 import (
    Stararm102FL,
    Stararm102FLConfig,
    Stararm102HD,
    Stararm102HDConfig,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Teleoperate Stararm102 follower from Stararm102 HD leader with two follower cameras."
    )
    parser.add_argument("--leader-port", required=True, help="Leader serial port, e.g. /dev/ttyUSB1")
    parser.add_argument("--follower-port", required=True, help="Follower serial port, e.g. /dev/ttyUSB0")
    parser.add_argument("--leader-id", default="leader1")
    parser.add_argument("--follower-id", default="follower1")
    parser.add_argument("--baudrate", type=int, default=1_000_000)
    parser.add_argument("--interval", type=float, default=0.03, help="Loop sleep in seconds.")
    parser.add_argument("--first-person", required=True, help="First-person camera index/path, e.g. 0")
    parser.add_argument("--third-person", required=True, help="Third-person camera index/path, e.g. 2")
    parser.add_argument("--camera-width", type=int, default=640)
    parser.add_argument("--camera-height", type=int, default=480)
    parser.add_argument("--camera-fps", type=int, default=30)
    parser.add_argument("--render", action="store_true", help="Display follower camera frames.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Python logging level.",
    )
    return parser.parse_args()


def parse_camera_path(raw_value: str) -> int | str:
    try:
        return int(raw_value)
    except ValueError:
        return raw_value


def build_cameras(args: argparse.Namespace) -> dict[str, OpenCVCameraConfig]:
    return {
        "first_person": OpenCVCameraConfig(
            index_or_path=parse_camera_path(args.first_person),
            width=args.camera_width,
            height=args.camera_height,
            fps=args.camera_fps,
        ),
        "third_person": OpenCVCameraConfig(
            index_or_path=parse_camera_path(args.third_person),
            width=args.camera_width,
            height=args.camera_height,
            fps=args.camera_fps,
        ),
    }


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )

    leader = Stararm102HD(
        Stararm102HDConfig(
            id=args.leader_id,
            port=args.leader_port,
            baudrate=args.baudrate,
        )
    )
    follower = Stararm102FL(
        Stararm102FLConfig(
            id=args.follower_id,
            port=args.follower_port,
            baudrate=args.baudrate,
            cameras=build_cameras(args),
        )
    )

    logging.info("Connecting leader on %s", args.leader_port)
    leader.connect(calibrate=False)
    try:
        logging.info("Connecting follower on %s", args.follower_port)
        follower.connect(calibrate=False)
        try:
            logging.info("Teleoperation running. Press Ctrl+C to stop.")
            while True:
                action = leader.get_action()
                sent_action = follower.send_action(action)
                observation = follower.get_observation()

                if args.render:
                    for key, value in observation.items():
                        if key in follower.cameras:
                            cv2.imshow(key, cv2.cvtColor(value, cv2.COLOR_RGB2BGR))
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        logging.info("Received 'q' from render window, stopping.")
                        break

                logging.debug("sent_action=%s", sent_action)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logging.info("Stopping teleoperation.")
        finally:
            if args.render:
                cv2.destroyAllWindows()
            follower.disconnect()
    finally:
        leader.disconnect()


if __name__ == "__main__":
    main()


"""
PYTHONPATH=. python examples/teleoperate_hd_to_fl_with_cameras.py \
  --leader-port=/dev/ttyUSB0 \
  --follower-port=/dev/ttyUSB1 \
  --first-person=0 \
  --third-person=2 \
  --camera-width=640 \
  --camera-height=480 \
  --camera-fps=30 \
  --render
"""
