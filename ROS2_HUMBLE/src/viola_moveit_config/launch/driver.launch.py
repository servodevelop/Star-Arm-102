from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():


    # Create and return the launch description
    return LaunchDescription(
        [
            Node(
                package="robo_driver",
                executable="driver",
                name="viola_driver",
                output="screen",
            ),
            Node(
                package="viola_controller",
                executable="controller",
                name="viola_controller",
                output="screen",
            )        
        ]
    )