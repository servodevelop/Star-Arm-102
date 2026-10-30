import functools
import inspect
import json
import re
import subprocess
from .session import Session

def install_runtime_wrapper(module, cfg, *, enabled=False, log_path=None, collect_path=None, session_factory=Session):
    """只包装本次进程，退出即可恢复。两个设备在官方循环开始前已经连接。"""
    original = module.teleop_loop
    if getattr(original, "_stararm_rs_feedback", False):
        raise ValueError("RS feedback wrapper already active")
    signature = inspect.signature(original)
    if not {"teleop", "robot"} <= set(signature.parameters):
        raise ValueError("Unsupported LeRobot teleop_loop signature")
    try:
        source = inspect.getsource(original)
    except (OSError, TypeError):
        source = ""
    if "_stararm_automatic_feedback" in source:
        raise ValueError("Remove legacy stararm_auto_feedback hook before using the RS launcher")

    @functools.wraps(original)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        options = dict(enabled=enabled, log_path=log_path)
        if collect_path:
            options['collect_path'] = collect_path
        with session_factory(bound.arguments["teleop"], bound.arguments["robot"], cfg, **options):
            return original(*args, **kwargs)

    wrapped._stararm_rs_feedback = True
    module.teleop_loop = wrapped
    return original

def check_can(config):
    """Read-only check before either arm connects; never configures the interface."""
    port = config.port
    if config.can_adapter != 'socketcan' or not re.fullmatch('[a-zA-Z0-9_-]+', port):
        raise ValueError('RS residual trial requires a SocketCAN interface such as can0')
    hint = (f'Check: ip -details link show {port}\n'
            f'If no other controller is running, configure CAN:\n'
            f'  sudo ip link set {port} down\n'
            f'  sudo ip link set {port} type can bitrate 1000000\n'
            f'  sudo ip link set {port} up')
    try:
        result = subprocess.run(['ip', '-json', '-details', 'link', 'show', 'dev', port],
                                check=True, capture_output=True, text=True, timeout=3)
        records = json.loads(result.stdout)
        if len(records) != 1:
            raise ValueError('Expected one CAN interface')
        entry = records[0]
        info = entry.get('linkinfo', {})
        details = info.get('info_data', {})
        if ('UP' not in entry.get('flags', []) or info.get('info_kind') != 'can'
                or details.get('bittiming', {}).get('bitrate') != 1000000
                or details.get('state') in ('BUS-OFF', 'STOPPED', 'SLEEPING')):
            raise ValueError('CAN must be UP at 1 Mbps and not bus-off')
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as e:
        raise ValueError(f'CAN preflight failed before arm connection: {e}\n{hint}') from e
