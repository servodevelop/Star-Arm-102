"""Fixed-base rigid-body inverse dynamics in world coordinates.

Uses the bundled URDF mass, COM and inertia. Motor radians are used directly;
finger translations remain closed, as in GravityModel. No identified friction
or motor/gear inertia is claimed by this theoretical model.
"""
import math
import xml.etree.ElementTree as ET

from .gravity import (GravityModel, MODEL_PATH, I3, add, cross, dot, mm, mv,
                      origin, rotation)

ZERO = (0., 0., 0.)


def scale(s, v):
    return tuple(s*x for x in v)


def sub(a, b):
    return tuple(x-y for x,y in zip(a,b))


class DynamicsModel:
    def __init__(self, path=MODEL_PATH):
        self.tree = GravityModel(path)
        self.sha256 = self.tree.sha256
        self.inertias = {}
        for link in ET.parse(path).getroot().findall('link'):
            el = link.find('inertial/inertia')
            if el is None:
                inertia = ((0.,)*3,)*3
            else:
                xx,xy,xz,yy,yz,zz = (float(el.get(k)) for k in ('ixx','ixy','ixz','iyy','iyz','izz'))
                if not all(math.isfinite(x) for x in (xx,xy,xz,yy,yz,zz)):
                    raise ValueError('Nonfinite link inertia')
                inertia = ((xx,xy,xz),(xy,yy,yz),(xz,yz,zz))
            r,_ = origin(link.find('inertial/origin'))
            self.inertias[link.get('name')] = mm(mm(r,inertia),tuple(zip(*r)))

    def evaluate(self, q, velocity, acceleration):
        if any(len(x)<6 or not all(math.isfinite(v) for v in x[:6])
               for x in (q,velocity,acceleration)):
            raise ValueError('Six finite q, velocity and acceleration values required')
        tau = [0.]*6
        pivots, axes = {}, {}

        def walk(link, r, p, w, alpha, a, ancestors):
            mass, com = self.tree.bodies[link]
            lever = mv(r,com)
            center = add(p,lever)
            ac = add(add(a,cross(alpha,lever)),cross(w,cross(w,lever)))
            force = scale(mass,sub(ac,(0.,0.,-9.80665)))
            inertia = mm(mm(r,self.inertias[link]),tuple(zip(*r)))
            moment = add(mv(inertia,alpha),cross(w,mv(inertia,w)))
            for i in ancestors:
                tau[i] += dot(axes[i],add(moment,cross(sub(center,pivots[i]),force)))
            for child,idx,(lr,lp),axis in self.tree.children.get(link,[]):
                offset = mv(r,lp)
                rr,pp = mm(r,lr),add(p,offset)
                aa = add(add(a,cross(alpha,offset)),cross(w,cross(w,offset)))
                ww,al,branch = w,alpha,ancestors
                if idx is not None:
                    joint_axis = mv(rr,axis)
                    pivots[idx],axes[idx] = pp,joint_axis
                    relative = scale(velocity[idx],joint_axis)
                    ww = add(w,relative)
                    al = add(add(alpha,scale(acceleration[idx],joint_axis)),cross(w,relative))
                    rr = mm(rr,rotation(axis,q[idx]))
                    branch = ancestors+(idx,)
                walk(child,rr,pp,ww,al,aa,branch)

        walk(self.tree.root,I3,ZERO,ZERO,ZERO,ZERO,())
        return tau

    def kinetic_energy(self, q, velocity):
        """Independent energy check using point/angular Jacobians, for validation."""
        axes,pivots = {},{}
        energy = 0.

        def walk(link,r,p,ancestors):
            nonlocal energy
            mass,com = self.tree.bodies[link]
            center = add(p,mv(r,com))
            v,w = ZERO,ZERO
            for i in ancestors:
                omega = scale(velocity[i],axes[i])
                w = add(w,omega)
                v = add(v,cross(omega,sub(center,pivots[i])))
            inertia = mm(mm(r,self.inertias[link]),tuple(zip(*r)))
            energy += .5*(mass*dot(v,v)+dot(w,mv(inertia,w)))
            for child,idx,(lr,lp),axis in self.tree.children.get(link,[]):
                rr,pp = mm(r,lr),add(p,mv(r,lp))
                branch = ancestors
                if idx is not None:
                    axes[idx],pivots[idx] = mv(rr,axis),pp
                    rr = mm(rr,rotation(axis,q[idx]))
                    branch = ancestors+(idx,)
                walk(child,rr,pp,branch)
        walk(self.tree.root,I3,ZERO,())
        return energy
