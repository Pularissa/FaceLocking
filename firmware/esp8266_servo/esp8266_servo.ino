/*
 * High-Precision Single Servo Tracker for ESP8266
 * 
 * Hardware Wiring (ESP8266 NodeMCU / D1 Mini):
 *   - Signal (Yellow/Orange) -> Pin D1 (GPIO 5)
 *   - Power (Red)            -> Pin VIN or 5V (5V USB power)
 *   - Ground (Brown/Black)   -> Pin GND
 * 
 * Communication:
 *   - Baud Rate: 115200 baud
 *   - Protocol: Angle integer followed by newline (e.g. "90\n")
 *   - Behavior: Stays centered at 90° until Python sends face tracking coordinates.
 */

#include <Servo.h>

#ifndef D1
#define D1 5
#endif

// Pin D1 (GPIO 5)
const int SERVO_PIN = D1;
Servo myServo;

int currentAngle = 90;

// Fast non-blocking serial receive buffer
char rxBuffer[16];
int rxIndex = 0;

void setup() {
  Serial.begin(115200);

  // Attach servo on D1 with standard 544us to 2400us pulse width
  myServo.attach(SERVO_PIN, 544, 2400);

  // 1-Time Startup Test: Center -> Left -> Right -> Center (takes 0.8s)
  myServo.write(90);
  delay(300);
  myServo.write(60);
  delay(250);
  myServo.write(120);
  delay(250);
  myServo.write(90);

  Serial.println("\n=== ESP8266 SERVO TRACKER (PIN D1) READY ===");
  Serial.println("Holding at center (90°). Waiting for Python face tracker on COM port...");
}

void loop() {
  // Read incoming angle commands from Python (e.g., "90\n", "75\n", "110\n")
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (rxIndex > 0) {
        rxBuffer[rxIndex] = '\0';
        int angle = atoi(rxBuffer);
        rxIndex = 0;

        // Verify valid angle in SG90 operating bounds (15° to 165°)
        if (angle >= 10 && angle <= 170) {
          currentAngle = angle;
          myServo.write(currentAngle);

          // Return ACK to Python
          Serial.print("ACK:");
          Serial.println(currentAngle);
        }
      }
    } else if (c >= '0' && c <= '9') {
      if (rxIndex < (int)sizeof(rxBuffer) - 1) {
        rxBuffer[rxIndex++] = c;
      }
    }
  }
}
