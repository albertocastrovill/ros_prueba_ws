#!/usr/bin/env python3
import os
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class SnapshotSubNode(Node):
    def __init__(self):
        super().__init__('snapshot_sub_node')
        self.declare_parameter('image_topic', 'camera/image_raw')
        self.declare_parameter('save_dir', os.path.expanduser('~/Pictures/ros_snapshots'))
        self.declare_parameter('window_name', 'Snapshot Viewer')

        self.image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        self.save_dir = self.get_parameter('save_dir').get_parameter_value().string_value
        self.window_name = self.get_parameter('window_name').get_parameter_value().string_value

        os.makedirs(self.save_dir, exist_ok=True)

        self.bridge = CvBridge()
        self.last_frame = None

        self.sub = self.create_subscription(
            Image,'camera/image_raw', self._on_image, QoSProfile(depth=10)
        )

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        # Timer para refrescar GUI y leer teclado sin bloquear
        self.timer = self.create_timer(0.02, self._gui_loop)  # ~50 Hz

        self.get_logger().info(
            f'Suscrito a "{self.image_topic}". Presiona SPACE para guardar. Guardando en: {self.save_dir}'
        )

    def _on_image(self, msg: Image):
        try:
            self.last_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'Error al convertir imagen: {e}')

    def _gui_loop(self):
        if self.last_frame is not None:
            cv2.imshow(self.window_name, self.last_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # SPACE
            self._save_snapshot()
        elif key == 27:  # ESC
            self.get_logger().info('Cerrando ventana (ESC).')
            cv2.destroyWindow(self.window_name)

    def _save_snapshot(self):
        if self.last_frame is None:
            self.get_logger().warn('No hay frame para guardar.')
            return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        path = os.path.join(self.save_dir, f'snapshot_{ts}.png')
        try:
            cv2.imwrite(path, self.last_frame)
            self.get_logger().info(f'Foto guardada: {path}')
        except Exception as e:
            self.get_logger().error(f'Error guardando: {e}')

    def destroy_node(self):
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        super().destroy_node()

def main():
    rclpy.init()
    node = None
    try:
        node = SnapshotSubNode()
        rclpy.spin(node)
    finally:
        if node:
            node.destroy_node()
        rclpy.shutdown()
