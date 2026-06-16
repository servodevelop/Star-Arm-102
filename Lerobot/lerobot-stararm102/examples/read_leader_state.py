import argparse
import logging
import time
from pathlib import Path

from lerobot_teleoperator_stararm102 import Stararm102HD, Stararm102HDConfig
from lerobot_teleoperator_stararm102.config_stararm102_hd import ButtonConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Connect to the Stararm102 HD and log joint actions and lock state."
    )
    parser.add_argument("--port", required=True, help="Leader serial port, e.g. /dev/ttyUSB0")
    parser.add_argument("--id", default="leader1")
    parser.add_argument("--baudrate", type=int, default=1_000_000)
    parser.add_argument("--button-enabled", action="store_true", help="Enable external button lock state reading.")
    parser.add_argument("--button-id", type=int, default=7)
    parser.add_argument("--interval", type=float, default=0.2, help="Polling interval in seconds.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Python logging level.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    log_path = Path(__file__).resolve().parent / "leader.log"
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, args.log_level))

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info("Writing leader log to %s", log_path)
    logging.info("Creating leader instance on port=%s baudrate=%s", args.port, args.baudrate)

    leader = Stararm102HD(
        Stararm102HDConfig(
            id=args.id,
            port=args.port,
            baudrate=args.baudrate,
            button=ButtonConfig(enabled=args.button_enabled, id=args.button_id),
        )
    )

    logging.info("Connecting leader...")
    leader.connect(calibrate=False)
    try:
        logging.info("Reading leader state. Press Ctrl+C to stop.")
        while True:
            action = leader.get_action()
            raw_positions = dict(leader._last_raw_positions)
            locked = leader._leader_locked if leader.button.enabled else None

            if locked is None:
                logging.info("locked=disabled action=%s raw=%s", action, raw_positions)
            else:
                logging.info("locked=%s action=%s raw=%s", locked, action, raw_positions)

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logging.info("Stopping leader state reader.")
    finally:
        leader.disconnect()


if __name__ == "__main__":
    main()

'''
PYTHONPATH=.:/home/welt/kian/lerobot/rebot_102/lerobot/src \
/home/welt/miniconda3/envs/kian/bin/python \
examples/read_leader_state.py \
  --port=/dev/ttyUSB0 \
  --button-enabled
'''
