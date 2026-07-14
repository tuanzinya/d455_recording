from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("image_topic", default_value="/camera/camera/color/image_raw"),
            DeclareLaunchArgument("command_topic", default_value="/recording/command"),
            DeclareLaunchArgument("output_dir", default_value="~/recordings"),
            DeclareLaunchArgument("container", default_value="mp4"),
            DeclareLaunchArgument("codec", default_value="mp4v"),
            DeclareLaunchArgument("fps", default_value="30.0"),
            Node(
                package="recording_package",
                executable="video_recorder",
                name="video_recorder",
                output="screen",
                parameters=[
                    {
                        "image_topic": LaunchConfiguration("image_topic"),
                        "command_topic": LaunchConfiguration("command_topic"),
                        "output_dir": LaunchConfiguration("output_dir"),
                        "container": LaunchConfiguration("container"),
                        "codec": LaunchConfiguration("codec"),
                        "fps": LaunchConfiguration("fps"),
                    }
                ],
            ),
        ]
    )
