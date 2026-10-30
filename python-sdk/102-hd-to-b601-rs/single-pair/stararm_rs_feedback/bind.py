"""离线绑定已校准的默认 B601-RS；不构造设备、不打开串口或 CAN。"""
import argparse
import copy
import json
from pathlib import Path
from types import SimpleNamespace

from .dynamic import POLICY
from .dynamics import DynamicsModel
from .unloaded import robot_signature


def write_spec(robot, output):
    if robot.name != 'seeed_b601_rs_follower' or robot.config.gravity_compensation:
        raise ValueError('Binding requires the default RS follower without gravity feedforward')
    value = dict(format='stararm-rs-dynamic-v3', experimental=True,
                 upright_stock_gripper=True, robot_signature=robot_signature(robot),
                 model_sha256=DynamicsModel().sha256, policy=copy.deepcopy(POLICY))
    # 只创建新文件；不覆盖当前设备配置、校准或已绑定的 spec。
    with Path(output).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calibration', required=True, type=Path, help='Existing follower calibration JSON')
    parser.add_argument('--robot-id', default='follower1')
    parser.add_argument('--output', type=Path, default=Path('feedback.rs-dynamic.json'))
    parser.add_argument('--upright-stock-gripper', action='store_true', required=True,
                        help='Confirm upright fixed base and stock gripper')
    args = parser.parse_args(argv)
    # 仅读取官方默认配置与型号；不实例化/连接机械臂，校准文件只读。
    from lerobot_robot_seeed_b601.config_seeed_b601_rs_follower import SeeedB601RSFollowerConfig
    from lerobot_robot_seeed_b601.seeed_b601_rs_follower import SeeedB601RSFollower
    cfg = SeeedB601RSFollowerConfig(id=args.robot_id, port='can0', can_adapter='socketcan')
    robot = SimpleNamespace(name='seeed_b601_rs_follower', config=cfg,
                            calibration_fpath=args.calibration,
                            motor_model_mapping=SeeedB601RSFollower.motor_model_mapping)
    try:
        if not isinstance(json.loads(args.calibration.read_text()), dict):
            raise ValueError('Expected follower calibration JSON object')
        write_spec(robot, args.output)
    except (ValueError, OSError) as e:
        parser.error(str(e))
    print(f'Created {args.output}; no hardware opened. Binding checks identity, not calibration quality.')


if __name__ == '__main__':
    main()
