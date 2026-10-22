"""
Write operating parameters to servo IDs 0-6 and verify each result.
"""

import serial
import struct
import time

BAUDRATE = 1000000
USB = "/dev/ttyUSB0"    # Replace with the actual serial port.
# USB = 'COM3'  # Example serial port on Windows.

class ServoProtocol:
    
    def __init__(self, port, baudrate=115200, timeout=0.1):
        self.serial = serial.Serial(port, baudrate, timeout=timeout)
        
    def __del__(self):
        if hasattr(self, 'serial') and self.serial.is_open:
            self.serial.close()
    
    def calculate_checksum(self, data):
        return sum(data) % 256
    
    def write_public_parameters(self, 
                               servo_id=0,                      # Servo ID.
                               need_response=0,                 # Whether to return a response after a command.
                               baudrate=5,                      # Baud rate.
                               stall_protection=0,              # Stall protection switch.
                               stall_power_limit=6000,          # Maximum stall power.
                               low_voltage_protection=4000,     # Low-voltage protection threshold.
                               high_voltage_protection=12600,   # High-voltage protection threshold.
                               temperature_protection=735,      # Temperature protection threshold.
                               power_protection=20000,          # Power protection threshold.
                               current_protection=4000,         # Current protection threshold.
                               startup_force=0,                 # Startup force.
                               hysteresis_percent=80,           # Hysteresis percentage.
                               power_lock_switch=0,             # Power-on hold switch.
                               wheel_mode_brake_switch=0,       # Wheel-mode brake switch.
                               angle_limit_switch=1,            # Angle limit switch.
                               soft_start_switch=0,             # Power-on soft-start switch.
                               soft_start_time=3000,            # Power-on soft-start time.
                               angle_upper_limit=1800,        # Upper angle limit.
                               angle_lower_limit=-1800):       # Lower angle limit.

        # Build the packet.
        header = bytes([0x12, 0x4C, 0x06, 0x21])

        # Build the parameter payload.
        params = bytearray([
            servo_id,
            0x01,
            need_response,
            servo_id, 0x00,  # This field changes with the servo ID.
            baudrate,
            stall_protection
        ])
        # Append maximum stall power (2 bytes, little-endian).
        params.extend(struct.pack('<H', stall_power_limit))
        # Append low-voltage threshold (2 bytes, little-endian).
        params.extend(struct.pack('<H', low_voltage_protection))
        # Append high-voltage threshold (2 bytes, little-endian).
        params.extend(struct.pack('<H', high_voltage_protection))
        # Append temperature threshold (2 bytes, little-endian).
        params.extend(struct.pack('<H', temperature_protection))
        # Append power threshold (2 bytes, little-endian).
        params.extend(struct.pack('<H', power_protection))
        # Append current threshold (2 bytes, little-endian).
        params.extend(struct.pack('<H', current_protection))
        # Append startup force.
        params.append(startup_force)
        # Append hysteresis percentage.
        params.append(hysteresis_percent)
        # Append power-on hold switch.
        params.append(power_lock_switch)
        # Append wheel-mode brake switch.
        params.append(wheel_mode_brake_switch)
        # Append angle limit switch.
        params.append(angle_limit_switch)
        # Append power-on soft-start switch.
        params.append(soft_start_switch)
        # Append soft-start time (2 bytes, little-endian).
        params.extend(struct.pack('<H', soft_start_time))
        # Append upper angle limit (2 bytes, little-endian).
        params.extend(struct.pack('<H', angle_upper_limit))
        # Append lower angle limit (2 bytes, little-endian).
        params.extend(struct.pack('<h', angle_lower_limit))
        # Append reserved bytes.
        params.extend([0x00, 0x00])
        # Calculate the checksum.
        checksum = self.calculate_checksum(header + params)
        # Assemble the complete packet.
        packet = header + params + bytes([checksum])
        # Send the packet.
        try:
            self.serial.write(packet)
            return True
        except Exception as e:
            print(f"发送数据失败: {e}")
            return False
    
    def write_internal_parameters(self, 
                                 servo_id=0,              # Servo ID.
                                 kp=800,                  # Proportional gain.
                                 kd=50,                   # Derivative gain.
                                 ki=0,                    # Integral gain.
                                 bias=0,                  # Bias.
                                 hold_kp=800,             # Hold proportional gain.
                                 hold_kd=50,              # Hold derivative gain.
                                 hold_bias=0,             # Hold bias.
                                 forward_direction=0,     # Forward direction.
                                 dead_zone=1):            # Dead zone.

        # Build the packet.
        header = bytes([0x13, 0x4D, 0xC4, 0x1A])
        # Build the parameter payload.
        params = bytearray([servo_id])
        # Append Kp (2 bytes, little-endian).
        params.extend(struct.pack('<H', kp))
        # Append Kd (2 bytes, little-endian).
        params.extend(struct.pack('<H', kd))
        # Append Ki (2 bytes, little-endian).
        params.extend(struct.pack('<H', ki))
        # Append Bias (2 bytes, little-endian).
        params.extend(struct.pack('<H', bias))
        # Append Hold Kp (2 bytes, little-endian).
        params.extend(struct.pack('<H', hold_kp))
        # Append Hold Kd (2 bytes, little-endian).
        params.extend(struct.pack('<H', hold_kd))
        # Append Hold Bias (2 bytes, little-endian).
        params.extend(struct.pack('<H', hold_bias))
        # Append fixed bytes.
        params.extend([0x10, 0x0E, 0x00, 0x00, 0xA4, 0x0B])
        # Append forward-direction setting.
        params.append(forward_direction)
        # Append fixed bytes.
        params.append(0x05)
        # Append dead-zone setting.
        params.append(dead_zone)
        # Append fixed bytes.
        params.extend([0x00, 0x01])
        # Calculate the checksum.
        checksum = self.calculate_checksum(header + params)
        # Assemble the complete packet.
        packet = header + params + bytes([checksum])
        # Send the packet.
        try:
            self.serial.write(packet)
            return True
        except Exception as e:
            print(f"发送数据失败: {e}")
            return False
        
    def read_public_parameters(self, servo_id=0x00):
        # Clear the serial input buffer.
        self.serial.reset_input_buffer()
        # Build the packet.
        cmd_data = [0x12, 0x4C, 0x05, 0x01, servo_id]
        checksum = self.calculate_checksum(cmd_data)
        packet = bytes(cmd_data + [checksum])
        # Send the packet.
        try:
            self.serial.write(packet)
            # Wait for a response packet.
            time.sleep(0.2)  # Allow more time for the response.
            # Read the response packet.
            if self.serial.in_waiting:
                response = self.serial.read(self.serial.in_waiting)
                # Check the response length.
                if len(response) < 38:  # The response should contain 39 bytes.
                    print(f"回包数据不完整: {response.hex(' ')}")
                    return False
                
                # Parse the response.
                result = {
                    'header': response[0:4].hex(' '),  # Response header.
                    'id': response[4],                 # ID
                    'unknown1': response[5],           # 01
                    'need_response': response[6],      # Whether to return a response after a command.
                    'id_related': response[7:9].hex(' '),  # This field changes with the servo ID.
                    'baudrate': response[9],           # Baud rate.
                    'stall_protection': response[10],  # Stall protection switch.
                    'stall_power_limit': struct.unpack('<H', response[11:13])[0],  # Maximum stall power.
                    'low_voltage_protection': struct.unpack('<H', response[13:15])[0],  # Low-voltage protection voltage.
                    'high_voltage_protection': struct.unpack('<H', response[15:17])[0],  # High-voltage protection voltage.
                    'temperature_protection': struct.unpack('<H', response[17:19])[0],  # Temperature protection threshold.
                    'power_protection': struct.unpack('<H', response[19:21])[0],  # Power protection threshold.
                    'current_protection': struct.unpack('<H', response[21:23])[0],  # Current protection threshold.
                    'startup_force': response[23],     # Startup force.
                    'hysteresis_percent': response[24],  # Hysteresis percentage.
                    'power_lock_switch': response[25],  # Power-on hold switch.
                    'wheel_mode_brake_switch': response[26],  # Wheel-mode brake switch.
                    'angle_limit_switch': response[27],  # Angle limit switch.
                    'soft_start_switch': response[28],  # Power-on soft-start switch.
                    'soft_start_time': struct.unpack('<H', response[29:31])[0],  # Power-on soft-start time.
                    'angle_upper_limit': struct.unpack('<H', response[31:33])[0],  # Upper angle limit.
                    'angle_lower_limit': struct.unpack('<h', response[33:35])[0],  # Lower angle limit.
                    'reserved': response[35:37].hex(' '),  # Reserved bytes.
                    'checksum': response[37]           # Checksum.
                }
                
                # Print the parsed values.
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
        # Clear the serial input buffer.
        self.serial.reset_input_buffer()
        # Build the packet.
        cmd_data = [0x13, 0x4D, 0xC5, 0x01, servo_id]
        checksum = self.calculate_checksum(cmd_data)
        packet = bytes(cmd_data + [checksum])
        # Send the packet.
        try:
            self.serial.write(packet)
            # Wait for a response packet.
            time.sleep(0.2)  # Allow more time for the response.
            # Read the response packet.
            if self.serial.in_waiting:
                response = self.serial.read(self.serial.in_waiting)
                # Check the response length.
                if len(response) < 31:  # The response should contain 31 bytes.
                    print(f"回包数据不完整: {response.hex(' ')}")
                    return False
                
                # Parse the response.
                result = {
                    'header': response[0:4].hex(' '),  # Response header.
                    'id': response[4],                 # ID
                    'kp': struct.unpack('<H', response[5:7])[0],  # Kp
                    'kd': struct.unpack('<H', response[7:9])[0],  # Kd
                    'ki': struct.unpack('<H', response[9:11])[0],  # Ki
                    'bias': struct.unpack('<H', response[11:13])[0],  # Bias
                    'hold_kp': struct.unpack('<H', response[13:15])[0],  # Hold Kp
                    'hold_kd': struct.unpack('<H', response[15:17])[0],  # Hold Kd
                    'hold_bias': struct.unpack('<H', response[17:19])[0],  # Hold Bias
                    'unknown1': response[19:25].hex(' '),  # Unknown bytes: 10 0E 00 00 A4 0B.
                    'forward_direction': response[25],  # Forward direction.
                    'unknown2': response[26],          # 05
                    'dead_zone': response[27],         # Dead zone.
                    'unknown3': response[28:30].hex(' '),  # 00 01
                    'checksum': response[30]           # Checksum.
                }
                
                # Print the parsed values.
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

