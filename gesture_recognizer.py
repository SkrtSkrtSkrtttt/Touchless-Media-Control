"""
src/gesture_recognizer.py
==========================
Detects gestures from hand landmarks.

Supported gestures
------------------
  "open_palm"        - all 4 fingers extended        -> volume up
  "fist"             - all 4 fingers curled           -> volume down
  "pinch"            - thumb tip close to index tip   -> play/pause
  "swipe_right"      - wrist moved right quickly      -> next track
  "swipe_left"       - wrist moved left quickly       -> prev track
  "point_up"         - only index finger up, moving up   -> brightness up
  "point_down"       - only index finger up, moving down -> brightness down
  None               - no confident gesture detected
"""

from collections import deque


# Tunable constants
PINCH_THRESHOLD       = 0.06   # normalised distance for pinch
SWIPE_THRESHOLD       = 0.12   # normalised horizontal wrist travel
SWIPE_WINDOW          = 8      # frames to check for swipe motion
BRIGHTNESS_WINDOW     = 10     # frames to check for point drag motion
BRIGHTNESS_THRESHOLD  = 0.04   # normalised vertical index-tip travel


class GestureRecognizer:
    def __init__(self):
        self._wrist_history = deque(maxlen=SWIPE_WINDOW)
        self._index_tip_history = deque(maxlen=BRIGHTNESS_WINDOW)

    def recognize(self, landmarks_2d, landmarks_3d=None):
        if landmarks_2d is None:
            self._wrist_history.clear()
            self._index_tip_history.clear()
            return None

        lm = landmarks_2d

        self._wrist_history.append(lm[0][0])
        self._index_tip_history.append(lm[8][1])

        # 1. Pinch
        if self._is_pinch(lm):
            return "pinch"

        # 2. Swipe
        swipe = self._detect_swipe()
        if swipe:
            return swipe

        fingers_up = self._count_extended_fingers(lm)
        extended = self._which_fingers_extended(lm)

        # 3. Point (only index up) -> brightness
        if fingers_up == 1 and extended[0]:
            brightness = self._detect_brightness()
            if brightness:
                return brightness

        # 4. Open palm / fist -> volume
        if fingers_up >= 4:
            return "open_palm"

        if fingers_up == 0:
            return "fist"

        return None

    def _is_pinch(self, lm):
        return _dist2d(lm[4], lm[8]) < PINCH_THRESHOLD

    def _which_fingers_extended(self, lm):
        finger_pairs = [(8, 5), (12, 9), (16, 13), (20, 17)]
        return [lm[tip][1] < lm[mcp][1] for tip, mcp in finger_pairs]

    def _count_extended_fingers(self, lm):
        return sum(self._which_fingers_extended(lm))

    def _detect_swipe(self):
        if len(self._wrist_history) < SWIPE_WINDOW:
            return None
        delta = self._wrist_history[-1] - self._wrist_history[0]
        if delta > SWIPE_THRESHOLD:
            self._wrist_history.clear()
            return "swipe_right"
        if delta < -SWIPE_THRESHOLD:
            self._wrist_history.clear()
            return "swipe_left"
        return None

    def _detect_brightness(self):
        """
        Index tip moving UP (smaller y) = brightness up.
        Index tip moving DOWN (larger y) = brightness down.
        """
        if len(self._index_tip_history) < BRIGHTNESS_WINDOW:
            return None
        delta = self._index_tip_history[-1] - self._index_tip_history[0]
        if delta < -BRIGHTNESS_THRESHOLD:
            self._index_tip_history.clear()
            return "point_up"
        if delta > BRIGHTNESS_THRESHOLD:
            self._index_tip_history.clear()
            return "point_down"
        return None


def _dist2d(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5