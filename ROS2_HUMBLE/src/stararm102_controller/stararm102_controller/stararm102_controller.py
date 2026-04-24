import rclpy
from rclpy.action import ActionServer, CancelResponse
from rclpy.node import Node
import time
from std_msgs.msg import Float32MultiArray
from robo_interfaces.msg import SetAngle
from control_msgs.action import FollowJointTrajectory
from control_msgs.action import GripperCommand
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
import math
from sensor_msgs.msg import JointState

# 常量定义
ROBO_ACTION_NODE = 'stararm102_controller_node'
ROBO_CURRENT_ANGLE_SUBSCRIPTION = "joint_states"
ROBO_SET_ANGLE_PUBLISHER = 'set_angle_topic'
ROBO_ARM_ACTION_SERVER = '/arm_controller/follow_joint_trajectory'
ROBO_GRIPPER_ACTION_SERVER = '/hand_controller/gripper_cmd'

# 机器人关节名称与索引映射
ROBO_TYPE_1 = "stararm102"
ROBO_TYPE_1_JOINT_ = [
    "joint1",
    "joint2",
    "joint3",
    "joint4",
    "joint5",
    "joint6",
    "joint7_left",
]
ROBO_TYPE_1_INDEX_JOINT_ = {name: idx for idx, name in enumerate(ROBO_TYPE_1_JOINT_)}

def radians_to_degrees(radians):
    """弧度转角度"""
    return radians * (180 / math.pi)

def meters_to_degrees(meters):
    """长度(米)转角度（基于臂长0.032m）"""
    return (meters / 0.032) * 100

def jointstate2servoangle(servo_id, joint_state):
    """关节状态转舵机命令角度"""
    if servo_id < 6:
        return radians_to_degrees(joint_state)
    elif servo_id == 6:
        # Joint7 axis was flipped in URDF, so invert the gripper mapping here too.
        return -radians_to_degrees(joint_state)


class RoboActionClient(Node):
    """机械臂与夹爪动作服务器节点"""
    def __init__(self):
        super().__init__(ROBO_ACTION_NODE)
        # 使用可重入回调组支持并发
        self.callback_group = ReentrantCallbackGroup()
        # 创建机械臂轨迹跟踪动作服务器
        self.arm_action_server = ActionServer(
            self,
            FollowJointTrajectory,
            ROBO_ARM_ACTION_SERVER,
            execute_callback=self.arm_execute_callback,
            cancel_callback=self.arm_cancel_callback,
            callback_group=self.callback_group,
        )
        # 创建夹爪控制动作服务器
        self.gripper_action_server = ActionServer(
            self,
            GripperCommand,
            ROBO_GRIPPER_ACTION_SERVER,
            execute_callback=self.gripper_execute_callback,
            cancel_callback=self.gripper_cancel_callback,
            callback_group=self.callback_group,
        )
        # 订阅当前关节状态话题
        self.current_angle_subscription = self.create_subscription(
            JointState,
            ROBO_CURRENT_ANGLE_SUBSCRIPTION,
            self.current_angle_callback,
            1,
            callback_group=self.callback_group,
        )
        # 发布舵机角度设定话题
        self.set_angle_publisher = self.create_publisher(
            SetAngle, ROBO_SET_ANGLE_PUBLISHER, 1
        )
        self.get_logger().info(f"{ROBO_ACTION_NODE} is ready.")
        self.current_angle = [0.0] * 7
        self.last_time = 0

    def arm_cancel_callback(self, cancel_request):
        """处理机械臂动作取消请求"""
        self.get_logger().info('Received arm cancel request')
        return CancelResponse.ACCEPT

    def current_angle_callback(self, msg):
        """接收并转换 JointState 到舵机角度"""
        for name, pos in zip(msg.name, msg.position):
            idx = ROBO_TYPE_1_INDEX_JOINT_[name]
            self.current_angle[idx] = jointstate2servoangle(idx, pos)

    def arm_execute_callback(self, goal_handle):
        """执行轨迹点"""
        trajectory = goal_handle.request.trajectory
        self.last_time = 0
        # 遍历轨迹点
        for pt in trajectory.points:
            # 计算每段运行时间
            tfs = pt.time_from_start.sec + pt.time_from_start.nanosec * 1e-9
            duration = max(tfs - self.last_time, 0.1)
            self.last_time = tfs
            # 构造 SetAngle 消息
            msg = SetAngle(
                servo_id=list(range(6)),
                target_angle=[0]*6,
                time=[int(duration*1000)]*6,
            )
            # 填充目标角度
            for name, angle in zip(trajectory.joint_names, pt.positions):
                idx = ROBO_TYPE_1_INDEX_JOINT_[name]
                msg.target_angle[idx] = jointstate2servoangle(idx, angle)
            self.set_angle_publisher.publish(msg)
            time.sleep(duration)
        # 完成后返回成功
        goal_handle.succeed()
        return FollowJointTrajectory.Result()

    def gripper_cancel_callback(self, cancel_request):
        """处理夹爪取消请求"""
        self.get_logger().info('Received gripper cancel request')
        return CancelResponse.ACCEPT

    def gripper_execute_callback(self, goal_handle):
        """执行夹爪命令"""
        pos = goal_handle.request.command.position
        # 构造单舵机 SetAngle
        msg = SetAngle(
            servo_id=[6],
            target_angle=[jointstate2servoangle(6, pos)],
            time=[1000],
        )
        self.set_angle_publisher.publish(msg)
        goal_handle.succeed()
        return GripperCommand.Result()


def main(args=None):
    rclpy.init(args=args)
    node = RoboActionClient()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
