import math
import unittest

from stararm_rs_feedback.dynamics import DynamicsModel


class DynamicsTests(unittest.TestCase):
    def test_static_matches_existing_gravity(self):
        m=DynamicsModel()
        for q in ([0.]*6,[.2,.5,.7,-.3,.2,-.1],[-.5,1.1,.3,.7,-.4,.8]):
            for actual,expected in zip(m.evaluate(q,[0.]*6,[0.]*6),m.tree.evaluate(q)[0]):
                self.assertAlmostEqual(actual,expected,places=10)

    def test_mass_matrix_symmetric_positive_and_matches_kinetic_energy(self):
        m=DynamicsModel();q=[.2,.5,.7,-.3,.2,-.1]
        g=m.evaluate(q,[0.]*6,[0.]*6);cols=[]
        for i in range(6):
            a=[float(i==j) for j in range(6)]
            cols.append([t-b for t,b in zip(m.evaluate(q,[0.]*6,a),g)])
        for i in range(6):
            self.assertGreater(cols[i][i],0.)
            for j in range(6):self.assertAlmostEqual(cols[i][j],cols[j][i],places=10)
        v=[.4,-.3,.2,.5,-.4,.1]
        self.assertAlmostEqual(m.kinetic_energy(q,v),.5*sum(v[i]*cols[j][i]*v[j]
                               for i in range(6) for j in range(6)),places=10)

    def test_moving_torque_matches_lagrange_energy_differentiation(self):
        m=DynamicsModel()
        for q in ([.2,.5,.7,-.3,.2,-.1],[-.3,.9,1.1,.5,-.3,.7]):
            v=[.4,-.3,.2,.5,-.4,.1];a=[-.2,.7,-.4,.3,.2,-.6]
            actual=m.evaluate(q,v,a);g=m.tree.evaluate(q)[0]
            h=1e-4;k=1e-5
            def derivative_v(q,v,i):
                plus,minus=list(v),list(v);plus[i]+=k;minus[i]-=k
                return (m.kinetic_energy(q,plus)-m.kinetic_energy(q,minus))/(2*k)
            qp=[x+h*y+.5*h*h*z for x,y,z in zip(q,v,a)]
            qm=[x-h*y+.5*h*h*z for x,y,z in zip(q,v,a)]
            vp=[x+h*y for x,y in zip(v,a)];vm=[x-h*y for x,y in zip(v,a)]
            for i in range(6):
                plus,minus=list(q),list(q);plus[i]+=k;minus[i]-=k
                dtdq=(m.kinetic_energy(plus,v)-m.kinetic_energy(minus,v))/(2*k)
                dtdvdt=(derivative_v(qp,vp,i)-derivative_v(qm,vm,i))/(2*h)
                self.assertAlmostEqual(actual[i],dtdvdt-dtdq+g[i],delta=2e-6)


if __name__=='__main__':unittest.main()
