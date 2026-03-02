import rclpy                            
from rclpy.action import ActionServer, CancelResponse  # 动作服务器与取消响应 / Action server & cancel response
from rclpy.node import Node
import time
from std_msgs.msg import Float32MultiArray
# from uservo.uservo_ex import uservo_ex
from robo_interfaces.msg import SetAngle  # 舵机角度控制消息 / Servo angle control message
from control_msgs.action import FollowJointTrajectory  # 机械臂轨迹动作 / Arm trajectory action
from control_msgs.action import GripperCommand  # 夹爪控制动作 / Gripper control action
from rclpy.callback_groups import ReentrantCallbackGroup  # 可重入回调组 / Reentrant callback group
from rclpy.executors import MultiThreadedExecutor  # 多线程执行器 / Executor for multithread
import math
from sensor_msgs.msg import JointState
# 常量定义 / Constants
ROBO_ACTION_NODE = 'cello_controller_node'  # 节点名称 / Node name
ROBO_CURRENT_ANGLE_SUBSCRIPTION = "joint_states"  # 当前关节角度话题 / Current joint states topic
ROBO_SET_ANGLE_PUBLISHER = 'set_angle_topic'  # 发布舵机设定角度话题 / Publish set_angle topic
ROBO_ARM_ACTION_SERVER = '/arm_controller/follow_joint_trajectory'  # 机械臂动作服务器名 / Arm action server name
ROBO_GRIPPER_ACTION_SERVER = '/hand_controller/gripper_cmd'  # 夹爪动作服务器名 / Gripper action server name

# 机器人关节名称与索引映射 / Joint name to index mapping
ROBO_TYPE_1 = "cello"
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
    """弧度转角度 / convert radians to degrees"""
    return radians * (180 / math.pi)

def meters_to_degrees(meters):
    """长度(米)转角度（基于臂长0.032m）/ convert meters to degrees"""
    return (meters / 0.032) * 100

def jointstate2servoangle(servo_id, joint_state):
    """关节状态转舵机命令角度 / joint state to servo angle"""
    if servo_id < 6:
        return radians_to_degrees(joint_state)
    elif servo_id == 6:
        return meters_to_degrees(joint_state) + 100


class RoboActionClient(Node):
    """机械臂与夹爪动作服务器节点 / Action server node for arm & gripper"""
    def __init__(self):
        super().__init__(ROBO_ACTION_NODE)
        # 使用可重入回调组支持并发 / Use reentrant callback group for concurrency
        self.callback_group = ReentrantCallbackGroup()
        # 创建机械臂轨迹跟踪动作服务器 / Arm trajectory action server
        self.arm_action_server = ActionServer(
            self,
            FollowJointTrajectory,
            ROBO_ARM_ACTION_SERVER,
            execute_callback=self.arm_execute_callback,
            cancel_callback=self.arm_cancel_callback,
            callback_group=self.callback_group,
        )
        # 创建夹爪控制动作服务器 / Gripper control action server
        self.gripper_action_server = ActionServer(
            self,
            GripperCommand,
            ROBO_GRIPPER_ACTION_SERVER,
            execute_callback=self.gripper_execute_callback,
            cancel_callback=self.gripper_cancel_callback,
            callback_group=self.callback_group,
        )
        # 订阅当前关节状态话题 / Subscribe current joint states
        self.current_angle_subscription = self.create_subscription(
            JointState,
            ROBO_CURRENT_ANGLE_SUBSCRIPTION,
            self.current_angle_callback,
            1,
            callback_group=self.callback_group,
        )
        # 发布舵机角度设定话题 / Publisher for SetAngle messages
        self.set_angle_publisher = self.create_publisher(
            SetAngle, ROBO_SET_ANGLE_PUBLISHER, 1
        )
        self.get_logger().info(f"{ROBO_ACTION_NODE} is ready.")  # 节点就绪日志 / ready log
        self.current_angle = [0.0] * 7  # 当前舵机角度缓存 / current servo angles
        self.last_time = 0  # 上一次时间戳 / last trajectory time index

    def arm_cancel_callback(self, cancel_request):
        """处理机械臂动作取消请求 / handle cancel request"""
        self.get_logger().info('Received arm cancel request')
        return CancelResponse.ACCEPT

    def current_angle_callback(self, msg):
        """接收并转换 JointState 到舵机角度 / receive joint states"""
        for name, pos in zip(msg.name, msg.position):
            idx = ROBO_TYPE_1_INDEX_JOINT_[name]
            self.current_angle[idx] = jointstate2servoangle(idx, pos)

    def arm_execute_callback(self, goal_handle):
        """执行轨迹点 / execute trajectory points"""
        trajectory = goal_handle.request.trajectory
        # self.get_logger().info(
        #     f'Receiving trajectory with {len(trajectory.points)} points.')
        self.last_time = 0
        # 遍历轨迹点 / iterate through trajectory
        for pt in trajectory.points:
            # 计算每段运行时间 / compute run duration
            tfs = pt.time_from_start.sec + pt.time_from_start.nanosec * 1e-9
            duration = max(tfs - self.last_time, 0.1)
            self.last_time = tfs
            # 构造 SetAngle 消息 / build SetAngle msg
            msg = SetAngle(
                servo_id=list(range(6)),
                target_angle=[0]*6,
                time=[int(duration*1000)]*6,
            )
            # 填充目标角度 / fill target angles
            for name, angle in zip(trajectory.joint_names, pt.positions):
                idx = ROBO_TYPE_1_INDEX_JOINT_[name]
                msg.target_angle[idx] = jointstate2servoangle(idx, angle)
            self.set_angle_publisher.publish(msg)  # 发布命令 / publish command
            time.sleep(duration)  # 等待完成 / wait
        # 完成后返回成功 / succeed goal
        goal_handle.succeed()
        return FollowJointTrajectory.Result()

    def gripper_cancel_callback(self, cancel_request):
        """处理夹爪取消请求 / handle gripper cancel"""
        self.get_logger().info('Received gripper cancel request')
        return CancelResponse.ACCEPT

    def gripper_execute_callback(self, goal_handle):
        """执行夹爪命令 / execute gripper command"""
        pos = goal_handle.request.command.position
        # 构造单舵机 SetAngle / build single servo command
        msg = SetAngle(
            servo_id=[6],
            target_angle=[jointstate2servoangle(6, pos)],
            time=[1000],
        )
        self.set_angle_publisher.publish(msg)
        goal_handle.succeed()
        return GripperCommand.Result()


def main(args=None):
    rclpy.init(args=args)  # 初始化 ROS 客户端 / init ROS
    node = RoboActionClient()
    executor = MultiThreadedExecutor()
    executor.add_node(node)  # 添加节点到执行器 / add node
    executor.spin()  # 运行执行器 / spin executor
    rclpy.shutdown()  # 退出 ROS / shutdown


if __name__ == '__main__':
    main()
