# recording_package 使用说明

`recording_package` 是一个 ROS 2 Humble 功能包，用于 RealSense 双相机录像。

当前默认设计：

- 相机 0：前置相机，命名空间 `/camera0`，录像文件前缀 `front_camera`
- 相机 1：后置相机，命名空间 `/camera1`，录像文件前缀 `rear_camera`
- 默认启动后自动录像：`auto_start:=true`
- 至少检测到 1 个相机连接，就启动对应相机节点和录像节点
- 两个相机都连接时，两路同时录像并分别保存文件

## 1. 依赖

系统环境：

- Ubuntu 22.04
- ROS 2 Humble
- RealSense ROS 驱动：`realsense2_camera`
- librealsense 工具：`rs-enumerate-devices`
- OpenCV Python
- `cv_bridge`

安装常用依赖：

```bash
sudo apt update
sudo apt install -y \
  ros-humble-realsense2-camera \
  ros-humble-cv-bridge \
  ros-humble-image-transport \
  ros-humble-image-transport-plugins \
  python3-opencv
```

如果 `rs-enumerate-devices` 不存在，安装 librealsense 工具：

```bash
sudo apt install -y librealsense2-utils
```

检查 RealSense 是否能被系统识别：

```bash
rs-enumerate-devices
```

检查 ROS 是否能找到 RealSense 驱动：

```bash
source /opt/ros/humble/setup.bash
ros2 pkg prefix realsense2_camera
```

## 2. 工作空间位置

当前功能包位置：

```bash
~/d445_ws/src/recording_package
```

工作空间位置：

```bash
~/d445_ws
```

## 3. 编译方式

进入工作空间：

```bash
cd ~/d445_ws
```

加载 ROS 2 环境：

```bash
source /opt/ros/humble/setup.bash
```

安装依赖：

```bash
rosdep install --from-paths src -y --ignore-src
```

编译功能包：

```bash
colcon build --packages-select recording_package
```

加载当前工作空间：

```bash
source ~/d445_ws/install/setup.bash
```

检查功能包是否可用：

```bash
ros2 pkg prefix recording_package
ros2 pkg executables recording_package
```

应能看到：

```bash
recording_package video_recorder
recording_package recording_test_client
```

## 4. 启动录像功能

启动双相机录像：

```bash
source /opt/ros/humble/setup.bash
source ~/d445_ws/install/setup.bash
ros2 launch recording_package video_recorder.launch.py
```

启动时会先检测相机连接情况，并在终端输出：

```text
相机0（前置）：已连接，序列号 xxxxxxxxxxxx
相机1（后置）：已连接，序列号 xxxxxxxxxxxx
至少一个相机已连接，开始启动录像
```

如果某个相机未连接，会输出：

```text
相机0（前置）：未连接
```

或：

```text
相机1（后置）：未连接
```

如果两个相机都未连接，会输出：

```text
没有相机连接，不启动相机节点和录像节点
```

## 5. 默认录像逻辑

默认参数：

```bash
auto_start:=true
```

因此启动 launch 后：

- 相机 0 连接：自动启动相机 0 并录制前置视频
- 相机 1 连接：自动启动相机 1 并录制后置视频
- 两个相机都连接：两路同时自动录像
- 只有一个相机连接：只录制已连接的那一路

录像默认保存目录：

```bash
~/recordings
```

默认文件名格式：

```bash
front_camera_YYYYMMDD_HHMMSS.mp4
rear_camera_YYYYMMDD_HHMMSS.mp4
```

查看录像文件：

```bash
ls -lh ~/recordings
```

## 6. 手动开始和停止录像

所有已启动的录像节点都订阅同一个控制话题：

```bash
/recording/command
```

停止所有正在录像的相机：

```bash
ros2 topic pub --once /recording/command std_msgs/msg/String "{data: stop}"
```

重新开始所有已连接相机录像：

```bash
ros2 topic pub --once /recording/command std_msgs/msg/String "{data: start}"
```

支持的命令包括：

- `start`
- `stop`
- `record`
- `begin`
- `end`
- `true`
- `false`

## 7. 禁用启动自动录像

如果希望启动相机节点后不立刻录像：

```bash
ros2 launch recording_package video_recorder.launch.py auto_start:=false
```

之后手动开始录像：

```bash
ros2 topic pub --once /recording/command std_msgs/msg/String "{data: start}"
```

## 8. 固定前置和后置相机序列号

