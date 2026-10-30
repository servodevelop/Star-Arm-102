import fashionstar_uart_sdk as uservo
import serial
import time
import struct

SERVO_BAUDRATE = 1000000  # 舵机的波特率 / Servo communication baud rate
LEADER_PORT_NAME = "/dev/ttyUSB0"  # leader端口号
FOLLOWER_PORT_NAME = "/dev/ttyUSB1"  # follower端口号

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


def main(args=None):
    leader_uart = serial.Serial(port=LEADER_PORT_NAME,baudrate=SERVO_BAUDRATE,parity=serial.PARITY_NONE,stopbits=1,bytesize=8,timeout=0)
    leader_control = uservo.UartServoManager(leader_uart)

    follower_uart = serial.Serial(port=FOLLOWER_PORT_NAME,baudrate=SERVO_BAUDRATE,parity=serial.PARITY_NONE,stopbits=1,bytesize=8,timeout=0)
    follower_control = uservo.UartServoManager(follower_uart)
    leader_control.stop_on_control_mode(0xff,0x10,0x00)
    follower_control.stop_on_control_mode(0xff,0x10,0x00)
    leader_control.reset_multi_turn_angle(0xff)
    follower_control.reset_multi_turn_angle(0xff)
    get_frequency = measure_frequency()
    servo_ids = [0,1,2,3,4,5,6]
    target_angle = [0.0 for i in range(len(servo_ids))]
    while True:
        leader_control.send_sync_servo_monitor(servo_ids)  
        for id in servo_ids: 
            target_angle[id] = leader_control.servos[id].angle_monitor

        command_data_list = [struct.pack("<BlLHHH", i, int(target_angle[i]*10), 100, 50, 50, 0) for i in servo_ids]
        follower_control.send_sync_multiturnanglebyinterval(14,7, command_data_list)
        time.sleep(0.001)

        freq = get_frequency()
        if freq is not None:
            print(f"当前运行频率: {freq:.2f} Hz")


if __name__ == "__main__":
    main()