# Usage example.
if __name__ == "__main__":
    # Create a servo protocol connection.
    # Replace this with the actual serial port.
    servo = ServoProtocol(USB,baudrate=BAUDRATE)  # Use the actual port, such as /dev/ttyUSB0 on Linux.
    
    # Define public parameters for servo IDs 0-6.
    public_params_dict = {
        0: {  # Servo ID 0 parameters.
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
        1: {  # Servo ID 1 parameters.
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
        2: {  # Servo ID 2 parameters.
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
        3: {  # Servo ID 3 parameters.
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
        4: {  # Servo ID 4 parameters.
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
        5: {  # Servo ID 5 parameters.
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
        6: {  # Servo ID 6 parameters.
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
    
    # Define internal parameters for servo IDs 0-6.
    internal_params_dict = {
        0: {  # Servo ID 0 parameters.
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
        1: {  # Servo ID 1 parameters.
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
        2: {  # Servo ID 2 parameters.
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
        3: {  # Servo ID 3 parameters.
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
        4: {  # Servo ID 4 parameters.
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
        5: {  # Servo ID 5 parameters.
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
        6: {  # Servo ID 6 parameters.
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
    
    # Write public parameters from the dictionaries.
    print("设置所有舵机的公开参数...")
    for servo_id, params in public_params_dict.items():
        print(f"设置 {servo_id} 号舵机的公开参数")
        # Unpack parameters and pass servo_id explicitly.
        servo.write_public_parameters(servo_id=servo_id, **params)
        time.sleep(0.5)  # Allow the command to be processed.
    
    time.sleep(0.5)  # Pause between public and internal parameter writes.


    # Write internal parameters from the dictionaries.
    print("设置所有舵机的内部参数...")
    for servo_id, params in internal_params_dict.items():
        print(f"设置 {servo_id} 号舵机的内部参数")
        # Unpack parameters and pass servo_id explicitly.
        servo.write_internal_parameters(servo_id=servo_id, **params)
        time.sleep(0.5)  # Allow the command to be processed.
        # List the public and internal fields to verify.
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

    # Verify every servo parameter set.
    all_valid = True
    for servo_id in range(7):  # Verify servo IDs 0-6.
        if servo_id not in public_params_dict or servo_id not in internal_params_dict:
            print(f"跳过 {servo_id} 号舵机，未设置参数")
            continue
            
        print(f"\n验证 {servo_id} 号舵机参数...")
        
        # Verify public parameters.
        print(f"读取 {servo_id} 号舵机的公开参数...")
        time.sleep(0.5)
        read_public_params = servo.read_public_parameters(servo_id=servo_id)
        
        if not read_public_params:
            all_valid = False
            print(f"舵机 {servo_id} 公开参数读取失败")
            continue
        
        # Compare only the selected public parameters.
        public_mismatches = []
        for param in public_params_to_check:
            if param in public_params_dict[servo_id] and param in read_public_params:
                expected = public_params_dict[servo_id][param]
                actual = read_public_params[param]
                
                # Allow a tolerance of +/-1 for numeric values.
                if isinstance(expected, int) and isinstance(actual, int):
                    if abs(actual - expected) > 1:  # Allow a tolerance of +/-1.
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
        
        # Verify internal parameters.
        print(f"读取 {servo_id} 号舵机的内部参数...")
        time.sleep(0.5)
        read_internal_params = servo.read_internal_parameters(servo_id=servo_id)
        
        if not read_internal_params:
            all_valid = False
            print(f"舵机 {servo_id} 内部参数读取失败")
            continue
        
        # Compare only the selected internal parameters.
        internal_mismatches = []
        for param in internal_params_to_check:
            if param in internal_params_dict[servo_id] and param in read_internal_params:
                expected = internal_params_dict[servo_id][param]
                actual = read_internal_params[param]
                
                # Allow a tolerance of +/-1 for numeric values.
                if isinstance(expected, int) and isinstance(actual, int):
                    if abs(actual - expected) > 1:  # Allow a tolerance of +/-1.
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
    

    # Print the final verification result.
    if all_valid:
        print("\n所有舵机参数验证通过，参数设置成功！")
    else:
        print("\n部分舵机参数验证失败，请检查错误信息并重试！")