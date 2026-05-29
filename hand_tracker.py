"""
src/hand_tracker.py
===================
Wraps MediaPipe Hands to return:
  - 2D normalized landmark positions
  - An annotated BGR frame with the hand skeleton drawn
"""

import cv2
import mediapipe as mp


def _get_mediapipe_api():
    """
    MediaPipe 0.10+ moved to a new Tasks API.
    Returns (use_new_api: bool, hands_object, draw_utils, draw_styles).
    """
    if hasattr(mp, 'solutions'):
        return False, mp.solutions.hands, mp.solutions.drawing_utils, mp.solutions.drawing_styles
    else:
        return True, None, None, None


class HandTracker:
    """
    Detects a single hand and returns its 21 landmarks.
    Compatible with both old (mp.solutions) and new (mp.tasks) MediaPipe APIs.

    MediaPipe landmark indices (key ones):
        0  = wrist
        4  = thumb tip
        8  = index tip
        12 = middle tip
        16 = ring tip
        20 = pinky tip
        5  = index MCP (knuckle)
        9  = middle MCP
        13 = ring MCP
        17 = pinky MCP
    """

    def __init__(self, max_hands=1, detection_confidence=0.7, tracking_confidence=0.6):
        self._use_new_api, mp_hands, self._mp_draw, self._mp_styles = _get_mediapipe_api()

        if self._use_new_api:
            # MediaPipe 0.10+ Tasks API
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision
            import urllib.request, os

            # we need to download the hand landmarker model if not present
            model_path = "hand_landmarker.task"
            if not os.path.exists(model_path):
                print("📥 Downloading MediaPipe hand landmarker model...")
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
                urllib.request.urlretrieve(url, model_path)
                print("Model downloaded.")

            base_opts = mp_python.BaseOptions(model_asset_path=model_path)
            opts = mp_vision.HandLandmarkerOptions(
                base_options=base_opts,
                num_hands=max_hands,
                min_hand_detection_confidence=detection_confidence,
                min_tracking_confidence=tracking_confidence,
                running_mode=mp_vision.RunningMode.VIDEO,
            )
            self._detector = mp_vision.HandLandmarker.create_from_options(opts)
            self._frame_idx = 0
            self._mp_vision = mp_vision
            self._mp_drawing = mp.solutions.drawing_utils if hasattr(mp, 'solutions') else None

        else:
            # Legacy solutions API
            self._mp_hands = mp_hands
            self._hands = mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=max_hands,
                min_detection_confidence=detection_confidence,
                min_tracking_confidence=tracking_confidence,
            )

    def detect(self, bgr_frame):
        """
        Process a BGR frame.

        Returns:
            landmarks_2d : list of (x_norm, y_norm) for all 21 points,
                           or None if no hand found.
            annotated    : BGR frame with skeleton overlay drawn.
        """
        if self._use_new_api:
            return self._detect_new(bgr_frame)
        else:
            return self._detect_legacy(bgr_frame)

    def _detect_legacy(self, bgr_frame):
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self._hands.process(rgb)
        rgb.flags.writeable = True

        annotated = bgr_frame.copy()
        landmarks_2d = None

        if results.multi_hand_landmarks:
            hand_lms = results.multi_hand_landmarks[0]
            self._mp_draw.draw_landmarks(
                annotated,
                hand_lms,
                self._mp_hands.HAND_CONNECTIONS,
                self._mp_styles.get_default_hand_landmarks_style(),
                self._mp_styles.get_default_hand_connections_style(),
            )
            landmarks_2d = [(lm.x, lm.y) for lm in hand_lms.landmark]

        return landmarks_2d, annotated

    def _detect_new(self, bgr_frame):
        import mediapipe as mp
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        self._frame_idx += 1
        result = self._detector.detect_for_video(mp_image, self._frame_idx * 33)

        annotated = bgr_frame.copy()
        landmarks_2d = None

        if result.hand_landmarks:
            hand_lms = result.hand_landmarks[0]
            landmarks_2d = [(lm.x, lm.y) for lm in hand_lms]

            # Draw landmarks manually
            h, w = bgr_frame.shape[:2]
            for lm in hand_lms:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(annotated, (cx, cy), 5, (0, 255, 0), -1)

            # Draw connections
            CONNECTIONS = mp.tasks.vision.HandLandmarksConnector.HAND_CONNECTIONS \
                if hasattr(mp.tasks.vision, 'HandLandmarksConnector') \
                else _HAND_CONNECTIONS
            for a, b in CONNECTIONS:
                ax, ay = int(hand_lms[a].x * w), int(hand_lms[a].y * h)
                bx, by = int(hand_lms[b].x * w), int(hand_lms[b].y * h)
                cv2.line(annotated, (ax, ay), (bx, by), (0, 200, 80), 2)

        return landmarks_2d, annotated


# Fallback hand connection list (standard MediaPipe topology)
_HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17),
]