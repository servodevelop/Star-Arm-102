"""Settings for StarArm fixed damping and gripper contact hold."""
import copy
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import tempfile

from .config import Config
from .gripper_lock import GripperLockConfig

GRIPPER_FIELDS = {
    'contact_torque_nm': (.05, 5., '接触扭矩阈值', 'Nm'),
    'release_torque_nm': (.01, 5., '释放扭矩阈值', 'Nm'),
    'contact_dwell_s': (.04, 1., '接触确认时间', 's'),
    'release_dwell_s': (.04, 1., '失物释放确认时间', 's'),
    'open_release_leader_deg': (.1, 5., '反向解锁角度', '°'),
    'open_release_dwell_s': (.02, .5, '反向解锁确认时间', 's'),
}


def defaults():
    return dict(format='stararm-rs-unloaded-damping-v1', revision=0,
                damping_enabled=True, joint_damping_mw=[100] * 7,
                gripper_lock=asdict(GripperLockConfig(enabled=True)))


def validate(data):
    if not isinstance(data, dict) or set(data) != set(defaults()):
        raise ValueError('参数字段不完整或包含未知字段')
    value = copy.deepcopy(data)
    if value['format'] != defaults()['format'] or type(value['revision']) is not int or value['revision'] < 0:
        raise ValueError('参数格式无效，请使用本项目生成的 settings.json')
    Config(damping_enabled=value['damping_enabled'], joint_damping_mw=value['joint_damping_mw']).validate()
    lock = value['gripper_lock']
    if not isinstance(lock, dict) or set(lock) != set(asdict(GripperLockConfig())):
        raise ValueError('夹爪锁止参数字段不完整或包含未知字段')
    for key, (low, high, *_) in GRIPPER_FIELDS.items():
        number = lock[key]
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or not low <= number <= high:
            raise ValueError(f'{key}: 数值须在 {low} 到 {high} 之间')
    GripperLockConfig(**lock)
    return value


def read(path):
    return validate(json.loads(Path(path).read_text(encoding='utf-8')))


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, ensure_ascii=False, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
