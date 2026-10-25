import serial
import struct
import time

BAUDRATE = 1000000
USB = "/dev/ttyUSB2"    # 替换为实际的串口名称
# USB = 'COM3'  # Windows系统下的串口名称

class ServoProtocol:
    
    def __init__(self, port, baudrate=115200, timeout=0.1):
        self.serial = serial.Serial(port, baudrate, timeout=timeout)
        
    def __del__(self):
        if hasattr(self, 'serial') and self.serial.is_open:
            self.serial.close()
    
    def calculate_checksum(self, data):
        return sum(data) % 256
    
    def write_public_parameters(self, 
                               servo_id=0,                      # 舵机ID
                               need_response=0,                 # 控制送出后是否响应
                               baudrate=5,                      # 波特率
                               stall_protection=0,              # 堵转保护开关
                               stall_power_limit=6000,          # 堵转功率上限
                               low_voltage_protection=4000,     # 低电压保护值
                               high_voltage_protection=12600,   # 高电压保护值
                               temperature_protection=735,      # 温度保护值
                               power_protection=20000,          # 功率保护值
                               current_protection=4000,         # 电流保护值
                               startup_force=0,                 # 启动力度
                               hysteresis_percent=80,           # 迟滞百分比
                               power_lock_switch=0,             # 上电锁力开关
                               wheel_mode_brake_switch=0,       # 轮式模式刹车开关
                               angle_limit_switch=1,            # 角度限制开关
                               soft_start_switch=0,             # 上电缓启动开关
                               soft_start_time=3000,            # 上电缓启动时间
                               angle_upper_limit=1800,        # 角度上限
                               angle_lower_limit=-1800):       # 角度下限

        # 构建数据包
        header = bytes([0x12, 0x4C, 0x06, 0x21])

        # 构建参数部分
        params = bytearray([
            servo_id,
            0x01,
            need_response,
            servo_id, 0x00,  # 这个会跟着ID变动
            baudrate,
            stall_protection
        ])
        # 添加堵转功率上限 (2字节，小端序)
        params.extend(struct.pack('<H', stall_power_limit))
        # 添加低压保护电压 (2字节，小端序)
        params.extend(struct.pack('<H', low_voltage_protection))
        # 添加高压保护电压 (2字节，小端序)
        params.extend(struct.pack('<H', high_voltage_protection))
        # 添加温度保护值 (2字节，小端序)
        params.extend(struct.pack('<H', temperature_protection))
        # 添加功率保护值 (2字节，小端序)
        params.extend(struct.pack('<H', power_protection))
        # 添加电流保护值 (2字节，小端序)
        params.extend(struct.pack('<H', current_protection))
        # 添加启动力度
        params.append(startup_force)
        # 添加迟滞百分比
        params.append(hysteresis_percent)
        # 添加上电锁力开关
        params.append(power_lock_switch)
        # 添加轮式模式刹车开关
        params.append(wheel_mode_brake_switch)
        # 添加角度限制开关
        params.append(angle_limit_switch)
        # 添加上电缓启动开关
        params.append(soft_start_switch)
        # 添加上电缓启动时间 (2字节，小端序)
        params.extend(struct.pack('<H', soft_start_time))
        # 添加角度上限 (2字节，小端序)
        params.extend(struct.pack('<H', angle_upper_limit))
        # 添加角度下限 (2字节，小端序)
        params.extend(struct.pack('<h', angle_lower_limit))
        # 添加保留字节
        params.extend([0x00, 0x00])
        # 计算校验和
        checksum = self.calculate_checksum(header + params)
        # 构建完整的数据包
        packet = header + params + bytes([checksum])
        # 发送数据包
        try:
            self.serial.write(packet)
            return True
        except Exception as e:
            print(f"发送数据失败: {e}")
            return False
    
    def write_internal_parameters(self, 
                                 servo_id=0,              # 舵机ID
                                 kp=800,                  # 比例系数
                                 kd=50,                   # 微分系数
                                 ki=0,                    # 积分系数
                                 bias=0,                  # 偏置
                                 hold_kp=800,             # 保持比例系数
                                 hold_kd=50,              # 保持微分系数
                                 hold_bias=0,             # 保持偏置
                                 forward_direction=0,     # 正转方向
                                 dead_zone=1):            # 死区

        # 构建数据包
        header = bytes([0x13, 0x4D, 0xC4, 0x1A])
        # 构建参数部分
        params = bytearray([servo_id])
        # 添加Kp (2字节，小端序)
        params.extend(struct.pack('<H', kp))
        # 添加Kd (2字节，小端序)
        params.extend(struct.pack('<H', kd))
        # 添加Ki (2字节，小端序)
        params.extend(struct.pack('<H', ki))
        # 添加Bias (2字节，小端序)
        params.extend(struct.pack('<H', bias))
        # 添加Hold Kp (2字节，小端序)
        params.extend(struct.pack('<H', hold_kp))
        # 添加Hold Kd (2字节，小端序)
        params.extend(struct.pack('<H', hold_kd))
        # 添加Hold Bias (2字节，小端序)
        params.extend(struct.pack('<H', hold_bias))
        # 添加固定字节
        params.extend([0x10, 0x0E, 0x00, 0x00, 0xA4, 0x0B])
        # 添加正转
        params.append(forward_direction)
        # 添加固定字节
        params.append(0x05)
        # 添加死区
        params.append(dead_zone)
        # 添加固定字节
        params.extend([0x00, 0x01])
        # 计算校验和
        checksum = self.calculate_checksum(header + params)
        # 构建完整的数据包
        packet = header + params + bytes([checksum])
        # 发送数据包
        try:
            self.serial.write(packet)
            return True
        except Exception as e:
            print(f"发送数据失败: {e}")
            return False
        
    def read_public_parameters(self, servo_id=0x00):
        # 清空串口缓冲区
        self.serial.reset_input_buffer()
        # 构建数据包
        cmd_data = [0x12, 0x4C, 0x05, 0x01, servo_id]
        checksum = self.calculate_checksum(cmd_data)
        packet = bytes(cmd_data + [checksum])
        # 发送数据包
        try:
            self.serial.write(packet)
            # 等待回包
            time.sleep(0.2)  # 增加等待时间
            # 读取回包
            if self.serial.in_waiting:
                response = self.serial.read(self.serial.in_waiting)
                # 检查回包长度是否足够
                if len(response) < 38:  # 回包总长度应为39字节
                    print(f"回包数据不完整: {response.hex(' ')}")
                    return False
                
                # 解析回包数据
                result = {
                    'header': response[0:4].hex(' '),  # 回包帧头
                    'id': response[4],                 # ID
                    'unknown1': response[5],           # 01
                    'need_response': response[6],      # 控制送出后是否响应
                    'id_related': response[7:9].hex(' '),  # 这个会跟着ID变动
                    'baudrate': response[9],           # 波特率
                    'stall_protection': response[10],  # 堵转保护开关
                    'stall_power_limit': struct.unpack('<H', response[11:13])[0],  # 堵转功率上限
                    'low_voltage_protection': struct.unpack('<H', response[13:15])[0],  # 低压保护电压
                    'high_voltage_protection': struct.unpack('<H', response[15:17])[0],  # 高压保护电压
                    'temperature_protection': struct.unpack('<H', response[17:19])[0],  # 温度保护值
                    'power_protection': struct.unpack('<H', response[19:21])[0],  # 功率保护值
                    'current_protection': struct.unpack('<H', response[21:23])[0],  # 电流保护值
                    'startup_force': response[23],     # 启动力度
                    'hysteresis_percent': response[24],  # 迟滞百分比
                    'power_lock_switch': response[25],  # 上电锁力开关
                    'wheel_mode_brake_switch': response[26],  # 轮式模式刹车开关
                    'angle_limit_switch': response[27],  # 角度限制开关
                    'soft_start_switch': response[28],  # 上电缓启动开关
                    'soft_start_time': struct.unpack('<H', response[29:31])[0],  # 上电缓启动时间
                    'angle_upper_limit': struct.unpack('<H', response[31:33])[0],  # 角度上限
                    'angle_lower_limit': struct.unpack('<h', response[33:35])[0],  # 角度下限
                    'reserved': response[35:37].hex(' '),  # 保留字节
                    'checksum': response[37]           # 校验和
                }
                
                # 打印解析结果
                print("公开参数解析结果:")
                for key, value in result.items():
                    print(f"{key}: {value}")
                
                return result
            else:
                print("未收到回包数据")
                return False
        except Exception as e:
            print(f"读取数据失败: {e}")
            return False
    
    def read_internal_parameters(self, servo_id=0x00):
        # 清空串口缓冲区
        self.serial.reset_input_buffer()
        # 构建数据包
        cmd_data = [0x13, 0x4D, 0xC5, 0x01, servo_id]
        checksum = self.calculate_checksum(cmd_data)
        packet = bytes(cmd_data + [checksum])
        # 发送数据包
        try:
            self.serial.write(packet)
            # 等待回包
            time.sleep(0.2)  # 增加等待时间
            # 读取回包
            if self.serial.in_waiting:
                response = self.serial.read(self.serial.in_waiting)
                # 检查回包长度是否足够
                if len(response) < 31:  # 回包总长度应为31字节
                    print(f"回包数据不完整: {response.hex(' ')}")
                    return False
                
                # 解析回包数据
                result = {
                    'header': response[0:4].hex(' '),  # 回包帧头
                    'id': response[4],                 # ID
                    'kp': struct.unpack('<H', response[5:7])[0],  # Kp
                    'kd': struct.unpack('<H', response[7:9])[0],  # Kd
                    'ki': struct.unpack('<H', response[9:11])[0],  # Ki
                    'bias': struct.unpack('<H', response[11:13])[0],  # Bias
                    'hold_kp': struct.unpack('<H', response[13:15])[0],  # Hold Kp
                    'hold_kd': struct.unpack('<H', response[15:17])[0],  # Hold Kd
                    'hold_bias': struct.unpack('<H', response[17:19])[0],  # Hold Bias
                    'unknown1': response[19:25].hex(' '),  # 未知字节 10 0E 00 00 A4 0B
                    'forward_direction': response[25],  # 正转
                    'unknown2': response[26],          # 05
                    'dead_zone': response[27],         # 死区
                    'unknown3': response[28:30].hex(' '),  # 00 01
                    'checksum': response[30]           # 校验和
                }
                
                # 打印解析结果
                print("内部参数解析结果:")
                for key, value in result.items():
                    print(f"{key}: {value}")
                
                return result
            else:
                print("未收到回包数据")
                return False
        except Exception as e:
            print(f"读取数据失败: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    # 创建舵机通信协议对象
    # 注意：需要替换为实际的串口端口
    servo = ServoProtocol(USB,baudrate=BAUDRATE)  # Windows系统示例，Linux系统可能是"/dev/ttyUSB0"
    
    # 定义0-6号舵机的公开参数字典
    public_params_dict = {
        0: {  # 舵机ID 0的参数
            'need_response':0,
            "baudrate": 8,
            "stall_protection": 0,
            "stall_power_limit": 6000,
            "low_voltage_protection": 4000,
            "high_voltage_protection": 12600,
            "temperature_protection": 1058,
            "power_protection": 10000,
            "current_protection": 6000,
            "startup_force": 0,
            "hysteresis_percent": 80,
            "power_lock_switch": 0,
            "wheel_mode_brake_switch": 0,
            "angle_limit_switch": 1,
            "soft_start_switch": 0,
            "soft_start_time": 3000,
            "angle_upper_limit": 1800,
            "angle_lower_limit": -1800
        },
        1: {  # 舵机ID 1的参数
            'need_response':0,
            "baudrate": 8,
            "stall_protection": 0,
            "stall_power_limit": 50000,
            "low_voltage_protection": 4000,
            "high_voltage_protection": 12600,
            "temperature_protection": 835,
            "power_protection": 50000,
            "current_protection": 6000,
            "startup_force": 0,
            "hysteresis_percent": 80,
            "power_lock_switch": 0,
            "wheel_mode_brake_switch": 0,
            "angle_limit_switch": 1,
            "soft_start_switch": 0,
            "soft_start_time": 3000,
            "angle_upper_limit": 1800,
            "angle_lower_limit": -1800
        },
        2: {  # 舵机ID 2的参数
            'need_response':0,
            "baudrate": 8,
            "stall_protection": 0,
            "stall_power_limit": 50000,
            "low_voltage_protection": 4000,
            "high_voltage_protection": 12600,
            "temperature_protection": 835,
            "power_protection": 50000,
            "current_protection": 6000,
            "startup_force": 0,
            "hysteresis_percent": 80,
            "power_lock_switch": 0,
            "wheel_mode_brake_switch": 0,
            "angle_limit_switch": 1,
            "soft_start_switch": 0,
            "soft_start_time": 3000,
            "angle_upper_limit": 1800,
            "angle_lower_limit": -1800
        },
        3: {  # 舵机ID 3的参数
            'need_response':0,
            "baudrate": 8,
            "stall_protection": 0,
            "stall_power_limit": 30000,
            "low_voltage_protection": 4000,
            "high_voltage_protection": 12600,
            "temperature_protection": 1058,
            "power_protection": 30000,
            "current_protection": 6000,
            "startup_force": 0,
            "hysteresis_percent": 80,
            "power_lock_switch": 0,
            "wheel_mode_brake_switch": 0,
            "angle_limit_switch": 1,
            "soft_start_switch": 0,
            "soft_start_time": 3000,
            "angle_upper_limit": 1800,
            "angle_lower_limit": -1800
        },
        4: {  # 舵机ID 4的参数
            'need_response':0,
            "baudrate": 8,
            "stall_protection": 0,
            "stall_power_limit": 6000,
            "low_voltage_protection": 4000,
            "high_voltage_protection": 12600,
            "temperature_protection": 1058,
            "power_protection": 10000,
            "current_protection": 6000,
            "startup_force": 0,
            "hysteresis_percent": 80,
            "power_lock_switch": 0,
            "wheel_mode_brake_switch": 0,
            "angle_limit_switch": 1,
            "soft_start_switch": 0,
            "soft_start_time": 3000,
            "angle_upper_limit": 1800,
            "angle_lower_limit": -1800
        },
        5: {  # 舵机ID 5的参数
            'need_response':0,
            "baudrate": 8,
            "stall_protection": 0,
            "stall_power_limit": 6000,
            "low_voltage_protection": 4000,
            "high_voltage_protection": 12600,
            "temperature_protection": 1058,
            "power_protection": 10000,
            "current_protection": 6000,
            "startup_force": 0,
            "hysteresis_percent": 80,
            "power_lock_switch": 0,
            "wheel_mode_brake_switch": 0,
            "angle_limit_switch": 1,
            "soft_start_switch": 0,
            "soft_start_time": 3000,
            "angle_upper_limit": 1800,
            "angle_lower_limit": -1800
        },
        6: {  # 舵机ID 6的参数
            'need_response':0,
            "baudrate": 8,
            "stall_protection": 0,
            "stall_power_limit": 2000,
            "low_voltage_protection": 4000,
            "high_voltage_protection": 12600,
            "temperature_protection": 1058,
            "power_protection": 4000,
            "current_protection": 6000,
            "startup_force": 0,
            "hysteresis_percent": 80,
            "power_lock_switch": 0,
            "wheel_mode_brake_switch": 0,
            "angle_limit_switch": 1,
            "soft_start_switch": 0,
            "soft_start_time": 3000,
            "angle_upper_limit": 1800,
            "angle_lower_limit": -1800
        }
    }
    
    # 定义0-6号舵机的内部参数字典
    internal_params_dict = {
        0: {  # 舵机ID 0的参数
            "kp": 400,
            "kd": 2300,
            "ki": 0,
            "bias": 0,
            "hold_kp": 400,
            "hold_kd": 2300,
            "hold_bias": 0,
            "forward_direction": 0,
            "dead_zone": 3
        },
        1: {  # 舵机ID 1的参数
            "kp": 800,
            "kd": 50,
            "ki": 0,
            "bias": 0,
            "hold_kp": 800,
            "hold_kd": 50,
            "hold_bias": 0,
            "forward_direction": 0,
            "dead_zone": 3
        },
        2: {  # 舵机ID 2的参数
            "kp": 800,
            "kd": 50,
            "ki": 0,
            "bias": 0,
            "hold_kp": 800,
            "hold_kd": 50,
            "hold_bias": 0,
            "forward_direction": 0,
            "dead_zone": 3
        },
        3: {  # 舵机ID 3的参数
            "kp": 200,
            "kd": 1100,
            "ki": 0,
            "bias": 0,
            "hold_kp": 200,
            "hold_kd": 1100,
            "hold_bias": 0,
            "forward_direction": 0,
            "dead_zone": 3
        },
        4: {  # 舵机ID 4的参数
            "kp": 200,
            "kd": 20,
            "ki": 0,
            "bias": 0,
            "hold_kp": 200,
            "hold_kd": 20,
            "hold_bias": 0,
            "forward_direction": 0,
            "dead_zone": 3
        },
        5: {  # 舵机ID 5的参数
            "kp": 200,
            "kd": 1100,
            "ki": 0,
            "bias": 0,
            "hold_kp": 200,
            "hold_kd": 1100,
            "hold_bias": 0,
            "forward_direction": 0,
            "dead_zone": 3
        },
        6: {  # 舵机ID 6的参数
            "kp": 200,
            "kd": 20,
            "ki": 0,
            "bias": 0,
            "hold_kp": 200,
            "hold_kd": 20,
            "hold_bias": 0,
            "forward_direction": 0,
            "dead_zone": 3
        }
    }
    
    # 使用字典设置公开参数
    print("设置所有舵机的公开参数...")
    for servo_id, params in public_params_dict.items():
        print(f"设置 {servo_id} 号舵机的公开参数")
        # 使用字典解包传递参数，并显式传入servo_id
        servo.write_public_parameters(servo_id=servo_id, **params)
        time.sleep(0.5)  # 添加延时以确保命令被处理
    
    time.sleep(0.5)  # 在公开参数和内部参数设置之间添加延时


    # 使用字典设置内部参数
    print("设置所有舵机的内部参数...")
    for servo_id, params in internal_params_dict.items():
        print(f"设置 {servo_id} 号舵机的内部参数")
        # 使用字典解包传递参数，并显式传入servo_id
        servo.write_internal_parameters(servo_id=servo_id, **params)
        time.sleep(0.5)  # 添加延时以确保命令被处理
        # 定义需要比较的公开参数和内部参数列表
    public_params_to_check = [
        'need_response', 'baudrate', 'stall_protection', 'stall_power_limit',
        'low_voltage_protection', 'high_voltage_protection', 'temperature_protection',
        'power_protection', 'current_protection', 'startup_force', 'hysteresis_percent',
        'power_lock_switch', 'wheel_mode_brake_switch', 'angle_limit_switch',
        'soft_start_switch', 'soft_start_time', 'angle_upper_limit', 'angle_lower_limit'
    ]
    
    internal_params_to_check = [
        'kp', 'kd', 'ki', 'bias', 'hold_kp', 'hold_kd', 'hold_bias',
        'forward_direction', 'dead_zone'
    ]

    # 验证所有舵机的参数
    all_valid = True
    for servo_id in range(7):  # 验证0-6号舵机
        if servo_id not in public_params_dict or servo_id not in internal_params_dict:
            print(f"跳过 {servo_id} 号舵机，未设置参数")
            continue
            
        print(f"\n验证 {servo_id} 号舵机参数...")
        
        # 验证公开参数
        print(f"读取 {servo_id} 号舵机的公开参数...")
        time.sleep(0.5)
        read_public_params = servo.read_public_parameters(servo_id=servo_id)
        
        if not read_public_params:
            all_valid = False
            print(f"舵机 {servo_id} 公开参数读取失败")
            continue
        
        # 只比较指定的公开参数
        public_mismatches = []
        for param in public_params_to_check:
            if param in public_params_dict[servo_id] and param in read_public_params:
                expected = public_params_dict[servo_id][param]
                actual = read_public_params[param]
                
                # 对于数值型参数，允许±1的误差
                if isinstance(expected, int) and isinstance(actual, int):
                    if abs(actual - expected) > 1:  # 允许±1的误差
                        public_mismatches.append(f"{param}: 期望值={expected}, 实际值={actual}")
                elif actual != expected:
                    public_mismatches.append(f"{param}: 期望值={expected}, 实际值={actual}")
        
        if public_mismatches:
            all_valid = False
            print(f"舵机 {servo_id} 公开参数不匹配:")
            for mismatch in public_mismatches:
                print(f"  - {mismatch}")
        else:
            print(f"舵机 {servo_id} 公开参数验证通过")
        
        # 验证内部参数
        print(f"读取 {servo_id} 号舵机的内部参数...")
        time.sleep(0.5)
        read_internal_params = servo.read_internal_parameters(servo_id=servo_id)
        
        if not read_internal_params:
            all_valid = False
            print(f"舵机 {servo_id} 内部参数读取失败")
            continue
        
        # 只比较指定的内部参数
        internal_mismatches = []
        for param in internal_params_to_check:
            if param in internal_params_dict[servo_id] and param in read_internal_params:
                expected = internal_params_dict[servo_id][param]
                actual = read_internal_params[param]
                
                # 对于数值型参数，允许±1的误差
                if isinstance(expected, int) and isinstance(actual, int):
                    if abs(actual - expected) > 1:  # 允许±1的误差
                        internal_mismatches.append(f"{param}: 期望值={expected}, 实际值={actual}")
                elif actual != expected:
                    internal_mismatches.append(f"{param}: 期望值={expected}, 实际值={actual}")
        
        if internal_mismatches:
            all_valid = False
            print(f"舵机 {servo_id} 内部参数不匹配:")
            for mismatch in internal_mismatches:
                print(f"  - {mismatch}")
        else:
            print(f"舵机 {servo_id} 内部参数验证通过")
    

    # 输出最终验证结果
    if all_valid:
        print("\n所有舵机参数验证通过，参数设置成功！")
    else:
        print("\n部分舵机参数验证失败，请检查错误信息并重试！")