默认情况下，相机按 `rs-enumerate-devices` 检测顺序分配：

- 第 1 个检测到的相机 -> 相机 0 / 前置
- 第 2 个检测到的相机 -> 相机 1 / 后置

建议在机器人上固定序列号，避免 USB 插口变化导致前后相机对应关系变化。

查看相机序列号：

```bash
rs-enumerate-devices | grep "Serial Number"
```

启动时指定：

```bash
ros2 launch recording_package video_recorder.launch.py \
  camera0_serial:=前置相机序列号 \
  camera1_serial:=后置相机序列号
```

示例：

```bash
ros2 launch recording_package video_recorder.launch.py \
  camera0_serial:=341222301319 \
  camera1_serial:=123456789012
```

## 9. 单独控制某一路录像

相机 0 / 前置：

```bash
ros2 service call /recording/camera0/start std_srvs/srv/Trigger "{}"
ros2 service call /recording/camera0/stop std_srvs/srv/Trigger "{}"
```

相机 1 / 后置：

```bash
ros2 service call /recording/camera1/start std_srvs/srv/Trigger "{}"
ros2 service call /recording/camera1/stop std_srvs/srv/Trigger "{}"
```

也可以使用 `SetBool` 接口：

```bash
ros2 service call /recording/camera0/set_recording std_srvs/srv/SetBool "{data: true}"
ros2 service call /recording/camera0/set_recording std_srvs/srv/SetBool "{data: false}"
```

## 10. 状态话题

相机 0 状态：

```bash
ros2 topic echo /recording/camera0/status
```

相机 1 状态：

```bash
ros2 topic echo /recording/camera1/status
```

状态内容示例：

```text
recording: /home/robot007/recordings/front_camera_20260714_144755.mp4
idle: saved /home/robot007/recordings/front_camera_20260714_144755.mp4, frames=279
```

## 11. 修改输出格式

默认使用 MP4：

```bash
container:=mp4 codec:=mp4v
```

如果 MP4 编码不稳定，可以改用 AVI：

```bash
ros2 launch recording_package video_recorder.launch.py container:=avi codec:=MJPG
```

修改保存目录：

```bash
ros2 launch recording_package video_recorder.launch.py output_dir:=/home/robot007/videos
```

修改录像帧率参数：

```bash
ros2 launch recording_package video_recorder.launch.py fps:=30.0
```

注意：`fps` 是视频文件写入帧率，应与相机实际发布帧率一致或接近。

## 12. 常用完整命令

自动检测相机并立即开始录像：

```bash
source /opt/ros/humble/setup.bash
source ~/d445_ws/install/setup.bash
ros2 launch recording_package video_recorder.launch.py
```

固定双相机序列号并自动录像：

```bash
source /opt/ros/humble/setup.bash
source ~/d445_ws/install/setup.bash
ros2 launch recording_package video_recorder.launch.py \
  camera0_serial:=前置相机序列号 \
  camera1_serial:=后置相机序列号
```

启动但不自动录像：

```bash
ros2 launch recording_package video_recorder.launch.py auto_start:=false
```

停止录像：

```bash
ros2 topic pub --once /recording/command std_msgs/msg/String "{data: stop}"
```

重新开始录像：

```bash
ros2 topic pub --once /recording/command std_msgs/msg/String "{data: start}"
```

## 13. 故障排查

查看是否检测到相机：

```bash
rs-enumerate-devices
```

查看是否有其他进程占用相机：

```bash
ps aux | grep realsense
fuser /dev/video*
```

查看相机话题：

```bash
ros2 topic list | grep camera
```

确认录像节点是否启动：

```bash
ros2 node list | grep recorder
```

如果终端出现 `Device or resource busy`，通常表示相机被其他程序占用，先关闭：

- `realsense-viewer`
- 旧的 `ros2 launch`
- 其他读取 `/dev/video*` 的程序

必要时重新插拔相机。

## 14. 参考链接
https://fishros.org.cn/forum/topic/3755/%E5%A6%82%E4%BD%95%E5%9C%A8ros2-humble%E7%89%88%E6%9C%AC%E4%B8%8A%E5%AE%89%E8%A3%85d455%E7%9B%B8%E6%9C%BA%E5%B9%B6%E8%8E%B7%E5%8F%96%E5%9B%BE%E5%83%8F%E5%92%8C%E6%B7%B1%E5%BA%A6%E4%BF%A1%E6%81%AF/2
