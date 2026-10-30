"""Check the installed environment without connecting either arm."""
import importlib
from importlib.metadata import version
import inspect
import platform
import sys
from .resources import ready, resource_root


def main():
    errors = []
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        errors.append('Supported control host: Linux x86_64 with SocketCAN')
    if sys.version_info[:2] != (3, 12):
        errors.append('Use Python 3.12 for the pinned environment')
    expected = {'lerobot':'0.4.1', 'lerobot-teleoperator-rebot-arm-102':'1.0.1',
                'lerobot-robot-seeed-b601':'1.0.5', 'motorbridge':'0.5.6',
                'motorbridge-smart-servo':'0.0.4+rsfix1'}
    for package, target in expected.items():
        try:
            actual = version(package)
            if actual != target: errors.append(f'{package}: expected {target}, got {actual}')
            else: print(f'OK {package} {actual}')
        except importlib.metadata.PackageNotFoundError:
            errors.append(f'Missing {package}')
    try:
        module = importlib.import_module('lerobot.scripts.lerobot_teleoperate')
        if not {'teleop','robot'} <= set(inspect.signature(module.teleop_loop).parameters):
            errors.append('Unsupported LeRobot teleop_loop API')
        importlib.import_module('lerobot_teleoperator_rebot_arm_102')
        importlib.import_module('lerobot_robot_seeed_b601')
    except (ImportError, AttributeError) as error:
        errors.append(str(error))
    if not ready(): errors.append('Missing or damaged runtime assets: run python -m stararm_rs_feedback.resources')
    else: print(f'OK runtime assets {resource_root()}')
    if errors:
        raise SystemExit('Environment check failed:\n'+'\n'.join('- '+error for error in errors))
    print('Environment ready. No hardware connections were opened.')


if __name__ == '__main__': main()
