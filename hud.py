"""
src/hud.py
==========
Draws a clean on-screen HUD on each video frame showing:
  - Current gesture label
  - Last triggered action
  - A colour-coded gesture indicator dot
  - FPS counter
"""

import cv2
import time


# Gesture → accent colour (BGR)
GESTURE_COLOURS = {
    "open_palm":   (0, 220, 100),   # green
    "fist":        (0, 80,  220),   # red
    "pinch":       (220, 180, 0),   # cyan-ish
    "swipe_right": (255, 160, 0),   # blue
    "swipe_left":  (255, 160, 0),   # blue
    "point_up":    (0,   220, 220),   # yellow
    "point_down":  (0,   220, 220),   # yellow
}
DEFAULT_COLOUR = (180, 180, 180)    # grey

ACTION_DISPLAY_SECONDS = 1.5        # how long to show the action label


class HUD:
    def __init__(self):
        self._last_action = None
        self._action_time = 0.0
        self._fps_times = []

    def draw(self, frame, gesture: str | None, action: str | None) -> "np.ndarray":
        """
        Overlay HUD elements onto frame and return the modified frame.
        """
        h, w = frame.shape[:2]
        now = time.time()

        # Track action display
        if action:
            self._last_action = action
            self._action_time = now

        # ── FPS ─────────────────────────────────────────────────────────────
        self._fps_times.append(now)
        self._fps_times = [t for t in self._fps_times if now - t < 1.0]
        fps = len(self._fps_times)

        # ── Colour for this gesture ─────────────────────────────────────────
        colour = GESTURE_COLOURS.get(gesture, DEFAULT_COLOUR)

        # ── Semi-transparent top bar ─────────────────────────────────────────
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 54), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # ── Gesture dot ─────────────────────────────────────────────────────
        dot_x, dot_y = 30, 27
        cv2.circle(frame, (dot_x, dot_y), 12, colour, -1)
        cv2.circle(frame, (dot_x, dot_y), 12, (255, 255, 255), 1)

        # ── Gesture label ────────────────────────────────────────────────────
        gesture_text = gesture.replace("_", " ").title() if gesture else "No Gesture"
        cv2.putText(
            frame, gesture_text,
            (54, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.75, colour, 2, cv2.LINE_AA,
        )

        # ── FPS (top right) ──────────────────────────────────────────────────
        fps_text = f"{fps} FPS"
        tw, _ = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0], 0
        cv2.putText(
            frame, fps_text,
            (w - tw[0] - 14, 32),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (160, 160, 160), 1, cv2.LINE_AA,
        )

        # ── Action label (centre bottom, fades out) ──────────────────────────
        if self._last_action and (now - self._action_time) < ACTION_DISPLAY_SECONDS:
            alpha = 1.0 - (now - self._action_time) / ACTION_DISPLAY_SECONDS
            action_colour = tuple(int(c * alpha) for c in (255, 255, 255))

            text = self._last_action
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.1, 2)
            tx = (w - tw) // 2
            ty = h - 36

            # Shadow
            cv2.putText(frame, text, (tx + 2, ty + 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 3, cv2.LINE_AA)
            # Text
            cv2.putText(frame, text, (tx, ty),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, action_colour, 2, cv2.LINE_AA)

        # ── Legend (bottom-left) ─────────────────────────────────────────────
        legend = [
            ("Open Palm", "Vol Up"),
            ("Fist", "Vol Down"),
            ("Pinch",     "Play/Pause"),
            ("→ Swipe", "Next"),
            ("☝ Point Up", "Bright Up"),
            ("☝ Point Dn", "Bright Dn"),
            ("← Swipe",   "Prev"),
        ]
        for i, (g, a) in enumerate(legend):
            y = h - (len(legend) - i) * 22 - 8
            cv2.putText(frame, f"{g}: {a}", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (140, 140, 140), 1, cv2.LINE_AA)

        return frame