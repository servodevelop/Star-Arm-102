import argparse
import ast
import logging
import time
from pathlib import Path

from lerobot_teleoperator_stararm102 import Stararm102FL, Stararm102FLConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay leader action logs into the Stararm102 follower and print sent/readback state."
    )
    parser.add_argument("--port", required=True, help="Follower serial port, e.g. /dev/ttyUSB1")
    parser.add_argument("--id", default="follower1")
    parser.add_argument("--baudrate", type=int, default=1_000_000)
    parser.add_argument(
        "--input-log",
        required=True,
        help="Path to a leader state log file containing `action={...}` records.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Delay between replayed actions in seconds.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Replay the whole action sequence this many times.",
    )
    parser.add_argument(
        "--skip-locked",
        action="store_true",
        help="Skip lines where the leader log says locked=True.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Python logging level.",
    )
    return parser.parse_args()


def extract_action_from_line(line: str) -> tuple[dict[str, float], bool] | None:
    if "action=" not in line:
        return None

    locked = "locked=True" in line
    action_start = line.index("action=") + len("action=")
    raw_start = line.find(" raw=", action_start)
    if raw_start == -1:
        return None

    action_text = line[action_start:raw_start].strip()
    try:
        action = ast.literal_eval(action_text)
    except (SyntaxError, ValueError):
        return None

    if not isinstance(action, dict):
        return None

    normalized_action: dict[str, float] = {}
    for key, value in action.items():
        if not isinstance(key, str):
            continue
        try:
            normalized_action[key] = float(value)
        except (TypeError, ValueError):
            continue

    if not normalized_action:
        return None

    return normalized_action, locked


def load_actions(log_path: Path, skip_locked: bool) -> list[dict[str, float]]:
    actions: list[dict[str, float]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        parsed = extract_action_from_line(line)
        if parsed is None:
            continue
        action, locked = parsed
        if skip_locked and locked:
            continue
        actions.append(action)
    return actions


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )

    log_path = Path(args.input_log)
    actions = load_actions(log_path, skip_locked=args.skip_locked)
    if not actions:
        raise ValueError(f"No valid actions found in log file: {log_path}")

    logging.info("Loaded %d replay actions from %s", len(actions), log_path)
    logging.info("Creating follower instance on port=%s baudrate=%s", args.port, args.baudrate)

    follower = Stararm102FL(
        Stararm102FLConfig(
            id=args.id,
            port=args.port,
            baudrate=args.baudrate,
        )
    )

    logging.info("Connecting follower...")
    follower.connect(calibrate=False)
    try:
        logging.info("Replaying actions to follower. Press Ctrl+C to stop.")
        for replay_idx in range(args.repeat):
            logging.info("Replay round %d/%d", replay_idx + 1, args.repeat)
            for step_idx, action in enumerate(actions, start=1):
                sent_action = follower.send_action(action)
                observation = follower.get_observation()
                logging.info(
                    "step=%d/%d sent=%s observation=%s",
                    step_idx,
                    len(actions),
                    sent_action,
                    observation,
                )
                time.sleep(args.interval)
    except KeyboardInterrupt:
        logging.info("Stopping follower replay.")
    finally:
        follower.bus.port_handler.StopOnControlMode(0xFF,"unlocked",0)
        follower.disconnect()


if __name__ == "__main__":
    main()


'''
PYTHONPATH=.:/home/welt/kian/lerobot/rebot_102/lerobot/src \
/home/welt/miniconda3/envs/kian/bin/python \
examples/replay_leader_actions_to_follower.py \
  --port=/dev/ttyUSB0 \
  --input-log='./examples/leader.log' \
  --skip-locked \
  --interval=0.2
'''