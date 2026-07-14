import os
import site
import sys

user_site = site.getusersitepackages()
if user_site in sys.path:
    sys.path.remove(user_site)

import threading
from datetime import datetime

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_srvs.srv import SetBool, Trigger


class VideoRecorder(Node):
    def __init__(self):
        super().__init__("video_recorder")

        self.declare_parameter("image_topic", "/camera/camera/color/image_raw")
        self.declare_parameter("command_topic", "/recording/command")
        self.declare_parameter("output_dir", "~/recordings")
        self.declare_parameter("container", "mp4")
        self.declare_parameter("codec", "mp4v")
        self.declare_parameter("fps", 30.0)
        self.declare_parameter("filename_prefix", "camera")

        self.image_topic = self.get_parameter("image_topic").value
        self.command_topic = self.get_parameter("command_topic").value
        self.output_dir = os.path.expanduser(self.get_parameter("output_dir").value)
        self.container = self.get_parameter("container").value.lower().lstrip(".")
        self.codec = self.get_parameter("codec").value
        self.fps = float(self.get_parameter("fps").value)
        self.filename_prefix = self.get_parameter("filename_prefix").value

        self.bridge = CvBridge()
        self.lock = threading.Lock()
        self.writer = None
        self.output_path = None
        self.frame_size = None
        self.recording = False
        self.frames_written = 0

        self.status_pub = self.create_publisher(String, "/recording/status", 10)
        self.create_subscription(Image, self.image_topic, self.on_image, 10)
        self.create_subscription(String, self.command_topic, self.on_command, 10)
        self.create_service(SetBool, "/recording/set_recording", self.on_set_recording)
        self.create_service(Trigger, "/recording/start", self.on_start)
        self.create_service(Trigger, "/recording/stop", self.on_stop)

        self.get_logger().info(f"Image topic: {self.image_topic}")
        self.get_logger().info(f"Command topic: {self.command_topic}")
        self.get_logger().info("Use command 'start' or 'stop', or services /recording/start and /recording/stop")
        self.publish_status("idle")

    def publish_status(self, text):
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)

    def on_command(self, msg):
        command = msg.data.strip().lower()
        if command in ("start", "record", "begin", "1", "true"):
            ok, text = self.start_recording()
        elif command in ("stop", "end", "0", "false"):
            ok, text = self.stop_recording()
        else:
            ok = False
            text = f"Unknown command '{msg.data}'. Use start or stop."

        if ok:
            self.get_logger().info(text)
        else:
            self.get_logger().warn(text)

    def on_set_recording(self, request, response):
        if request.data:
            response.success, response.message = self.start_recording()
        else:
            response.success, response.message = self.stop_recording()
        return response

    def on_start(self, request, response):
        response.success, response.message = self.start_recording()
        return response

    def on_stop(self, request, response):
        response.success, response.message = self.stop_recording()
        return response

    def on_image(self, msg):
        with self.lock:
            if not self.recording:
                return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().error(f"Failed to convert image: {exc}")
            return

        height, width = frame.shape[:2]
        frame_size = (width, height)

        with self.lock:
            if not self.recording:
                return
            if self.writer is None:
                try:
                    self.open_writer(frame_size)
                except RuntimeError as exc:
                    self.get_logger().error(str(exc))
                    self.recording = False
                    self.publish_status(f"error: {exc}")
                    return
            if frame_size != self.frame_size:
                self.get_logger().warn(f"Frame size changed from {self.frame_size} to {frame_size}; frame dropped")
                return
            self.writer.write(frame)
            self.frames_written += 1

    def start_recording(self):
        with self.lock:
            if self.recording:
                return False, f"Already recording: {self.output_path}"

            os.makedirs(self.output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_path = os.path.join(self.output_dir, f"{self.filename_prefix}_{timestamp}.{self.container}")
            self.writer = None
            self.frame_size = None
            self.frames_written = 0
            self.recording = True
            self.publish_status(f"recording: {self.output_path}")

        return True, f"Recording started: {self.output_path}"

    def stop_recording(self):
        with self.lock:
            if not self.recording:
                return False, "Recorder is not running."

            self.recording = False
            path = self.output_path
            frames = self.frames_written
            if self.writer is not None:
                self.writer.release()

            self.writer = None
            self.output_path = None
            self.frame_size = None
            self.frames_written = 0
            self.publish_status(f"idle: saved {path}, frames={frames}")

        return True, f"Recording stopped: {path}, frames={frames}"

    def open_writer(self, frame_size):
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        writer = cv2.VideoWriter(self.output_path, fourcc, self.fps, frame_size)
        if not writer.isOpened():
            raise RuntimeError(f"Failed to open video writer: {self.output_path}, codec={self.codec}")
        self.writer = writer
        self.frame_size = frame_size
        self.get_logger().info(f"Video writer opened: {self.output_path}, size={frame_size}, fps={self.fps}, codec={self.codec}")

    def destroy_node(self):
        if self.recording:
            self.stop_recording()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = VideoRecorder()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
