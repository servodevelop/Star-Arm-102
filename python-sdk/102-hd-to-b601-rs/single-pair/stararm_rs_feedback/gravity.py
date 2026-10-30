"""B601-RS 的静态支撑力矩。输入为原始电机弧度，不应用遥操作方向倍率。"""
import hashlib
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from .resources import runtime_file

MODEL_PATH = runtime_file('assets/b601_rs.urdf')
I3 = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def mv(r, v):
    return tuple(dot(row, v) for row in r)


def mm(a, b):
    return tuple(tuple(dot(row, col) for col in zip(*b)) for row in a)


def rotation(axis, angle):
    x, y, z = axis
    c, s, h = math.cos(angle), math.sin(angle), 1-math.cos(angle)
    return ((c+x*x*h, x*y*h-z*s, x*z*h+y*s),
            (y*x*h+z*s, c+y*y*h, y*z*h-x*s),
            (z*x*h-y*s, z*y*h+x*s, c+z*z*h))


def xyz(text, default=(0., 0., 0.)):
    v = tuple(map(float, text.split())) if text is not None else default
    if len(v) != 3 or not all(math.isfinite(x) for x in v):
        raise ValueError('Invalid model vector')
    return v


def origin(el):
    if el is None:
        return I3, (0., 0., 0.)
    r, p, y = xyz(el.get('rpy'))
    return mm(mm(rotation((0, 0, 1), y), rotation((0, 1, 0), p)),
              rotation((1, 0, 0), r)), xyz(el.get('xyz'))


class GravityModel:
    """URDF 指爪移动分支固定在闭合位置；质量保留，误差由独立空载复测约束。"""
    def __init__(self, path=MODEL_PATH):
        data = Path(path).read_bytes()
        self.sha256 = hashlib.sha256(data).hexdigest()
        tree = ET.fromstring(data)
        self.bodies, self.children = {}, {}
        for link in tree.findall('link'):
            name = link.get('name')
            mass = link.find('inertial/mass')
            mass = 0. if mass is None else float(mass.get('value'))
            if not name or name in self.bodies or not math.isfinite(mass) or mass < 0:
                raise ValueError('Invalid model link/mass')
            self.bodies[name] = mass, origin(link.find('inertial/origin'))[1]
        parents, indices = set(), set()
        for joint in tree.findall('joint'):
            name, kind = joint.get('name'), joint.get('type')
            parent, child = joint.find('parent').get('link'), joint.find('child').get('link')
            if parent not in self.bodies or child not in self.bodies or child in parents:
                raise ValueError('Invalid model tree')
            idx = int(name[-1])-1 if name in [f'joint{i}' for i in range(1, 7)] else None
            if idx is not None:
                if idx in indices or kind not in ('revolute', 'continuous'):
                    raise ValueError('Expected six distinct revolute arm joints')
                indices.add(idx)
            elif kind != 'fixed' and not (kind == 'prismatic' and name in ('joint_left', 'joint_right')
                                         and parent == 'gripper_end'):
                raise ValueError('Unknown moving model branch')
            axis = xyz(None if joint.find('axis') is None else joint.find('axis').get('xyz'), (1, 0, 0))
            norm = math.sqrt(dot(axis, axis))
            if idx is not None and norm < 1e-9:
                raise ValueError('Zero model joint axis')
            axis = tuple(x/norm for x in axis) if norm else axis
            self.children.setdefault(parent, []).append((child, idx, origin(joint.find('origin')), axis))
            parents.add(child)
        roots = set(self.bodies)-parents
        if len(roots) != 1 or indices != set(range(6)):
            raise ValueError('Expected one root and joint1..joint6')
        self.root = roots.pop()
        self.evaluate([0.]*6)

    def evaluate(self, positions):
        if len(positions) < 6 or not all(math.isfinite(x) for x in positions[:6]):
            raise ValueError('Expected six finite raw motor positions')
        tau, axes, pivots, visited = [0.]*6, {}, {}, set()
        potential = 0.

        def walk(link, r, p, ancestors):
            nonlocal potential
            if link in visited:
                raise ValueError('Cyclic model')
            visited.add(link)
            mass, com = self.bodies[link]
            center = add(p, mv(r, com))
            force = (0., 0., -9.80665*mass)
            potential -= dot(center, force)
            for i in ancestors:
                lever = tuple(x-y for x, y in zip(center, pivots[i]))
                tau[i] -= dot(axes[i], cross(lever, force))
            for child, idx, (lr, lp), axis in self.children.get(link, []):
                rr, pp = mm(r, lr), add(p, mv(r, lp))
                branch = ancestors
                if idx is not None:
                    axes[idx], pivots[idx] = mv(rr, axis), pp
                    rr = mm(rr, rotation(axis, positions[idx]))
                    branch = ancestors+(idx,)
                walk(child, rr, pp, branch)
        walk(self.root, I3, (0., 0., 0.), ())
        if visited != set(self.bodies):
            raise ValueError('Disconnected model')
        return tau, potential
