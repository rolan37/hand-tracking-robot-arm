"""Hand-tracking robot arm.

Watches your hand with the webcam (OpenCV + MediaPipe) and sends servo angles
to an Arduino Uno over USB:
    move your hand left/right  -> base turns
    move your hand up/down     -> shoulder lifts
    move your hand closer/away -> elbow reaches
    pinch thumb and index      -> gripper closes

Run:   python hand_arm.py              (finds the Arduino by itself)
       python hand_arm.py --port COM5
       python hand_arm.py --no-arduino (just the camera, to try the tracking)

Keys in the video window:  q = quit,  h = send arm home,  space = pause/resume the arm
"""

import argparse
import os
import sys
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

import config
from arm_mapping import Smoother, angles_from_hand

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
             "hand_landmarker/float16/1/hand_landmarker.task")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "hand_landmarker.task")

# Lines between the 21 hand points, for drawing the skeleton
HAND_LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
              (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
              (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]
JOINTS = ("Base", "Shoulder", "Elbow", "Gripper")


def get_model():
    """Download MediaPipe's hand model (about 8 MB) the first time."""
    if not os.path.exists(MODEL_PATH):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        print("Downloading the hand model (first run only)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH + ".part")
        os.replace(MODEL_PATH + ".part", MODEL_PATH)
    return MODEL_PATH


def find_arduino_port():
    from serial.tools import list_ports
    ports = [p for p in list_ports.comports() if "bluetooth" not in (p.description or "").lower()]
    for p in ports:
        text = f"{p.description} {p.manufacturer or ''}".lower()
        if any(w in text for w in ("arduino", "ch340", "ch341", "usb-serial", "usb serial", "wch")):
            return p.device
    return ports[0].device if len(ports) == 1 else None


class Arm:
    """Talks to arduino/robot_arm/robot_arm.ino. Does nothing if there is no Arduino."""

    def __init__(self, port, baud):
        self.ser = None
        if port is None:
            return
        import serial
        self.ser = serial.Serial(port, baud, timeout=0)
        print(f"Connected to Arduino on {port}. Waiting for it to restart...")
        time.sleep(2)            # the Uno resets when the port opens
        self.ser.reset_input_buffer()

    def send(self, angles):
        if self.ser:
            self.ser.write((",".join(str(a) for a in angles) + "\n").encode())

    def home(self):
        if self.ser:
            self.ser.write(b"H\n")

    def read_messages(self):
        if self.ser and self.ser.in_waiting:
            for line in self.ser.read(self.ser.in_waiting).decode(errors="ignore").splitlines():
                if line.strip():
                    print("Arduino:", line.strip())

    def close(self):
        if self.ser:
            self.home()
            time.sleep(0.1)
            self.ser.close()


def draw(frame, points, angles, status):
    h, w = frame.shape[:2]
    if points:
        px = [(int(x * w), int(y * h)) for x, y in points]
        for a, b in HAND_LINES:
            cv2.line(frame, px[a], px[b], (255, 132, 0), 2)
        for p in px:
            cv2.circle(frame, p, 4, (0, 179, 255), -1)
        cv2.line(frame, px[4], px[8], (0, 255, 0), 2)   # pinch line
    # Angle panel
    cv2.rectangle(frame, (8, 8), (230, 132), (51, 6, 6), -1)
    for i, (name, a) in enumerate(zip(JOINTS, angles)):
        y = 32 + i * 24
        cv2.putText(frame, f"{name:<9}{int(round(a)):>4} deg", (16, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.rectangle(frame, (150, y - 10), (150 + int(a / 180 * 70), y - 2), (0, 179, 255), -1)
    cv2.putText(frame, status, (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (255, 255, 255), 1, cv2.LINE_AA)


def main():
    ap = argparse.ArgumentParser(description="Move a servo robot arm with your hand.")
    ap.add_argument("--port", default=config.SERIAL_PORT, help="serial port, e.g. COM5")
    ap.add_argument("--camera", type=int, default=config.CAMERA_INDEX, help="camera number")
    ap.add_argument("--no-arduino", action="store_true", help="track only, send nothing")
    args = ap.parse_args()

    port = None
    if not args.no_arduino:
        port = args.port or find_arduino_port()
        if port is None:
            sys.exit("No Arduino found. Plug it in, pass --port COMx, or use --no-arduino.")
    arm = Arm(port, config.BAUD_RATE)

    options = vision.HandLandmarkerOptions(
        base_options=mp_tasks.BaseOptions(model_asset_path=get_model()),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.5,
    )
    landmarker = vision.HandLandmarker.create_from_options(options)

    cam = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    if not cam.isOpened():
        sys.exit(f"Camera {args.camera} didn't open. Try --camera 1.")

    smooth = Smoother(config.HOME, config.SMOOTHING, config.DEADBAND_DEG)
    arm.send(config.HOME)
    paused, last_send, last_write, last_seen = False, 0.0, 0.0, 0.0
    start = time.monotonic()
    print("Show your hand to the camera. q = quit, h = home, space = pause.")

    try:
        while True:
            ok, frame = cam.read()
            if not ok:
                print("Camera stopped sending pictures.")
                break
            if config.MIRROR:
                frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            stamp_ms = int((time.monotonic() - start) * 1000)
            result = landmarker.detect_for_video(image, stamp_ms)

            points = None
            now = time.monotonic()
            if result.hand_landmarks:
                points = [(lm.x, lm.y) for lm in result.hand_landmarks[0]]
                last_seen = now
                if not paused:
                    smooth.update(angles_from_hand(points, config))
            elif now - last_seen > 1.5 and not paused:
                smooth.update(config.HOME)      # no hand for a while: drift home

            if now - last_send >= config.SEND_EVERY_S:
                angles = None if paused else smooth.changed()
                if angles:
                    arm.send(angles)
                    last_write = now
                elif now - last_write > 0.5:
                    arm.send(smooth.sent)   # keep-alive, so the Arduino knows we're still here
                    last_write = now
                last_send = now
            arm.read_messages()

            status = "PAUSED (space to resume)" if paused else (
                "Tracking" if points else "No hand - show your palm")
            status += f"   |   {'Arduino ' + port if port else 'no Arduino'}"
            draw(frame, points, smooth.value, status)
            cv2.imshow("Hand-tracking robot arm", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("h"):
                smooth = Smoother(config.HOME, config.SMOOTHING, config.DEADBAND_DEG)
                arm.send(config.HOME)
            if key == ord(" "):
                paused = not paused
    finally:
        cam.release()
        cv2.destroyAllWindows()
        landmarker.close()
        arm.close()


if __name__ == "__main__":
    main()
