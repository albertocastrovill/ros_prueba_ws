#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class CameraPubNode(Node):
    def __init__(self):
        super().__init__('camera_pub_node')
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('fps', 30)

        self.camera_index = self.get_parameter('camera_index').get_parameter_value().integer_value
        self.fps = self.get_parameter('fps').get_parameter_value().integer_value

        self.bridge = CvBridge()
        self.pub = self.create_publisher(Image, 'camera/image_raw', QoSProfile(depth=10))

        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            self.get_logger().error(f'No se pudo abrir la cámara índice {self.camera_index}')
            raise RuntimeError('Cámara no disponible')

        period = 1.0 / float(max(1, self.fps))
        self.timer = self.create_timer(period, self._tick)
        self.get_logger().info(f'Publicando /camera/image_raw @ {self.fps} FPS (cam {self.camera_index})')

    def _tick(self):
        ok, frame = self.cap.read()
        if not ok:
            self.get_logger().warning('No se pudo leer frame.')
            return
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        self.pub.publish(msg)

    def destroy_node(self):
        try:
            if hasattr(self, 'cap') and self.cap.isOpened():
                self.cap.release()
        finally:
            super().destroy_node()

def main():
    rclpy.init()
    node = None
    try:
        node = CameraPubNode()
        rclpy.spin(node)
    finally:
        if node:
            node.destroy_node()
        rclpy.shutdown()
