import fashionstar_uart_sdk as uservo
import serial
import time
import struct
import argparse

SERVO_BAUDRATE = 1000000  # 舵机的波特率 / Servo communication baud rate
LEADER_PORT_NAME = "/dev/ttyUSB2"  # leader端口号
FOLLOWER_PORT_NAME_Arr = [
   "/dev/ttyUSB3"
    # "COM33"
    ]  # follower端口号

class Button:
    """
    102_HD 按钮设置
    """
    key_state_0 = 0
    key_state_1 = 180
    key_state_3 = 90
    state = {
        "robot_unlock_state":key_state_0,   # 查询机械臂是否为解锁
        "lock":key_state_1,                 # 控制机械臂为锁定
        "unlock":key_state_3                # 控制机械臂为解锁
    }
    def __init__(self, id=7):
        self.id = id
        self.flag = False   # 记录状态是否发生转变

servo_ids = [0,1,2,3,4,5,6]

def measure_frequency():
    """
    测量循环运行频率（每秒运行次数）
    """
    count = 0
    start_time = time.time()
    
    def get_frequency():
        nonlocal count, start_time
        count += 1
        current_time = time.time()
        elapsed = current_time - start_time
        
        if elapsed >= 1.0:  # 每1秒计算一次频率
            frequency = count / elapsed
            count = 0
            start_time = current_time
            return frequency
        return None
    
    return get_frequency

def main(args):

    # 默认（102LD）
    button_enable = False
    button_id = 7
    filtered_size = 1

    if args.leader_type == "102HD":
        button_enable = True
        button_id = 7
        filtered_size = 1
    elif args.leader_type == "102LD" or args.leader_type is None:
        button_enable = False
        button_id = 7
        filtered_size = 1
    else:
        print(f"警告：未知 leader.type={args.leader_type}，使用默认102LD配置")

    if args.button is not None:
        button_enable = args.button
    if args.button_enable:
        button_enable = True
    if args.button_disable:
        button_enable = False

    if args.button_id is not None:
        button_id = args.button_id
    if args.filtered_size is not None:
        filtered_size = args.filtered_size

    # 初始化leader
    leader_uart = serial.Serial(port=LEADER_PORT_NAME,baudrate=SERVO_BAUDRATE,parity=serial.PARITY_NONE,stopbits=1,bytesize=8,timeout=0)
    leader_control = uservo.UartServoManager(leader_uart)
    leader_control.stop_on_control_mode(0xff,0x10,0x00)     # 解锁机械臂
    leader_control.reset_multi_turn_angle(0xff)             # 重置圈数

    if button_enable:
        button_get = leader_control.ping(button_id)
        if button_get==False:
            raise ValueError(f"找不到button_id={button_id}")

    # 初始化follower
    follower_uart_arr = [serial.Serial(port=NAME,baudrate=SERVO_BAUDRATE,parity=serial.PARITY_NONE,stopbits=1,bytesize=8,timeout=0) for NAME in FOLLOWER_PORT_NAME_Arr]
    follower_control_arr = [uservo.UartServoManager(uart) for uart in follower_uart_arr]
    [follower_control_arr[i].stop_on_control_mode(0xff,0x10,0x00) for i in range(len(FOLLOWER_PORT_NAME_Arr))]  # 解锁机械臂
    [follower_control_arr[i].reset_multi_turn_angle(0xff) for i in range(len(FOLLOWER_PORT_NAME_Arr))]          # 重置圈数
    
    button = Button(id=button_id)

    get_frequency = measure_frequency()

    target_angle = [0.0 for i in range(len(servo_ids))]

    target_angle_buffer = []        # 均值滤波缓存
    target_angle_buffer_size = filtered_size   # 滤波数据大小
    
    while True:
        leader_servo_board_ids = servo_ids.copy()
        if button_enable:
            leader_servo_board_ids.append(button.id)
        leader_control.send_sync_servo_monitor(leader_servo_board_ids)
        for id in servo_ids: 
            target_angle[id] = leader_control.servos[id].angle_monitor
        target_angle[-1] = max(0,min(target_angle[-1]*1.5,90))  # 防止角度过大

        # 均值滤波
        target_angle_buffer.append(target_angle.copy())
        if len(target_angle_buffer) > target_angle_buffer_size:
            target_angle_buffer.pop(0)
        filtered_angle = [sum(col) / len(col) for col in zip(*target_angle_buffer)]

        filtered_angle[-1] = target_angle[-1]   # 末端不参与滤波

        if button_enable:
            if(leader_control.servos[button.id].angle_monitor == button.state["lock"]):
                if(not button.flag):
                    for i in range(len(servo_ids)-1):
                        leader_control.stop_on_control_mode(servo_ids[i],0x11,0x00)
                    button.flag = True
            else:
                if(button.flag):
                    leader_control.stop_on_control_mode(0xff,0x10,0x00)
                    button.flag = False

        command_data_list = [struct.pack("<BlLHHH", i, int(filtered_angle[i]*10), 100, 50, 50, 0) for i in servo_ids]

        for i in range(len(FOLLOWER_PORT_NAME_Arr)):
            follower_control_arr[i].send_sync_multiturnanglebyinterval(14,7, command_data_list)
        time.sleep(0.001)

        freq = get_frequency()
        if freq is not None:
            print(f"当前运行频率: {freq:.2f} Hz")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="leader类型自动配置按键与滤波参数")

    parser.add_argument("--leader_type", type=str, default=None, help="设备型号：102HD / 102LD，默认102LD")
    parser.add_argument("--button_enable", action="store_true", help="启用按键")
    parser.add_argument("--button_disable", action="store_true", help="禁用按键")
    parser.add_argument("--button", type=lambda x: (str(x).lower() == 'true'), default=None,
                        help="直接指定按键状态，True开启 / False关闭")
    parser.add_argument("--button_id", type=int, default=None, help="按键ID")
    parser.add_argument("--filtered_size", type=int, default=None, help="均值滤波窗口大小")

    args = parser.parse_args()
    main(args)
