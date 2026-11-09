"""Run with:  python -m pytest tests   (or just: python tests/test_mapping.py)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from arm_mapping import Smoother, angles_from_hand


def fake_hand(cx, cy, size=0.2, pinch=0.1):
    """21 points: wrist below the palm centre, middle knuckle above it."""
    pts = [(cx, cy)] * 21
    pts[0] = (cx, cy + size / 2)          # wrist
    pts[9] = (cx, cy - size / 2)          # middle knuckle
    pts[4] = (cx - pinch * size / 2, cy)  # thumb tip
    pts[8] = (cx + pinch * size / 2, cy)  # index tip
    return pts


def test_left_right_moves_base_end_to_end():
    left = angles_from_hand(fake_hand(0.05, 0.5), config)
    right = angles_from_hand(fake_hand(0.95, 0.5), config)
    assert round(left[0]) == config.BASE[0]
    assert round(right[0]) == config.BASE[1]


def test_up_down_moves_shoulder():
    high = angles_from_hand(fake_hand(0.5, 0.1), config)
    low = angles_from_hand(fake_hand(0.5, 0.9), config)
    assert round(high[1]) == config.SHOULDER[0]
    assert round(low[1]) == config.SHOULDER[1]


def test_near_far_moves_elbow():
    far = angles_from_hand(fake_hand(0.5, 0.5, size=0.05), config)
    near = angles_from_hand(fake_hand(0.5, 0.5, size=0.4), config)
    assert round(far[2]) == config.ELBOW[0]
    assert round(near[2]) == config.ELBOW[1]


def test_pinch_closes_gripper():
    closed = angles_from_hand(fake_hand(0.5, 0.5, pinch=0.1), config)
    opened = angles_from_hand(fake_hand(0.5, 0.5, pinch=1.5), config)
    assert round(closed[3]) == config.GRIPPER[0]
    assert round(opened[3]) == config.GRIPPER[1]


def test_angles_stay_in_servo_range():
    for x in (-0.5, 0, 0.5, 1, 1.5):
        for a in angles_from_hand(fake_hand(x, x, size=x * 0.5 + 0.01, pinch=x * 3), config):
            assert 0 <= a <= 180


def test_smoother_deadband():
    s = Smoother((90, 90, 90, 90), alpha=1, deadband=2)
    s.update((90.4, 90, 90, 90))
    assert s.changed() is None
    s.update((95, 90, 90, 90))
    assert s.changed() == [95, 90, 90, 90]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
