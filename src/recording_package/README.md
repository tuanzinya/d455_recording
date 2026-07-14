# recording_package

ROS 2 camera recording package for RealSense or any sensor_msgs/msg/Image camera topic.

## Interfaces

- Image input: /camera/camera/color/image_raw
- Command topic: /recording/command, type std_msgs/msg/String
  - publish start to begin recording
  - publish stop to end recording
- Status topic: /recording/status, type std_msgs/msg/String
- Services:
  - /recording/start, type std_srvs/srv/Trigger
  - /recording/stop, type std_srvs/srv/Trigger
  - /recording/set_recording, type std_srvs/srv/SetBool

## Build

```bash
cd ~/ros_ws
rosdep install --from-paths src -y --ignore-src
colcon build --packages-select recording_package
source install/setup.bash
```

## Run

Terminal 1:

```bash
source /opt/ros/humble/setup.bash
ros2 launch realsense2_camera rs_launch.py
```

Terminal 2:

```bash
source /opt/ros/humble/setup.bash
source ~/ros_ws/install/setup.bash
ros2 launch recording_package video_recorder.launch.py
```

## Start and Stop

```bash
ros2 topic pub --once /recording/command std_msgs/msg/String "{data: start}"
ros2 topic pub --once /recording/command std_msgs/msg/String "{data: stop}"
```

or:

```bash
ros2 run recording_package recording_test_client start
ros2 run recording_package recording_test_client stop
```

Videos are saved under ~/recordings by default.

Use AVI if MP4 does not work on the robot:

```bash
ros2 launch recording_package video_recorder.launch.py container:=avi codec:=MJPG
```
