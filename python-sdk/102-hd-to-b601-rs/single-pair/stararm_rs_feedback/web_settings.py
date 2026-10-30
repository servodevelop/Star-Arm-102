"""网页可编辑的普通阻尼参数；不开放校准、设备映射或保护阈值。"""
import copy
import json
import math
import os
from pathlib import Path
import tempfile

from .dynamic import POLICY

SCALARS = {
    'residual_filter_s': (.02, 1., '力矩滤波时间', 's'),
    'confirmation_s': (.02, 1., '负载确认时间', 's'),
    'power_filter_s': (.02, 1., '输出平滑时间', 's'),
    'power_rise_mw_s': (100., 20000., '功率上升速率', 'mW/s'),
    'power_fall_mw_s': (100., 30000., '功率下降速率', 'mW/s'),
}
ARRAYS = {
    'deadzone_nm': (.05, 15., '基础死区', 'Nm'),
    'moving_margin_nm': (0., 5., '最大运动余量', 'Nm'),
    'excess_full_scale_nm': (.05, 20., '满输出力矩标尺', 'Nm'),
}

def defaults():
    return dict(format='stararm-rs-web-v1', revision=0, max_power_mw=1200,
                joint_power_mw=[1200, 1200, 1200, 1200, 1200, 0, 1200],
                **{k:copy.deepcopy(POLICY[k]) for k in (*SCALARS, *ARRAYS)})

def validate(data):
    if not isinstance(data, dict) or set(data) != set(defaults()):
        raise ValueError('参数字段不完整或包含未知字段')
    d=copy.deepcopy(data)
    if d['format']!='stararm-rs-web-v1' or type(d['revision']) is not int or d['revision']<0:
        raise ValueError('无效参数版本')
    if type(d['max_power_mw']) is not int or not 400<=d['max_power_mw']<=1500:
        raise ValueError('总功率上限须为 400–1500 mW 的整数')
    powers=d['joint_power_mw']
    if (not isinstance(powers,list) or len(powers)!=7 or powers[5]!=0 or
            any(type(p) is not int or not 0<=p<=d['max_power_mw'] for p in powers)):
        raise ValueError('各轴上限须在 0 到总上限之间，J6 普通阻尼保持 0')
    for key,(lo,hi,*_) in {**SCALARS,**ARRAYS}.items():
        values=d[key] if key in ARRAYS else [d[key]]
        if not isinstance(values,list) or (key in ARRAYS and len(values)!=7):
            raise ValueError(f'{key}: 需要七个值')
        # J6 不参与普通阻尼，保留代码中的原值。
        for i,x in enumerate(values):
            if key in ARRAYS and i==5:
                if x!=POLICY[key][5]:raise ValueError('J6 参数不可修改')
                continue
            if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or not lo<=x<=hi:
                raise ValueError(f'{key}: 数值须在 {lo} 到 {hi} 之间')
    return d

def read(path):
    return validate(json.loads(Path(path).read_text(encoding='utf-8')))

def atomic_json(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,allow_nan=False)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
