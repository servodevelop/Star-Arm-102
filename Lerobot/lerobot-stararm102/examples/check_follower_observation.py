import argparse
import logging
import time

import cv2
from lerobot.cameras.opencv import OpenCVCameraConfig

try:
    from lerobot.cameras.configs import Cv2Backends
except ImportError:
    try:
        from lerobot.cameras.opencv.configuration_opencv import Cv2Backends
    except ImportError:
        Cv2Backends = None

from lerobot_teleoperator_stararm102 import Stararm102FL, Stararm102FLConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Stararm102 follower observation output, including optional camera frames."
    )
    parser.add_argument("--port", required=True, help="Follower serial port, e.g. /dev/ttyUSB1")
    parser.add_argument("--id", default="follower1")
    parser.add_argument("--baudrate", type=int, default=1_000_000)
    parser.add_argument("--interval", type=float, default=0.2, help="Polling interval in seconds.")
    parser.add_argument(
        "--camera",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help=(
            "Camera mapping entry. Repeat this flag to build the cameras dict, "
            "for example --camera first_person=0 --camera third_person=1."
        ),
    )
    parser.add_argument("--camera-width", type=int, default=640, help="Requested camera width.")
    parser.add_argument("--camera-height", type=int, default=480, help="Requested camera height.")
    parser.add_argument("--camera-fps", type=int, default=30, help="Requested camera FPS.")
    parser.add_argument(
        "--camera-backend",
        default="auto",
        choices=["auto", "any", "v4l2"],
        help="OpenCV backend hint for camera open.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Display camera frames in OpenCV windows when image observations are available.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Python logging level.",
    )
    return parser.parse_args()


def parse_camera_path(raw_value: str | None) -> int | str | None:
    if raw_value is None:
        return None

    try:
        return int(raw_value)
    except ValueError:
        return raw_value


def parse_camera_entries(entries: list[str]) -> dict[str, int | str]:
    cameras: dict[str, int | str] = {}
    for entry in entries:
        if "=" not in entry:
            raise ValueError(
                f"Invalid --camera entry {entry!r}. Expected NAME=PATH, for example first_person=0."
            )

        name, raw_path = entry.split("=", 1)
        name = name.strip()
        raw_path = raw_path.strip()
        if not name:
            raise ValueError(f"Invalid --camera entry {entry!r}. Camera name must not be empty.")
        if not raw_path:
            raise ValueError(f"Invalid --camera entry {entry!r}. Camera path must not be empty.")
        if name in cameras:
            raise ValueError(f"Duplicate camera name {name!r} in --camera entries.")

        cameras[name] = parse_camera_path(raw_path)

    return cameras


def build_cameras(args: argparse.Namespace) -> dict[str, OpenCVCameraConfig]:
    camera_entries = parse_camera_entries(args.camera)
    if not camera_entries:
        return {}

    cameras: dict[str, OpenCVCameraConfig] = {}
    for camera_name, camera_path in camera_entries.items():
        camera_kwargs = {
            "index_or_path": camera_path,
            "fps": args.camera_fps,
            "width": args.camera_width,
            "height": args.camera_height,
        }

        if Cv2Backends is not None:
            if args.camera_backend == "any":
                camera_kwargs["backend"] = Cv2Backends.ANY
            elif args.camera_backend == "v4l2":
                camera_kwargs["backend"] = Cv2Backends.V4L2

        cameras[camera_name] = OpenCVCameraConfig(**camera_kwargs)

    return cameras


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )

    follower = Stararm102FL(
        Stararm102FLConfig(
            id=args.id,
            port=args.port,
            baudrate=args.baudrate,
            cameras=build_cameras(args),
        )
    )

    logging.info("Connecting follower on port=%s", args.port)
    if not args.camera:
        logging.info("Camera disabled for this check.")
    else:
        logging.info("Cameras enabled: %s", ", ".join(args.camera))

    follower.connect(calibrate=False)
    try:
        logging.info("Reading observations continuously. Press Ctrl+C to stop.")
        step = 0
        while True:
            step += 1
            observation = follower.get_observation()
            joint_obs = {k: v for k, v in observation.items() if k.endswith(".pos")}
            image_summary: dict[str, tuple[int, ...]] = {}

            for key, value in observation.items():
                if key in follower.cameras:
                    shape = getattr(value, "shape", None)
                    image_summary[key] = tuple(shape) if shape is not None else ()
                    if args.render and shape is not None:
                        cv2.imshow(key, cv2.cvtColor(value, cv2.COLOR_RGB2BGR))

            logging.info(
                "step=%d joints=%s images=%s",
                step,
                joint_obs,
                image_summary,
            )

            if args.render and cv2.waitKey(1) & 0xFF == ord("q"):
                logging.info("Received 'q' from render window, stopping.")
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logging.info("Stopping follower observation check.")
    finally:
        if args.render:
            cv2.destroyAllWindows()
        follower.disconnect()


if __name__ == "__main__":
    main()

"""
PYTHONPATH=. python examples/check_follower_observation.py \
  --port=/dev/ttyUSB0 \
  --camera first_person=2 \
  --camera third_person=0 \
  --camera-fps=30 \
  --camera-width=640 \
  --camera-height=480 \
  --camera-backend=any \
  --render
"""
