from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
import os
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    

    robo_state_publisher_launch = os.path.join(get_package_share_directory('cello_description'),'launch')
    robo_state_publisher_node = IncludeLaunchDescription(PythonLaunchDescriptionSource([robo_state_publisher_launch,'/robo_state_publisher.launch.py']))


    robo_moveit_rviz_launch = os.path.join(get_package_share_directory('cello_moveit_config'),'launch')
    robo_moveit_rviz_node = IncludeLaunchDescription(PythonLaunchDescriptionSource([robo_moveit_rviz_launch,'/move_group_rviz.launch.py']))


    return LaunchDescription([
        robo_state_publisher_node,
        robo_moveit_rviz_node
    ])

