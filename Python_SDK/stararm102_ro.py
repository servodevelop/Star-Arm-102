import fashionstar_uart_sdk as uservo
import serial
import time
import struct

SERVO_BAUDRATE = 1000000  # 舵机的波特率 / Servo communication baud rate
LEADER_PORT_NAME = "/dev/ttyUSB0"  # leader端口号
FOLLOWER_PORT_NAME_Arr = [
   #"/dev/ttyUSB1",
    "COM33"]  # follower端口号
    
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

    follower_uart_arr = [serial.Serial(port=NAME,baudrate=SERVO_BAUDRATE,parity=serial.PARITY_NONE,stopbits=1,bytesize=8,timeout=0) for NAME in FOLLOWER_PORT_NAME_Arr]
    follower_control_arr = [uservo.UartServoManager(uart) for uart in follower_uart_arr]
    leader_control.stop_on_control_mode(0xff,0x10,0x00)
    for i in range(len(FOLLOWER_PORT_NAME_Arr)):
        follower_control_arr[i].stop_on_control_mode(0xff,0x10,0x00)
    leader_control.reset_multi_turn_angle(0xff)
    for i in range(len(FOLLOWER_PORT_NAME_Arr)):
        follower_control_arr[i].reset_multi_turn_angle(0xff)
    get_frequency = measure_frequency()
    servo_ids = [0,1,2,3,4,5,6]
    target_angle = [0.0 for i in range(len(servo_ids))]

    target_angle_buffer = []
    target_angle_buffer_size = 60
    
    while True:
        leader_control.send_sync_servo_monitor(servo_ids)  
        for id in servo_ids: 
            target_angle[id] = leader_control.servos[id].angle_monitor
        target_angle[-1] = target_angle[-1]*1.5

        # 均值滤波
        target_angle_buffer.append(target_angle.copy())
        if len(target_angle_buffer) > target_angle_buffer_size:
            target_angle_buffer.pop(0)
        filtered_angle = [sum(col) / len(col) for col in zip(*target_angle_buffer)]

        filtered_angle[-1] = target_angle[-1]

        command_data_list = [struct.pack("<BlLHHH", i, int(filtered_angle[i]*10), 100, 50, 50, 0) for i in servo_ids]

        for i in range(len(FOLLOWER_PORT_NAME_Arr)):
            follower_control_arr[i].send_sync_multiturnanglebyinterval(14,7, command_data_list)
        time.sleep(0.001)

        freq = get_frequency()
        if freq is not None:
            print(f"当前运行频率: {freq:.2f} Hz")


if __name__ == "__main__":
    main()
