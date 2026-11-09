# Hand-Tracking Robot Arm

Move a 4-servo robot arm with your bare hand. A webcam watches your hand
(Python + OpenCV + MediaPipe), works out where it is, and sends servo angles
over USB to an Arduino Uno, which drives the servos.

| Your hand | The arm |
|---|---|
| moves left / right | **base** turns |
| moves up / down | **shoulder** (lift servo) raises or lowers the arm |
| moves closer / further from the camera | **elbow** (reach servo) reaches out or pulls back |
| pinches thumb and index finger together | **claw** closes (spread them to open) |

> **New to robotics?** Start with the step-by-step
> [beginner guide](GUIDE-FOR-HOORIYYA.md): setup, wiring, testing, and a
> ready-made classroom lesson.

Built for the common 3D-printed 4-DOF desktop arm with four **SG90** micro
servos (base, two side servos on a linkage, claw), but any 4-servo arm works
once you set its limits.

## Think of it like a puppet

A puppeteer moves their hand and the puppet copies it. Here the camera is the
puppeteer's eyes, the Python program is the brain that turns "hand is up and
to the left" into numbers ("base 140°, shoulder 120°"), and the USB cable is
the string that carries those numbers to the Arduino, which pulls the servos.

## How it works

1. **See the hand.** MediaPipe's hand landmarker finds 21 points on your hand
   (wrist, knuckles, finger tips) in every camera frame.
2. **Turn points into controls** (`arm_mapping.py`):
   - palm centre left/right → 0..1 → base angle
   - palm centre up/down → 0..1 → shoulder angle
   - hand size in the picture (wrist to middle knuckle) → how close it is → elbow angle
   - thumb-tip to index-tip distance ÷ hand size → claw angle
     (dividing by hand size means a pinch counts the same near or far)
3. **Smooth it.** Each angle eases toward its target and tiny changes are
   ignored, so the servos glide instead of shaking.
4. **Send it.** Lines like `90,120,75,40` go to the Arduino at 115200 baud,
   up to 30 times a second (and a repeat every 0.5 s as a "still here").
5. **Move safely** (`arduino/robot_arm/robot_arm.ino`): the Uno clamps every
   angle to safe limits, moves at most 1° every 10 ms, and goes home if it
   hears nothing for 3 seconds (for example if the program crashes).

## What you'll need

- Arduino Uno + USB cable
- The 4-servo arm (4 × SG90 or MG90S)
- **A separate 5 V supply for the servos, 2 A or more** (a 5 V phone charger
  with a cut cable, a 4×AA pack, or a 5 V buck module). Four SG90s can pull
  over 1 A when they start or push; the Uno's 5V pin can't supply that and the
  board will keep resetting.
- A breadboard or servo shield, jumper wires
- A webcam (the laptop's own camera is fine)
- Python 3.10–3.12 (MediaPipe may not have a build for the newest Python yet)

## Wiring

| Servo | Signal (orange) to Uno pin | Red | Brown |
|---|---|---|---|
| Base | D3 | 5 V supply + | GND |
| Shoulder (lift) | D5 | 5 V supply + | GND |
| Elbow (reach) | D6 | 5 V supply + | GND |
| Claw | D9 | 5 V supply + | GND |

**Join the supply's GND to the Uno's GND.** Without a shared ground the
signals have no reference and the servos twitch randomly.

```
 5V supply +  ──────────┬────────┬────────┬────────┐
                       red      red      red      red
                      BASE   SHOULDER   ELBOW    CLAW
                      brown    brown    brown    brown
 5V supply −  ──────────┴────────┴────────┴────────┴──── Uno GND
 Uno D3 ── base signal     Uno D5 ── shoulder signal
 Uno D6 ── elbow signal    Uno D9 ── claw signal
```

Which side servo is "lift" and which is "reach" depends on how your arm was
assembled: wiggle each one in step 3 and swap D5/D6 if needed.

## Setup

### 1. Upload the Arduino sketch

Open `arduino/robot_arm/robot_arm.ino` in the Arduino IDE, choose
**Arduino Uno** and its COM port, and upload. (`Servo` comes with the IDE.)

Or with arduino-cli:

```bash
arduino-cli compile --upload -p COM3 --fqbn arduino:avr:uno arduino/robot_arm
```

### 2. Install the Python side

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

The first run downloads MediaPipe's hand model (about 8 MB) into `models/`.

### 3. Find your arm's safe limits (do this before using the camera!)

Open the Serial Monitor at **115200 baud**, line ending **Newline**. It prints
`READY robot arm`. Type four angles (base, shoulder, elbow, claw) and press Enter:

```
90,95,95,50
```

Change one number at a time in small steps (5°) to find where each joint
stops before it hits the frame or another part. If a servo buzzes or gets
warm, it's pushing against something: back off. Type `H` to go home.

Put what you found in two places:
- `MIN_DEG` / `MAX_DEG` / `HOME_DEG` in the sketch (hard limits, re-upload)
- `BASE`, `SHOULDER`, `ELBOW`, `GRIPPER`, `HOME` in `config.py` (the range your hand sweeps)

**Close the Serial Monitor before step 4**: only one program can use the port.

### 4. Run it

```bash
python hand_arm.py                # finds the Arduino by itself
python hand_arm.py --port COM3    # or name the port
python hand_arm.py --no-arduino   # camera only, to try the tracking
python hand_arm.py --camera 1     # use a USB webcam instead of the built-in one
```

Hold one hand up, palm facing the camera, about an arm's length away.

| Key | Does |
|---|---|
| `q` / Esc | quit (arm goes home) |
| `h` | send the arm home |
| space | pause / resume the arm (tracking keeps going) |

No hand for 1.5 s and the arm drifts home on its own.

## Tuning (`config.py`)

| Problem | Fix |
|---|---|
| A joint moves the wrong way | swap its two numbers, e.g. `BASE = (30, 150)` |
| Arm is jittery | lower `SMOOTHING` (e.g. 0.15) or raise `DEADBAND_DEG` to 2 |
| Arm is slow to follow | raise `SMOOTHING` (e.g. 0.4) |
| Elbow barely moves | watch the hand size and set `HAND_SIZE_FAR` / `HAND_SIZE_NEAR` to your near and far |
| Claw won't close / open fully | adjust `PINCH_CLOSED` / `PINCH_OPEN` |
| Have to stretch to the edge of the picture | raise `MARGIN` |

## Troubleshooting

- **"No Arduino found"**: check the cable, then pass `--port COMx`
  (Arduino IDE → Tools → Port shows the number).
- **"Access is denied" / port busy**: close the Serial Monitor or Arduino IDE.
- **Arduino keeps resetting / servos shake when moving**: the servos need
  their own 5 V supply with the grounds joined.
- **Camera didn't open**: try `--camera 1`, or close other apps using the camera.
- **`pip install mediapipe` fails**: use Python 3.12 (`py -3.12 -m venv .venv`).

## Try it

- Add a second hand: `num_hands=2` and use the left hand for the claw.
- Record a sequence of angles and play it back with a key.
- Add a "freeze" gesture (closed fist) that holds the arm still.

## Files

| File | What it does |
|---|---|
| `hand_arm.py` | camera, hand tracking, drawing, sending to the Arduino |
| `arm_mapping.py` | the maths: hand points → servo angles, smoothing |
| `config.py` | all the settings you'd change |
| `arduino/robot_arm/robot_arm.ino` | Uno sketch: reads angles, moves servos safely |
| `tests/test_mapping.py` | checks the maths (`python tests/test_mapping.py`) |

Made by [Electronics Simplified](https://www.electronicssimplified.in). MIT licence.
