# Hand-Tracking Robot Arm: Step-by-Step Guide

**For Hooriyya**, from Rolan. No robotics experience needed. Follow the steps
in order and tick each check before moving on. It takes about an hour and a
half the first time; after that, about 5 minutes to set up.

---

## What you are building

You hold your hand up to a laptop's webcam. The robot arm copies you:

| You do this | The arm does this |
|---|---|
| Move your hand left or right | Turns left or right |
| Move your hand up or down | Lifts or lowers |
| Move your hand closer to or further from the camera | Reaches forward or pulls back |
| Pinch your thumb and first finger together | Closes its claw (open your fingers to open it) |

### The big idea, as you might tell a class: a puppet show

- The **webcam** is the puppeteer's **eyes**: it watches your hand.
- The **Python program** on the laptop is the **brain**: it finds 21 points on
  your hand (wrist, knuckles, fingertips) and turns "the hand is up and to
  the left" into numbers like *base 140°, lift 120°*.
- The **USB cable** is the **string**: it carries those numbers to the Arduino.
- The **Arduino** is the **puppeteer's hands**: it pulls the four servos.
- The **servos** are the puppet's **joints**.

---

## Words you'll meet

| Word | What it means |
|---|---|
| **Arduino Uno** | A small blue circuit board, a tiny computer that controls motors and lights. It runs one program (a "sketch") at a time. |
| **Sketch** | A program for the Arduino. Ours is `robot_arm.ino`. |
| **Upload** | Copy a sketch from the laptop onto the Arduino. It stays there even when unplugged. |
| **Servo** | A small motor that turns to an exact angle (0° to 180°) and holds it. The arm has four small blue **SG90** servos. |
| **Signal / power / ground** | Every servo has 3 wires. **Orange** = signal (which angle to go to), **red** = power (+5 V), **brown** = ground (−, the "return path"). |
| **Ground (GND)** | The shared "zero" for all the electronics. Everything's ground must be joined, like everyone in a choir needing the same starting note. |
| **COM port** | The name Windows gives the Arduino's USB connection, e.g. `COM3`. |
| **Serial Monitor** | A window in the Arduino software where you can type messages to the Arduino and read its replies. |
| **Python** | The programming language the hand-tracking program is written in. |
| **Terminal** | A window where you type commands instead of clicking. |

---

## Part 1: Check your kit

- [ ] The robot arm with its **4 servos** (base, two on the sides, one on the claw)
- [ ] **Arduino Uno** and its **USB cable** (square USB-B end)
- [ ] **A 5 V power supply for the servos, 2 A or more**: a 5 V adapter, a
      USB power bank with a cut USB cable, or a 4×AA battery holder
- [ ] **Breadboard** and **jumper wires** (male-to-male), or a servo shield on the Uno
- [ ] A **laptop with a webcam** (Windows 10 or 11)

> ⚠️ **Why a separate power supply?** Four servos moving together need more
> electricity than the Arduino can give. Powered from the Arduino alone, the
> arm shakes, and the Arduino keeps restarting. It's like running four fans
> from one phone charger.

---

## Part 2: Install the software (once per laptop)

### 2a. Arduino IDE

1. Go to **arduino.cc/en/software** and download **Arduino IDE 2** for Windows.
2. Install it with the default options. Click **Install** whenever Windows asks
   to install drivers (these let the laptop talk to the Arduino).

### 2b. Python 3.12

1. Go to **python.org/downloads/windows** and download the latest
   **Python 3.12** "Windows installer (64-bit)".
   *Use 3.12, not the newest version: the hand-tracking library
   (MediaPipe) may not work on the newest one yet.*
2. Run it and **tick "Add python.exe to PATH"** at the bottom of the first
   screen, then click **Install Now**.

### 2c. The project files

1. Open **github.com/rolan37/hand-tracking-robot-arm**.
   (If you see "404", ask Rolan to add your GitHub account to the repository.)
2. Click the green **Code** button → **Download ZIP**.
3. Right-click the ZIP → **Extract All**, and put the folder somewhere easy,
   e.g. `Documents\hand-tracking-robot-arm`.

### 2d. Install the Python libraries

1. Open the project folder in File Explorer.
2. Click in the address bar at the top, type `cmd`, and press Enter.
   A black **terminal** window opens, already in the project folder.
