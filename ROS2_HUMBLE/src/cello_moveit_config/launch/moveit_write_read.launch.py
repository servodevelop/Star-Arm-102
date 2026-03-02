from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
import os
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    

    robo_moveit_write_launch = os.path.join(get_package_share_directory('cello_moveit_config'),'launch')
    robo_moveit_write_node = IncludeLaunchDescription(PythonLaunchDescriptionSource([robo_moveit_write_launch,'/arm_moveit_write.launch.py']))


    robo_moveit_read_launch = os.path.join(get_package_share_directory('cello_moveit_config'),'launch')
    robo_moveit_read_node = IncludeLaunchDescription(PythonLaunchDescriptionSource([robo_moveit_read_launch,'/arm_moveit_read.launch.py']))


    return LaunchDescription([
        robo_moveit_write_node,
        robo_moveit_read_node
    ])

