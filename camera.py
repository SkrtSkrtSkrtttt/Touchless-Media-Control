"""
src/camera.py
=============
Wraps the Intel RealSense SDK to provide:
  - Aligned RGB + depth frames
  - 3D depth lookup for 2D pixel coordinates
"""

import numpy as np

try:
    import pyrealsense2 as rs
    REALSENSE_AVAILABLE = True
except ImportError:
    REALSENSE_AVAILABLE = False
    print("pyrealsense2 not found. Falling back to webcam mode.")


class RealSenseCamera:
    """
    Manages the RealSense pipeline.
    Falls back to a regular webcam if pyrealsense2 is not installed,
    """

    def __init__(self, width=640, height=480, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.pipeline = None
        self.align = None
        self._fallback_cap = None  # webcam fallback
        self._use_realsense = REALSENSE_AVAILABLE

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        if self._use_realsense:
            self._start_realsense()
        else:
            self._start_webcam()

    def _start_realsense(self):
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
        self.pipeline.start(config)

        # Align depth to color frame so pixel coordinates match
        self.align = rs.align(rs.stream.color)

    def _start_webcam(self):
        import cv2
        self._fallback_cap = cv2.VideoCapture(0)
        self._fallback_cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._fallback_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def stop(self):
        if self.pipeline:
            self.pipeline.stop()
        if self._fallback_cap:
            self._fallback_cap.release()

    # ------------------------------------------------------------------
    # Frame acquisition
    # ------------------------------------------------------------------

    def get_frames(self):
        """
        Returns (color_image: np.ndarray, depth_frame).
        depth_frame is a pyrealsense2 depth frame (has .get_distance()),
        or None when using webcam fallback.
        """
        if self._use_realsense:
            return self._get_realsense_frames()
        else:
            return self._get_webcam_frame()

    def _get_realsense_frames(self):
        frames = self.pipeline.wait_for_frames()
        aligned = self.align.process(frames)

        color_frame = aligned.get_color_frame()
        depth_frame = aligned.get_depth_frame()

        if not color_frame or not depth_frame:
            return None, None

        color_image = np.asanyarray(color_frame.get_data())
        return color_image, depth_frame

    def _get_webcam_frame(self):
        ret, frame = self._fallback_cap.read()
        if not ret:
            return None, None
        return frame, None

    # ------------------------------------------------------------------
    # Depth enrichment
    # ------------------------------------------------------------------

    def add_depth_to_landmarks(self, landmarks_2d, depth_frame):
        """
        Given a list of (x_norm, y_norm) landmark tuples and a RealSense
        depth frame, returns a list of (x_norm, y_norm, z_meters) tuples.

        x_norm / y_norm are MediaPipe-normalized [0, 1] coordinates.
        z_meters is the real-world depth in metres.
        """
        if depth_frame is None:
            return [(x, y, 0.0) for x, y in landmarks_2d]

        enriched = []
        for x_norm, y_norm in landmarks_2d:
            px = int(x_norm * self.width)
            py = int(y_norm * self.height)

            # Clamp to frame bounds
            px = max(0, min(px, self.width - 1))
            py = max(0, min(py, self.height - 1))

            z = depth_frame.get_distance(px, py)  # metres
            enriched.append((x_norm, y_norm, z))

        return enriched
