"""Device doubles shared by binding and dynamic feedback checks."""
import copy
from stararm_rs_feedback.config import NAMES
from test_rs_feedback import pair, FakeMonitor

LIMITS = dict(zip(NAMES, [[-145,145],[0,170],[0,200],[-80,90],[-90,90],[-130,130],[0,270]]))
Q = [0., .8, 1., .2, 0., 0., 0.]

class MutableMonitor(FakeMonitor):
    def snapshot(self):
        return getattr(self, 'states', None) or super().snapshot()

def setup(root):
    leader, robot = pair()
    robot.config.id = 'follower1'
    robot.config.joint_limits = copy.deepcopy(LIMITS)
    robot.config.gravity_compensation = False
    robot.calibration_fpath = root/'calibration.json'
    robot.calibration_fpath.write_text('{}')
    path=root/'spec.json'
    path.write_text('{}')
    return leader, robot, path
