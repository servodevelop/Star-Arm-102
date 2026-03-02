import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
# from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import Command, FindExecutable
# from launch.substitutions import LaunchConfiguration
from launch_ros.parameter_descriptions import ParameterValue  # 确保导入
import xacro

def generate_launch_description():

    robot_description_file = os.path.join(get_package_share_directory('cello_description'), 'urdf','cello_description.urdf')
    robot_description = Command(
        [FindExecutable(name='xacro'), ' ', robot_description_file])


    return LaunchDescription([
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                name='robot_state_publisher',
                respawn=True,
                parameters=[{'robot_description': ParameterValue(robot_description, value_type=str)}], 
                output='screen'
            ),
        ])
