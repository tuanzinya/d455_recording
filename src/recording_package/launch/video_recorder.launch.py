import re
import subprocess

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

CAMERA_CONFIGS = [
    {
        "index": 0,
        "label": "前置",
        "namespace": "camera0",
        "name": "camera0",
        "prefix": "front_camera",
        "serial_arg": "camera0_serial",
    },
    {
        "index": 1,
        "label": "后置",
        "namespace": "camera1",
        "name": "camera1",
        "prefix": "rear_camera",
        "serial_arg": "camera1_serial",
    },
]


def get_connected_realsense_serials():
    try:
        result = subprocess.run(
            ["rs-enumerate-devices"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5.0,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    if result.returncode != 0:
        return []

    serials = []
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*Serial Number\s*:\s*(\S+)\s*$", line)
        if match:
            serials.append(match.group(1))

    return serials


def launch_after_camera_check(context, *args, **kwargs):
    connected_serials = get_connected_realsense_serials()
    assigned = []
    used_serials = set()
    actions = []
    requested_by_arg = {
        config["serial_arg"]: LaunchConfiguration(config["serial_arg"]).perform(context).strip()
        for config in CAMERA_CONFIGS
    }
    reserved_serials = {serial for serial in requested_by_arg.values() if serial}

    for config in CAMERA_CONFIGS:
        requested_serial = requested_by_arg[config["serial_arg"]]
        serial = ""

        if requested_serial:
            if requested_serial in connected_serials and requested_serial not in used_serials:
                serial = requested_serial
        else:
            for candidate in connected_serials:
                if candidate not in used_serials and candidate not in reserved_serials:
                    serial = candidate
                    break

        if serial:
            used_serials.add(serial)
            assigned.append((config, serial))
            actions.append(LogInfo(msg=f"相机{config['index']}（{config['label']}）：已连接，序列号 {serial}"))
        else:
            actions.append(LogInfo(msg=f"相机{config['index']}（{config['label']}）：未连接"))

    if not assigned:
        actions.append(LogInfo(msg="没有相机连接，不启动相机节点和录像节点"))
        return actions

    actions.append(LogInfo(msg="至少一个相机已连接，开始启动录像"))

    for config, serial in assigned:
        camera_node = Node(
            package="realsense2_camera",
            executable="realsense2_camera_node",
            namespace=config["namespace"],
            name=config["name"],
            output="screen",
            parameters=[
                {
                    "serial_no": f"_{serial}",
                    "enable_color": True,
                    "enable_depth": False,
                    "enable_infra": False,
                    "enable_infra1": False,
                    "enable_infra2": False,
                    "enable_gyro": False,
                    "enable_accel": False,
                    "enable_motion": False,
                }
            ],
        )

        recorder_node = Node(
            package="recording_package",
            executable="video_recorder",
            namespace="recording",
            name=f"camera{config['index']}_recorder",
            output="screen",
            parameters=[
                {
                    "image_topic": f"/{config['namespace']}/{config['name']}/color/image_raw",
                    "command_topic": LaunchConfiguration("command_topic"),
                    "status_topic": f"/recording/camera{config['index']}/status",
                    "start_service": f"/recording/camera{config['index']}/start",
                    "stop_service": f"/recording/camera{config['index']}/stop",
                    "set_recording_service": f"/recording/camera{config['index']}/set_recording",
                    "output_dir": LaunchConfiguration("output_dir"),
                    "container": LaunchConfiguration("container"),
                    "codec": LaunchConfiguration("codec"),
                    "fps": LaunchConfiguration("fps"),
                    "filename_prefix": config["prefix"],
                    "auto_start": LaunchConfiguration("auto_start"),
                }
            ],
        )

        actions.extend([camera_node, recorder_node])

    return actions


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("camera0_serial", default_value=""),
            DeclareLaunchArgument("camera1_serial", default_value=""),
            DeclareLaunchArgument("command_topic", default_value="/recording/command"),
            DeclareLaunchArgument("output_dir", default_value="~/recordings"),
            DeclareLaunchArgument("container", default_value="mp4"),
            DeclareLaunchArgument("codec", default_value="mp4v"),
            DeclareLaunchArgument("fps", default_value="30.0"),
            DeclareLaunchArgument("auto_start", default_value="true"),
            OpaqueFunction(function=launch_after_camera_check),
        ]
    )
