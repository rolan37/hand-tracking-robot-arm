/*
  Hand-tracking robot arm: Arduino Uno side.

  Listens on USB serial (115200 baud) for lines like
      90,120,75,40      base,shoulder,elbow,gripper in degrees
      H                 go to the home position
  and moves four servos there smoothly.

  You can also type these lines into the Arduino Serial Monitor
  (115200 baud, "Newline") to test each servo before using the camera.

  Wiring: servo signal wires to pins 3, 5, 6, 9.
  Power the servos from a separate 5-6 V supply (not the Uno's 5V pin),
  and join that supply's GND to the Uno's GND.
*/

#include <Servo.h>

const byte NUM = 4;
// base, shoulder (lift side servo), elbow (reach side servo), gripper (claw)
const byte PINS[NUM]     = {3, 5, 6, 9};
// Hard safety limits. The arm never goes past these, whatever the PC sends.
// Find your arm's real limits in the Serial Monitor (README, step 3) and set them here.
const int  MIN_DEG[NUM]  = {10, 50, 50, 20};
const int  MAX_DEG[NUM]  = {170, 140, 140, 85};
const int  HOME_DEG[NUM] = {90, 95, 95, 50};

const unsigned long STEP_MS = 10;        // move 1 degree every 10 ms at most (~100 deg/s)
const unsigned long TIMEOUT_MS = 3000;   // no message for 3 s: go home

Servo servos[NUM];
float current[NUM];
int target[NUM];
unsigned long lastStep = 0, lastMessage = 0;
bool timedOut = false;

char buf[32];
byte len = 0;

void goHome() {
  for (byte i = 0; i < NUM; i++) target[i] = HOME_DEG[i];
}

void handleLine(char *line) {
  if (line[0] == 'H' || line[0] == 'h') {
    goHome();
    Serial.println(F("OK home"));
    return;
  }
  int vals[NUM];
  byte n = 0;
  char *tok = strtok(line, ",");
  while (tok && n < NUM) {
    vals[n++] = atoi(tok);
    tok = strtok(NULL, ",");
  }
  if (n != NUM) {
    Serial.println(F("ERR send 4 numbers: base,shoulder,elbow,gripper"));
    return;
  }
  for (byte i = 0; i < NUM; i++) target[i] = constrain(vals[i], MIN_DEG[i], MAX_DEG[i]);
}

void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (len > 0) {
        buf[len] = '\0';
        handleLine(buf);
        len = 0;
        lastMessage = millis();
        timedOut = false;
      }
    } else if (len < sizeof(buf) - 1) {
      buf[len++] = c;
    } else {
      len = 0;  // line too long: throw it away
    }
  }
}

void setup() {
  Serial.begin(115200);
  for (byte i = 0; i < NUM; i++) {
    current[i] = HOME_DEG[i];
    target[i] = HOME_DEG[i];
    servos[i].attach(PINS[i]);
    servos[i].write(HOME_DEG[i]);
    delay(200);  // start servos one by one so the supply isn't hit all at once
  }
  lastMessage = millis();
  Serial.println(F("READY robot arm"));
}

void loop() {
  readSerial();

  if (!timedOut && millis() - lastMessage > TIMEOUT_MS) {
    goHome();
    timedOut = true;
  }

  // Ease every servo one step toward its target
  if (millis() - lastStep >= STEP_MS) {
    lastStep = millis();
    for (byte i = 0; i < NUM; i++) {
      float diff = target[i] - current[i];
      if (diff > 1) diff = 1;
      if (diff < -1) diff = -1;
      if (diff != 0) {
        current[i] += diff;
        servos[i].write((int)current[i]);
      }
    }
  }
}
