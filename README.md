# Gesture Control

Control your computer's **volume, brightness, and media playback** with hand gestures using an **Intel RealSense** depth camera and **MediaPipe** hand tracking.

## Gestures

| Gesture | Action |
|---|---|
| ✋ Open Palm (hold) | Volume Up |
| ✊ Fist (hold) | Volume Down |
| ☝️ Point up (drag up) | Brightness Up |
| ☝️ Point up (drag down) | Brightness Down |
| 🤌 Pinch | Play / Pause |
| 👉 Swipe Right | Next Track |
| 👈 Swipe Left | Previous Track |

> **Tip:** For brightness, extend only your index finger and drag it up or down like a real dimmer switch.

---

## Setup

### 1. Install the RealSense SDK

Download and install from Intel's official releases:
https://github.com/IntelRealSense/librealsense/releases

Make sure `realsense-viewer` works before continuing.

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note:** If `pyrealsense2` fails to install via pip (common on Linux ARM / macOS Apple Silicon), build it from source or use the `.whl` from Intel's GitHub releases page.

### 4. Linux only — install brightnessctl for brightness control

```bash
sudo apt install brightnessctl
```

Not needed on macOS or Windows.

### 5. Run

```bash
python main.py
```

Press **Q** to quit.

---

## Project Structure

```
gesture_control/
├── main.py                   # Entry point — ties everything together
├── requirements.txt
├── src/
│   ├── camera.py             # RealSense RGB + depth stream manager
│   ├── hand_tracker.py       # MediaPipe hand landmark detection (new + legacy API)
│   ├── gesture_recognizer.py # Stateful gesture classification
│   ├── system_controller.py  # Maps gestures → system actions
│   └── hud.py                # On-screen overlay (gesture label, FPS, legend)
```

---

## How It Works

1. **`camera.py`** opens the RealSense pipeline and aligns the depth stream to the colour stream so every pixel has a real-world depth value (in metres).
2. **`hand_tracker.py`** runs MediaPipe Hands on each colour frame to get 21 normalised (x, y) landmark positions. Supports both the legacy `mp.solutions` API and the newer Tasks API (0.10+).
3. **`camera.py`** enriches each landmark with its depth value from the RealSense frame, giving you true 3D coordinates.
4. **`gesture_recognizer.py`** classifies the current hand pose using geometric rules — finger extension, pinch distance, wrist travel history for swipes, and index fingertip vertical travel for brightness.
5. **`system_controller.py`** maps the gesture to a system action, with debouncing for one-shot gestures and a hold-interval for continuous ones (volume).
6. **`hud.py`** draws the gesture label, FPS counter, action notification, and legend onto each frame.

---

## Webcam Fallback

If `pyrealsense2` is not installed, the app falls back to your regular webcam. All gestures still work — you just lose the depth data (3D landmark enrichment is skipped). Great for testing without the camera plugged in.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `module 'mediapipe' has no attribute 'solutions'` | Updated `hand_tracker.py` handles this — it auto-detects your MediaPipe version |
| `pyrealsense2` not found | Install from Intel releases, not just pip |
| No hand detected | Make sure your hand is well-lit and within ~1.5 m |
| Volume keys not working on Linux | `pip install python-xlib` |
| Brightness not changing on Linux | `sudo apt install brightnessctl` |
| Brightness not changing on macOS | System Settings → Privacy → Accessibility → add Terminal |
| macOS Accessibility error (any keys) | System Settings → Privacy → Accessibility → add Terminal |
| Low FPS | Reduce resolution in `camera.py` (e.g. 424×240) |

---

