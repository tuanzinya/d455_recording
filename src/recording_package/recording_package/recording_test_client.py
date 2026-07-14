import sys

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class RecordingTestClient(Node):
    def __init__(self):
        super().__init__("recording_test_client")

    def call_trigger(self, service_name):
        client = self.create_client(Trigger, service_name)
        if not client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error(f"Service not available: {service_name}")
            return 1

        future = client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future)
        result = future.result()
        if result is None:
            self.get_logger().error(f"Service call failed: {service_name}")
            return 1

        if result.success:
            self.get_logger().info(result.message)
            return 0

        self.get_logger().warn(result.message)
        return 2


def main(args=None):
    rclpy.init(args=args)
    node = RecordingTestClient()
    command = sys.argv[1].lower() if len(sys.argv) > 1 else ""

    if command == "start":
        code = node.call_trigger("/recording/start")
    elif command == "stop":
        code = node.call_trigger("/recording/stop")
    else:
        node.get_logger().error("Usage: ros2 run recording_package recording_test_client start|stop")
        code = 1

    node.destroy_node()
    rclpy.shutdown()
    sys.exit(code)


if __name__ == "__main__":
    main()
