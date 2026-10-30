"""固定空载模型与准静态残余力矩阻尼。"""
import collections
import hashlib
import json
import math
from pathlib import Path

from .config import NAMES
from .gravity import GravityModel

ALGORITHM = 'stararm-rs-unloaded-v1'
RADIUS = [math.radians(5)]*6+[math.radians(30)]
SIGMA_MAX = [.5, .5, .5, .25, .25, .25]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def robot_signature(robot):
    path = Path(robot.calibration_fpath)
    if not path.is_file():
        raise ValueError('Follower calibration file required for unloaded model')
    c = robot.config
    values = dict(robot_type=robot.name, robot_id=c.id,
                  motor_can_ids=c.motor_can_ids, directions=c.joint_directions,
                  limits=c.joint_limits, models=robot.motor_model_mapping,
                  calibration_sha256=digest(path.read_bytes()),
                  gravity_compensation=bool(c.gravity_compensation))
    return digest(canonical(values))


def features(gravity, velocity):
    return [1., gravity, velocity, math.tanh(velocity/.03)]


def within(q, poses):
    # 每个姿态邻域分别验证，不能把不同姿态的各轴极值拼成未经测试的大方框。
    return any(all(abs(a-b) <= radius for a, b, radius in zip(q, pose, RADIUS)) for pose in poses)


def vector(v, n):
    if not isinstance(v, list) or len(v) != n or any(
            isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in v):
        raise ValueError(f'Expected {n} finite values')
    return v




class Profile:
    def __init__(self, path=None, *, data=None, require_validated=True):
        self.data = json.loads(Path(path).read_text(encoding='utf-8')) if data is None else data
        d = self.data
        self.model = GravityModel()
        if d.get('algorithm') != ALGORITHM or d.get('model_sha256') != self.model.sha256:
            raise ValueError('Unloaded model format/RS URDF hash mismatch')
        self.coefficients = d['coefficients']
        if not isinstance(self.coefficients, list) or len(self.coefficients) != 6:
            raise ValueError('Expected six model coefficient rows')
        for row in self.coefficients:
            vector(row, 4)
        self.sigma = vector(d['sigma_nm'], 6)
        if any(not .03 <= x <= limit for x, limit in zip(self.sigma, SIGMA_MAX)):
            raise ValueError('Unloaded noise too large or invalid')
        self.poses = d['validated_poses_rad']
        if not isinstance(self.poses, list) or not 1 <= len(self.poses) <= 3000:
            raise ValueError('Invalid validated pose coverage')
        for q in self.poses:
            vector(q, 7)
        self.limits = d['joint_limits_deg']
        for name in NAMES:
            lo, hi = vector(self.limits[name], 2)
            if lo >= hi:
                raise ValueError('Invalid model joint limits')
        if not isinstance(d.get('robot_signature'), str) or len(d['robot_signature']) != 64:
            raise ValueError('Missing unloaded robot identity')
        for i in (1, 2, 3):
            if i not in d['gravity_axes'] or not .2 <= abs(self.coefficients[i][1]) <= 3:
                raise ValueError('J2/J3/J4 gravity excitation/sign/scale invalid')
        if require_validated:
            report = d['validation']
            if (d.get('validated') is not True or d.get('training_samples', 0) < 120
                    or report.get('usable_samples', 0) < 80
                    or not .7 <= report.get('coverage_fraction', 0) <= 1
                    or report.get('false_activation_frames') != 0
                    or d['training_csv_sha256'] == d['validation_csv_sha256']
                    or d['training_run_id'] == d['validation_run_id']
                    or report.get('steady_samples', 0) < 40
                    or report.get('noise_source') != 'training_only_p95_absolute_residual'
                    or report.get('evidence_sigma') != 3.
                    or report.get('confirmation_s') != .2
                    or not all(digest_text(d.get(k)) for k in ('training_csv_sha256', 'validation_csv_sha256'))
                    or d.get('integrity_sha256') != digest(canonical({k: v for k, v in d.items()
                                                                     if k != 'integrity_sha256'}))):
                raise ValueError('Independent unloaded validation/integrity did not pass')

    def check_robot(self, robot):
        if robot_signature(robot) != self.data['robot_signature']:
            raise ValueError('Unloaded profile differs from follower calibration/mapping/configuration; recapture')

    def residual(self, q, v, tau):
        gravity, _ = self.model.evaluate(q)
        return [tau[i]-sum(a*b for a, b in zip(self.coefficients[i], features(gravity[i], v[i])))
                for i in range(6)]


def digest_text(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


class Observer:
    """只用已标定姿态中的稳定证据；参数固定，不把持物数据在线学习为空载。"""
    def __init__(self, profile, reference_nm):
        self.profile = profile
        self.reference = reference_nm
        self.loads = [0.]*7
        self.residual_nm = [0.]*6
        self.status = 'warming up'
        self.last = self.velocity = self.last_evidence = None
        self.history = collections.deque()
        self.positive = [None]*6

    def invalidate(self, reason):
        self.loads = [0.]*7
        self.positive = [None]*6
        self.history.clear()
        self.velocity = self.last = self.last_evidence = None
        self.status = reason

    def update(self, q, v, tau, now):
        vector(q, 7); vector(v, 7); vector(tau, 7)
        if not math.isfinite(now):
            raise ValueError('Invalid unloaded observer time')
        if self.last is not None and not 0 < now-self.last <= .25:
            self.invalidate('feedback gap')
        dt = .033 if self.last is None else now-self.last
        self.last = now
        if any(not math.radians(self.profile.limits[n][0]+2) <= q[i]
               <= math.radians(self.profile.limits[n][1]-2) for i, n in enumerate(NAMES[:6])):
            self.invalidate('near joint limit')
            return self.loads
        if not within(q, self.profile.poses):
            self.invalidate('outside validated poses')
            return self.loads
        alpha = dt/(.1+dt)
        previous = self.velocity
        self.velocity = list(v[:6]) if previous is None else [a+alpha*(b-a) for a, b in zip(previous, v)]
        acceleration = [0.]*6 if previous is None else [(a-b)/dt for a, b in zip(self.velocity, previous)]
        self.history.append((now, list(q)))
        while len(self.history) > 1 and self.history[1][0] <= now-.5:
            self.history.popleft()
        stable = (now-self.history[0][0] >= .5 and max(map(abs, self.velocity)) <= .08
                  and max(map(abs, acceleration)) <= .5
                  and all(max(row[1][i] for row in self.history)-min(row[1][i] for row in self.history)
                          <= math.radians(.7) for i in range(6)))
        self.residual_nm = self.profile.residual(q, self.velocity, tau)
        target = [0.]*7
        if stable:
            self.status = 'steady residual'
            self.last_evidence = now
            for i, r in enumerate(self.residual_nm):
                excess = abs(r)-3*self.profile.sigma[i]
                if excess > 0:
                    if self.positive[i] is None:
                        self.positive[i] = now
                    if now-self.positive[i] >= .2:
                        target[i] = min(1., excess/self.reference[i])
                else:
                    self.positive[i] = None
        else:
            self.status = 'moving/settling'
            self.positive = [None]*6
            if self.last_evidence is not None and now-self.last_evidence <= 1.:
                target = list(self.loads)
        alpha = dt/(.12+dt)
        self.loads = [a+alpha*(b-a) for a, b in zip(self.loads, target)]
        self.loads = [x if x >= .001 else 0. for x in self.loads]
        return self.loads
