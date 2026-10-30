import fashionstar_uart_sdk as uservo
import serial
import time
import struct

SERVO_BAUDRATE = 1000000  # 舵机的波特率 / Servo communication baud rate
LEADER_PORT_NAME = "/dev/ttyUSB0"  # leader端口号
FOLLOWER_PORT_NAME_Arr = [
   "/dev/ttyUSB1"
    # "COM33"
    ]  # follower端口号

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

class Hover_Mode:
    def __init__(self,leader_control:uservo.UartServoManager):
        self.ERR_ANGLE_TRESHOLD = 0.1
        self.leader_control = leader_control                    # 获取leader控制
        self.last_angle = [0.0 for i in range(len(servo_ids))]  # 前一时刻角度
        # self.last_currents = [0 for i in range(len(servo_ids))] # 前一时刻电流
        self.time_step = time.time()
        self.flag = False               # 状态标志
        self.lock = False               # 是否锁定

    def hover_mode(self,filtered_angle):
        if self.lock:
            # if self.flag:
            #     self.last_currents = [servos[id].current for id in servo_ids]
            #     self.flag = False
            # else:
            #     currents = [servos[i].current for i in servo_ids]
            #     err_current = sum(abs(last - filt) for last,filt in zip(self.last_currents,currents))
            #     if err_current > 700:
            #         self.leader_control.stop_on_control_mode(0xff,0x10,0x00)
            #         self.lock = False
            if self.flag:
                self.last_angle = [self.leader_control.servos[i].angle_monitor for i in range(len(servo_ids)-1)]
                self.flag = False
            else:
                err_angle = sum(abs(self.last_angle[i] - self.leader_control.servos[i].angle_monitor) for i in range(len(servo_ids)-1))
                if err_angle > 5:
                    self.leader_control.stop_on_control_mode(0xff,0x10,0x00)
                    self.lock = False
        else:
            """
            没有锁定状态
            """
            err_angle = sum(abs(self.last_angle[i] - filtered_angle[i]) for i in range(len(servo_ids)-1))   # 获取所有角度误差和
            self.last_angle = filtered_angle    # 更新记录这一时刻的角度
            if self.flag == False and err_angle <= self.ERR_ANGLE_TRESHOLD:
                self.flag = True
                self.time_step = time.time()
            elif self.flag and err_angle > self.ERR_ANGLE_TRESHOLD:
                self.flag = False
            elif self.flag and time.time() - self.time_step > 1:
                self.lock = True
                self.leader_control.send_sync_servo_monitor(servo_ids)
                command_data_list = [struct.pack("<BlLHHH", i, int(self.leader_control.servos[i].angle_monitor*10), 100, 50, 50, int(65535/16)) for i in range(len(servo_ids)-1)]
                self.leader_control.send_sync_multiturnanglebyinterval(14,6, command_data_list)

        return filtered_angle


def main(args=None):
    # 初始化leader
    leader_uart = serial.Serial(port=LEADER_PORT_NAME,baudrate=SERVO_BAUDRATE,parity=serial.PARITY_NONE,stopbits=1,bytesize=8,timeout=0)
    leader_control = uservo.UartServoManager(leader_uart)
    leader_control.stop_on_control_mode(0xff,0x10,0x00)
    leader_control.reset_multi_turn_angle(0xff)

    # 初始化follower
    follower_uart_arr = [serial.Serial(port=NAME,baudrate=SERVO_BAUDRATE,parity=serial.PARITY_NONE,stopbits=1,bytesize=8,timeout=0) for NAME in FOLLOWER_PORT_NAME_Arr]
    follower_control_arr = [uservo.UartServoManager(uart) for uart in follower_uart_arr]
    [follower_control_arr[i].stop_on_control_mode(0xff,0x10,0x00) for i in range(len(FOLLOWER_PORT_NAME_Arr))]  
    [follower_control_arr[i].reset_multi_turn_angle(0xff) for i in range(len(FOLLOWER_PORT_NAME_Arr))]
    
    get_frequency = measure_frequency()
    target_angle = [0.0 for i in range(len(servo_ids))]

    target_angle_buffer = []        # 均值滤波缓存
    target_angle_buffer_size = 60   # 滤波数据大小
    hover_Mode = Hover_Mode(leader_control)
    
    while True:
        leader_control.send_sync_servo_monitor(servo_ids)  
        for id in servo_ids: 
            target_angle[id] = leader_control.servos[id].angle_monitor
        target_angle[-1] = max(0,min(target_angle[-1]*1.5,90))  # 防止角度过大

        # 均值滤波
        target_angle_buffer.append(target_angle.copy())
        if len(target_angle_buffer) > target_angle_buffer_size:
            target_angle_buffer.pop(0)
        filtered_angle = [sum(col) / len(col) for col in zip(*target_angle_buffer)]

        filtered_angle[-1] = target_angle[-1]   # 末端不参与滤波

        # leader悬停模式
        filtered_angle = hover_Mode.hover_mode(filtered_angle)

        command_data_list = [struct.pack("<BlLHHH", i, int(filtered_angle[i]*10), 100, 50, 50, 0) for i in servo_ids]

        for i in range(len(FOLLOWER_PORT_NAME_Arr)):
            follower_control_arr[i].send_sync_multiturnanglebyinterval(14,7, command_data_list)
        time.sleep(0.001)

        freq = get_frequency()
        if freq is not None:
            print(f"当前运行频率: {freq:.2f} Hz")


if __name__ == "__main__":
    main()
