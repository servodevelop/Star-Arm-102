from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Set MoveIt configuration for viola robot
    moveit_config = MoveItConfigsBuilder("viola").to_moveit_configs()

    # Get the path to the config directory
    viola_config_path = os.path.join(
        get_package_share_directory('viola_moveit_config'),
        'config',
    )

    # Declare the config path as a launch argument
    declare_param_file_cmd = DeclareLaunchArgument(
        'config_path',
        default_value=viola_config_path,
        description='Full path to the ROS2 parameters file'
    )

    # Create and return the launch description
    return LaunchDescription(
        [
            declare_param_file_cmd,
            Node(
                package="arm_moveit_read",
                executable="arm_moveit_read",
                name="arm_moveit_read",
                output="screen",
                parameters=[
                    moveit_config.robot_description,  # Load URDF
                    moveit_config.robot_description_semantic,  # Load SRDF
                    moveit_config.robot_description_kinematics,  # Load kinematics.yaml
                    LaunchConfiguration('config_path'),
                ],
                # Remap topics if needed
                # remappings=[
                #     ("/joint_states", "/custom_joint_states"),
                #     ("/gripper_command_topic", "/custom_gripper_command_topic"),
                # ],
            )
        ]
    )