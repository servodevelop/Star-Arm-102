#!/usr/bin/env python
# coding:utf-8
"""
机械臂驱动节点
Robot arm driver node
"""
import rclpy
from rclpy.node import Node
from robo_interfaces.srv import ReadData, WriteData
from robo_interfaces.msg import SetAngle
import struct
from sensor_msgs.msg import JointState
import math
import fashionstar_uart_sdk as uservo
import time
import serial

ROBO_DRIVER_NODE = "robo_driver_node"  # 驱动节点名称 / driver node name
ROBO_SET_ANGLE_SUBSCRIBER = "set_angle_topic"  # 设置角度话题 / topic for setting angles

# PORT_NAME: 设置舵机串口号，默认使用/dev/ttyUSB0，当需要在同一个设备上使用多个机械臂时，需要修改该参数
# Port name: Serial port for servos, default "/dev/ttyUSB0", change when using multiple arms
# Whether to check servo angle on power-up, default True to ensure consistent init
SERVO_PORT_NAME = "/dev/ttyUSB0"  # 舵机串口号 <<< 修改为实际串口号
                                # Servo serial port <<< modify to actual port name
SERVO_BAUDRATE = 1000000  # 舵机的波特率 / Servo communication baud rate
servo_ids = list()

"""
舵机转手臂控制通用类
Universal class for servo-to-arm control
"""

class uservo_ex:
    JOINT_ = [
        "joint1",
        "joint2",
        "joint3",
        "joint4",
        "joint5",
        "joint6",
        "joint7_left",
    ]
    ROBO_TYPE_INDEX_JOINT = {
        value: index for index, value in enumerate(JOINT_)
    }
    SRV_NUM =7


    # 参数 / Parameters:
    def __init__(self,robo_type,log = None):
        self.ROBO_TYPE = robo_type
        self.INDEX_JOINT_ = {value: index for index, value in enumerate(self.JOINT_)}
        self.log = log
        # 初始化串口 / Initialize serial port
        try:
            self.uart = serial.Serial(port=SERVO_PORT_NAME,baudrate=SERVO_BAUDRATE,parity=serial.PARITY_NONE,stopbits=1,bytesize=8,timeout=0)
        except serial.SerialException as e:
            if self.log != None:
                self.log.error(f"{e}")
            raise ValueError(f"串口初始化失败: {e}")  # Serial port init failed
        try:
            self.uservo = uservo.UartServoManager(self.uart)
        except Exception as e:
            raise

        self.servo_ids = [0,1,2,3,4,5,6]
        self.ZERO_ANGLE = [0 for _ in range(self.SRV_NUM)]
        self.ZERO_ANGLE[6] = 500
        self.reset_multi_turn_angle(0xff)
        time.sleep(0.1)

    # 将角度转为弧度 / Convert degrees to radians
    @classmethod
    def degrees_to_radians(cls, degrees):
        radians = degrees * (math.pi / 180)
        return radians

    # 将角度转为米 / Convert degrees back to meters
    @classmethod
    def degrees_to_meters(cls, degrees):
        meters = (degrees / 100) * 0.032
        return meters

    # 将舵机角度转换为关节位置 / Servo angle to joint state mapping
    @classmethod
    def servoangle2jointstate(cls, servo_id, servo_angle):
        if servo_id in range(6):
            return cls.degrees_to_radians(servo_angle)
        elif servo_id == 6:
            return cls.degrees_to_meters(servo_angle-100)

    # 设置角度（指定转速） / Send angle commands with specified speed
    def set_angle_by_interval(self, size, command_data_list):
        self.uservo.send_sync_multiturnanglebyinterval(
            self.uservo.CODE_SET_SERVO_ANGLE_MTURN_BY_INTERVAL,
            size, command_data_list
        )

    # 查询角度 / Query current servo angle
    def query_servo_current_angle(self, servo_id):
        if servo_id in self.uservo.servos:
            return self.uservo.query_servo_angle(servo_id)

    # 失能舵机 / Disable servo torque
    def disable_torque(self, servo_id):
        self.servo_stop(servo_id)

    # 重设指定舵机多圈圈数 / Reset multi-turn count for a single servo
    def reset_multi_turn_angle(self, servo_id):
        self.uservo.disable_torque(servo_id)
        time.sleep(0.05)
        self.uservo.reset_multi_turn_angle(servo_id)

    # 停止并释放锁力 / Stop servo and release torque lock
    def servo_stop(self, servo_id, mode=2, power=500):
        self.uservo.stop_on_control_mode(servo_id, mode, power)