3. Type these lines one at a time, pressing Enter after each:

   ```bat
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   The first makes a private Python space for this project (a "virtual
   environment"), the second switches it on (you'll see `(.venv)` at the
   start of the line), and the third downloads the libraries. It takes a few
   minutes.

✅ **Check:** the last line says `Successfully installed ...` with no red `ERROR`.

---

## Part 3: Upload the program to the Arduino

1. Plug the Arduino into the laptop with the USB cable. **Don't connect the
   servos yet.** A green light comes on.
2. Open **Arduino IDE** → **File → Open** → choose
   `arduino\robot_arm\robot_arm.ino` from the project folder.
3. At the top, open the board menu and pick **Arduino Uno** on its **COM**
   port. (Not sure which COM? Unplug the Arduino and see which one disappears.)
4. Click the **→ Upload** button (the right arrow).

✅ **Check:** the bottom says **Done uploading**.

5. Open **Tools → Serial Monitor**. At the bottom right, set **115200 baud** and
   **Newline**. Press the Arduino's small **reset** button.

✅ **Check:** you see `READY robot arm`.

---

## Part 4: Wire it up

**Unplug the USB cable and switch the 5 V supply off while wiring.**

Each servo's 3 wires go to three different places:

| Servo | Orange (signal) → Arduino pin | Red (power) → | Brown (ground) → |
|---|---|---|---|
| Base (the one under the turntable) | **3** | 5 V supply **+** | supply **−** |
| Lift (one side servo) | **5** | 5 V supply **+** | supply **−** |
| Reach (the other side servo) | **6** | 5 V supply **+** | supply **−** |
| Claw | **9** | 5 V supply **+** | supply **−** |

And one extra wire, the one people forget:

| From | To |
|---|---|
| 5 V supply **−** | Arduino **GND** pin |

On a breadboard: plug the supply's + into the red (+) rail and − into the
blue (−) rail. Then all four red wires go into the + rail, all four brown
wires into the − rail, and one jumper goes from the − rail to the Arduino's GND.

```
  5V supply +  ── red rail ── 4 red servo wires
  5V supply −  ── blue rail ─ 4 brown servo wires ── 1 jumper ── Arduino GND
  Arduino pin 3 ── base orange      Arduino pin 5 ── lift orange
  Arduino pin 6 ── reach orange     Arduino pin 9 ── claw orange
