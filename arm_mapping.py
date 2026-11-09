"""Turns hand landmarks into servo angles. Plain maths, no camera, so it is easy to test.

MediaPipe gives 21 points per hand, each with x and y from 0 to 1
(0,0 = top left of the picture). The ones used here:
    0 = wrist, 4 = thumb tip, 8 = index tip, 9 = middle-finger knuckle
"""

import math

WRIST, THUMB_TIP, INDEX_TIP, MIDDLE_MCP = 0, 4, 8, 9


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def scale(v, in_lo, in_hi):
    """Where v sits between in_lo and in_hi, as 0..1 (clamped)."""
    if in_hi == in_lo:
        return 0.0
    return clamp((v - in_lo) / (in_hi - in_lo))


def to_angle(t, joint):
    """t in 0..1 -> angle between joint[0] and joint[1]."""
    a, b = joint
    return a + (b - a) * t


def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def hand_features(points, margin=0.15):
    """points: 21 (x, y) pairs in 0..1. Returns the four 0..1 controls."""
    wrist, knuckle = points[WRIST], points[MIDDLE_MCP]
    size = dist(wrist, knuckle) or 1e-6
    # Palm centre: halfway between wrist and middle knuckle
    cx = (wrist[0] + knuckle[0]) / 2
    cy = (wrist[1] + knuckle[1]) / 2
    return {
        "x": scale(cx, margin, 1 - margin),        # 0 = left, 1 = right
        "y": scale(cy, margin, 1 - margin),        # 0 = top, 1 = bottom
        "size": size,                              # bigger = closer to camera
        "pinch": dist(points[THUMB_TIP], points[INDEX_TIP]) / size,
    }


def angles_from_hand(points, cfg):
    """Returns (base, shoulder, elbow, gripper) in degrees, as floats."""
    f = hand_features(points, cfg.MARGIN)
    near = scale(f["size"], cfg.HAND_SIZE_FAR, cfg.HAND_SIZE_NEAR)
    opened = scale(f["pinch"], cfg.PINCH_CLOSED, cfg.PINCH_OPEN)
    return (
        to_angle(f["x"], cfg.BASE),
        to_angle(f["y"], cfg.SHOULDER),
        to_angle(near, cfg.ELBOW),
        to_angle(opened, cfg.GRIPPER),
    )


class Smoother:
    """Exponential smoothing plus a dead band, so the servos glide instead of shaking."""

    def __init__(self, start, alpha=0.25, deadband=1):
        self.value = [float(a) for a in start]
        self.sent = [int(round(a)) for a in start]
        self.alpha = alpha
        self.deadband = deadband

    def update(self, target):
        self.value = [v + self.alpha * (t - v) for v, t in zip(self.value, target)]
        return self.value

    def changed(self):
        """Rounded angles if any moved more than the dead band since last send, else None."""
        now = [int(round(v)) for v in self.value]
        if any(abs(n - s) >= self.deadband for n, s in zip(now, self.sent)):
            self.sent = now
            return now
        return None
