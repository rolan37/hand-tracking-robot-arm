"""Settings you are most likely to change. Edit these, then run hand_arm.py again."""

# ---------- Serial link to the Arduino ----------
SERIAL_PORT = None        # None = find the Arduino automatically, or e.g. "COM5" / "/dev/ttyUSB0"
BAUD_RATE = 115200        # must match Serial.begin() in arduino/robot_arm/robot_arm.ino
SEND_EVERY_S = 1 / 30     # send at most 30 angle updates per second

# ---------- Camera ----------
CAMERA_INDEX = 0          # 0 = built-in webcam, 1 = first USB webcam, ...
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MIRROR = True             # flip the picture so moving your hand right moves the arm right

# ---------- Servo limits (degrees) ----------
# Set up for the 4-servo SG90 desktop arm (base, two side servos on a
# linkage, claw). Each joint: (angle when your hand is at one end, angle at
# the other end). Swap the two numbers if a joint moves the wrong way.
# Find the real limits for YOUR arm with the Serial Monitor first (README,
# step 3) and keep these inside them: an SG90 pushing against a stop gets hot
# and strips its gears.
BASE = (150, 30)          # hand left ... hand right
SHOULDER = (130, 60)      # "lift" side servo:  hand high ... hand low
ELBOW = (60, 130)         # "reach" side servo: hand far from camera ... hand close
GRIPPER = (30, 75)        # claw: fingers pinched (closed) ... fingers apart (open)

HOME = (90, 95, 95, 50)   # base, shoulder, elbow, gripper when no hand is seen

# ---------- Feel ----------
SMOOTHING = 0.25          # 0..1, lower = smoother but slower to follow
DEADBAND_DEG = 1          # ignore changes smaller than this (stops servo jitter)

# Hand "size" in the picture (wrist to middle-finger knuckle, as a share of the
# picture height). Used to guess how close your hand is to the camera.
HAND_SIZE_FAR = 0.12
HAND_SIZE_NEAR = 0.30

# Pinch = distance thumb tip to index tip, divided by hand size.
PINCH_CLOSED = 0.25
PINCH_OPEN = 1.0

# The middle part of the picture that maps to the full servo range.
# A margin means you don't have to reach the very edge of the camera view.
MARGIN = 0.15
