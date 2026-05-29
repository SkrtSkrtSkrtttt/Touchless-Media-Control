"""
src/system_controller.py
========================
Maps recognized gestures to system actions.

Gesture -> Action
-----------------
  open_palm   -> Volume up
  fist        -> Volume down
  pinch       -> Play / Pause
  swipe_right -> Next track
  swipe_left  -> Previous track
  point_up    -> Brightness up
  point_down  -> Brightness down
"""

import time
import platform
import subprocess
from pynput.keyboard import Key, Controller

# Tunable constants
HOLD_INTERVAL = 0.15   # seconds between repeated ticks while holding
DEBOUNCE_TIME = 0.5    # seconds to ignore repeated one-shot gestures

_OS = platform.system()  # "Darwin", "Linux", "Windows"


class SystemController:
    def __init__(self):
        self._kb = Controller()
        self._last_gesture = None
        self._last_fire_time = 0.0
        self._hold_timer = 0.0

    def handle(self, gesture):
        now = time.time()

        # Held gestures (volume)
        if gesture in ("open_palm", "fist"):
            if now - self._hold_timer >= HOLD_INTERVAL:
                self._hold_timer = now
                if gesture == "open_palm":
                    self._volume_up()
                    return "Volume Up"
                else:
                    self._volume_down()
                    return "Volume Down"
            return None

        self._hold_timer = 0.0

        # One-shot gestures (debounced)
        one_shots = ("pinch", "swipe_right", "swipe_left", "point_up", "point_down")
        if gesture in one_shots:
            if gesture == self._last_gesture and now - self._last_fire_time < DEBOUNCE_TIME:
                return None
            self._last_gesture = gesture
            self._last_fire_time = now

            if gesture == "pinch":
                self._play_pause()
                return "⏯  Play / Pause"
            elif gesture == "swipe_right":
                self._next_track()
                return "⏭  Next Track"
            elif gesture == "swipe_left":
                self._prev_track()
                return "⏮  Prev Track"
            elif gesture == "point_up":
                self._brightness_up()
                return "  Brightness Up"
            elif gesture == "point_down":
                self._brightness_down()
                return "  Brightness Down"

        return None

    # ── Volume ────────────────────────────────────────────────────────────────

    def _volume_up(self):
        if _OS == "Darwin":
            self._kb.press(Key.media_volume_up); self._kb.release(Key.media_volume_up)
        elif _OS == "Linux":
            subprocess.run(["amixer", "-q", "sset", "Master", "5%+"], check=False)
        else:
            self._kb.press(Key.media_volume_up); self._kb.release(Key.media_volume_up)

    def _volume_down(self):
        if _OS == "Darwin":
            self._kb.press(Key.media_volume_down); self._kb.release(Key.media_volume_down)
        elif _OS == "Linux":
            subprocess.run(["amixer", "-q", "sset", "Master", "5%-"], check=False)
        else:
            self._kb.press(Key.media_volume_down); self._kb.release(Key.media_volume_down)

    # ── Brightness ────────────────────────────────────────────────────────────

    def _brightness_up(self):
        if _OS == "Darwin":
            self._kb.press(Key.brightness_up); self._kb.release(Key.brightness_up)
        elif _OS == "Linux":
            self._linux_brightness(+10)
        else:
            # Windows: use PowerShell WMI
            subprocess.run([
                "powershell", "-Command",
                "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                ".WmiSetBrightness(1, [Math]::Min(100, "
                "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + 10))"
            ], check=False)

    def _brightness_down(self):
        if _OS == "Darwin":
            self._kb.press(Key.brightness_down); self._kb.release(Key.brightness_down)
        elif _OS == "Linux":
            self._linux_brightness(-10)
        else:
            subprocess.run([
                "powershell", "-Command",
                "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                ".WmiSetBrightness(1, [Math]::Max(0, "
                "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness - 10))"
            ], check=False)

    def _linux_brightness(self, delta):
        """Adjust brightness via brightnessctl (install: sudo apt install brightnessctl)."""
        sign = "+" if delta > 0 else "-"
        pct = f"{abs(delta)}%{sign}"
        result = subprocess.run(["brightnessctl", "set", pct], check=False)
        if result.returncode != 0:
            # Fallback: try xrandr on X11
            subprocess.run(
                "xrandr --listmonitors | awk 'NR>1{print $4}' | "
                f"xargs -I{{}} xrandr --output {{}} --brightness "
                f"$(python3 -c \"import subprocess; cur=float(subprocess.check_output("
                f"['xrandr','--verbose']).decode().split('Brightness:')[1].split()[0]); "
                f"print(max(0.1,min(1.0,cur+{delta/100})))\")",
                shell=True, check=False
            )

    # ── Media ─────────────────────────────────────────────────────────────────

    def _play_pause(self):
        self._kb.press(Key.media_play_pause); self._kb.release(Key.media_play_pause)

    def _next_track(self):
        self._kb.press(Key.media_next); self._kb.release(Key.media_next)

    def _prev_track(self):
        self._kb.press(Key.media_previous); self._kb.release(Key.media_previous)