```

> ⚠️ **Never** connect the 5 V supply's + to the Arduino's 5V pin, and don't
> put the servos' red wires on the Arduino. Only the orange wires and one
> GND wire go to the Arduino.

✅ **Check before powering on:** count them. 4 orange wires on pins 3, 5, 6, 9.
4 red on +. 4 brown on −. 1 wire from − to Arduino GND.

---

## Part 5: Test each servo by hand (important!)

This is where you find how far each joint can safely move. A servo that is
told to go further than the arm allows pushes against the plastic, buzzes,
gets hot, and can strip its gears.

1. Switch on the 5 V supply, plug in the USB cable, and open the
   **Serial Monitor** (115200 baud, Newline). The arm moves to its home
   position.
2. In the box at the top, type four numbers separated by commas,
   then press Enter:

   ```
   90,95,95,50
   ```

   They are the angles for **base, lift, reach, claw**, in that order.
3. Change **one number at a time, 5 at a time**. For example, to test the base:
   `100,95,95,50` → `110,95,95,50` → `120,95,95,50` ...
   Stop as soon as the joint touches something or the servo starts to
   **buzz**. Go back 5°. Write that number down.
4. Do the same in the other direction, then for each joint.
5. Type `H` and press Enter to send the arm home at any time.

Fill this in:

| Joint | Smallest safe angle | Largest safe angle |
|---|---|---|
| Base | | |
| Lift | | |
| Reach | | |
| Claw (closed / open) | | |

> 💡 If the "lift" servo actually makes the arm reach (or the other way
> round), swap the orange wires on pins 5 and 6.

Now put your numbers into the two files (or ask Rolan to):

- In `robot_arm.ino`, the lines `MIN_DEG` and `MAX_DEG` (the hard limits the
  arm will never pass). Upload again after changing them.
- In `config.py` (open with Notepad), `BASE`, `SHOULDER` (lift), `ELBOW`
  (reach) and `GRIPPER` (claw): the range your hand will sweep. Keep them
  inside your safe numbers.

**Close the Serial Monitor when you're done.** Only one program can talk
to the Arduino at a time.

---

## Part 6: Run it!

1. In the terminal in the project folder (Part 2d steps 1–2), type:

   ```bat
   .venv\Scripts\activate
   python hand_arm.py
   ```

   The first time, it downloads a small hand model (about 8 MB).
2. A video window opens. Stand about an arm's length from the camera and hold
   **one hand up, palm facing the camera**. You'll see dots and lines on your
   hand and four angles in the top-left corner.
3. Move slowly at first. The arm follows.

| Key (click the video window first) | What it does |
|---|---|
| **Space** | Pause the arm (to rest or explain something); press again to resume |
| **H** | Send the arm home |
| **Q** | Quit (the arm goes home) |

The arm also goes home by itself if it can't see a hand for 1.5 seconds,
or if the program stops.

> 💡 **No arm today?** `python hand_arm.py --no-arduino` runs only the hand
> tracking, which is great for showing a class how the computer "sees" a hand.

---

## Part 7: When something goes wrong

| What you see | What to do |
|---|---|
| `No Arduino found` | Check the USB cable, then run `python hand_arm.py --port COM3` (use your COM number from Part 3). |
| `Access is denied` or `could not open port` | The Serial Monitor or Arduino IDE is still using the port. Close it. |
| `Camera 0 didn't open` | Close Zoom/Teams/Camera app. For a USB webcam: `python hand_arm.py --camera 1`. |
| `'python' is not recognized` | You missed "Add python.exe to PATH". Run the Python installer again → Modify. |
| `No module named cv2` | Type `.venv\Scripts\activate` first, then run again. |
| Arm shakes or the Arduino keeps restarting | The servos need their own 5 V supply, and supply − must be wired to Arduino GND. |
| One servo doesn't move at all | Check its orange wire is on the right pin and its red/brown wires are in the rails. |
| A joint moves the wrong way | In `config.py`, swap the two numbers for that joint, e.g. `BASE = (30, 150)`. |
| Arm is too jumpy | In `config.py`, change `SMOOTHING = 0.25` to `0.15`. |
| A servo buzzes and gets warm | It's pushing against the frame. Press **H**, then shrink that joint's limits (Part 5). |
| Tracking is poor | Better light on your hand, a plain background, only one hand in view. |

---

## Part 8: Using it in class

**Safety:** small servos are weak, but keep fingers out of the claw and the
joints while it's moving, and switch the power off before changing wires.

### Suggested lesson (about 60 minutes, ages 11+)

1. **Hook (5 min):** run it. Ask: *"How does the arm know where my hand is?"*
2. **How a computer sees (10 min):** run `--no-arduino`. Point out the 21 dots.
   The computer doesn't "see" a hand: it finds a pattern and gives each dot an
   x and y position, like coordinates on a graph.
3. **From position to angle (10 min):** hand at the left edge = 150°, right
   edge = 30°, in between = in between. Let students predict the angle before
   moving their hand, then check the number on screen.
4. **Servos (10 min):** use the Serial Monitor to type angles. Students
   discover the limits themselves and record them in the table from Part 5.
5. **Challenge (20 min):** in teams, pick up a small sponge or paper ball and
   drop it in a cup using only hand gestures. Time each team.
6. **Reflect (5 min):** where are robots like this used? (Surgery robots,
   bomb disposal, handling dangerous chemicals, space.)

### Questions to ask students

- Why does pinching close the claw even when your hand is far from the camera?
  *(The program divides the pinch distance by the size of your hand.)*
- What happens if two people put their hands up? *(It follows only one.)*
- Why does the arm move smoothly instead of jumping? *(Each angle moves only
  part of the way to its target every frame, and the Arduino moves at most
  1° every 10 ms.)*

---

## Quick start (after the first time)

1. Wire the servos (Part 4), supply on, USB in.
2. In the project folder's address bar type `cmd`, then:

   ```bat
   .venv\Scripts\activate
   python hand_arm.py
   ```

3. Hand up, palm to the camera. **Q** to quit.

Questions? Ask Rolan, or see `README.md` for the technical details.
