"""
Gesture Control - Main Entry Point
====================================
Run this file to start the gesture controller.
Usage: python main.py
"""

from camera import RealSenseCamera
from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer
from system_controller import SystemController
from hud import HUD
import cv2


def main():
    print("🖐  Gesture Control Starting...")
    print("Controls:")
    print("  Open Palm (hold)     → Increase volume")
    print("  Fist (hold)          → Decrease volume")
    print("  Swipe Right          → Next track")
    print("  Swipe Left           → Previous track")
    print("  Pinch                → Play / Pause")
    print("  Press Q to quit\n")

    camera = RealSenseCamera()
    tracker = HandTracker()
    recognizer = GestureRecognizer()
    controller = SystemController()
    hud = HUD()

    try:
        camera.start()
        print("RealSense camera connected.\n")

        while True:
            color_frame, depth_frame = camera.get_frames()
            if color_frame is None:
                continue

            # Detect hand landmarks (2D)
            landmarks_2d, annotated_frame = tracker.detect(color_frame)

            # Enrich landmarks with depth (3D)
            landmarks_3d = None
            if landmarks_2d and depth_frame is not None:
                landmarks_3d = camera.add_depth_to_landmarks(landmarks_2d, depth_frame)

            # Recognize gesture
            gesture = recognizer.recognize(landmarks_2d, landmarks_3d)

            # Trigger system action
            action_label = controller.handle(gesture)

            # Draw HUD overlay
            display = hud.draw(annotated_frame, gesture, action_label)

            cv2.imshow("Gesture Control", display)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        camera.stop()
        cv2.destroyAllWindows()
        print("Goodbye!")


if __name__ == "__main__":
    main()