class Arm_contorl(Node):

    def __init__(self):
        super().__init__(ROBO_DRIVER_NODE)
        self.declare_parameter("robo_type", "robo")

        self.declare_parameter('lock', 'enable')

        self.robo_type = (self.get_parameter("robo_type").get_parameter_value().string_value)
        self.lock = (self.get_parameter("lock").get_parameter_value().string_value)

        try:
            self.Servo = uservo_ex(self.robo_type,log = self.get_logger())
        except ValueError as e:
            raise
        self.target_angle = self.Servo.ZERO_ANGLE
        # self.target_angle 初始目标角度列表 / initial target angle list
        self.interval = [1500 for _ in range(self.Servo.SRV_NUM)]
        self.current_angle = [0.0 for _ in range(self.Servo.SRV_NUM)]
        if(self.lock == "enable"):
            self.arm_move_by_time()
        else:
            self.Servo.disable_torque(0xff)

        # 创建话题：发布joint_states / Create publisher for joint_states topic
        self.joint_states_publisher = self.create_publisher(
            JointState, "joint_states", 10
        )
        # 创建话题：处理设置角度 / Create subscription for SetAngle commands
        self.angle_subscribers = self.create_subscription(
            SetAngle, ROBO_SET_ANGLE_SUBSCRIBER, self.set_angle_callback, 10
        )
        self.timer2 = self.create_timer(0.03, self.timer_callback)
        self.get_logger().info(f"初始化完成 / Initialization complete")

    def node_close(self):
        pass
        # self.Servo.servo_all_stop()

    # 新的执行命令 / Callback for new angle commands
    def set_angle_callback(self, msg):
        for i in range(len(msg.servo_id)):
            id = msg.servo_id[i]
            self.target_angle[id] = int(10*msg.target_angle[i])
            if int(msg.time[i]) < 40:
                (msg.time[i]) = 40
            self.interval[id] = int(msg.time[i])+400

            self.arm_move_by_time()

    # 定时任务 / Timer callback
    def timer_callback(self):
        self.publish_current_angle()

    # 查询舵机角度发布 / Query servo angles and publish
    def publish_current_angle(self):
        JointState_msg = JointState()
        JointState_msg.header.stamp = self.get_clock().now().to_msg()
        JointState_msg.velocity = []
        JointState_msg.effort = []
        self.Servo.uservo.send_sync_servo_monitor(self.Servo.servo_ids)

        for i in range(self.Servo.SRV_NUM):
            self.current_angle[i] = self.Servo.uservo.servos[i].angle_monitor
            JointState_msg.name.append(self.Servo.JOINT_[i])
            JointState_msg.position.append(
                self.Servo.servoangle2jointstate(
                    servo_id=i, servo_angle=self.current_angle[i]
                )
            )
        self.joint_states_publisher.publish(JointState_msg)

    # 默认：控制by时间 / Default control mode: time-based
    def arm_move_by_time(self):
        acc = [0.0 for _ in range(self.Servo.SRV_NUM)]
        for i in range(self.Servo.SRV_NUM):
            acc[i] = int(self.interval[i]/2)
        command_data_list = [struct.pack("<BlLHHH", i, self.target_angle[i], self.interval[i], acc[i], acc[i], 8000) for i in range(self.Servo.SRV_NUM)]
        self.Servo.set_angle_by_interval(self.Servo.SRV_NUM, command_data_list)



def main(args=None):
    rclpy.init(args=args)
    try:
        robo_driver_node = Arm_contorl()
    except Exception as e:
        return

    try:
        rclpy.spin(robo_driver_node)
    except KeyboardInterrupt:
        pass
    finally:
        robo_driver_node.node_close()
        robo_driver_node.destroy_node()


if __name__ == "__main__":
    main()
