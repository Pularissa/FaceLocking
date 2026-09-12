# src/test_servo.py
"""
Interactive ESP8266 Servo Hardware Diagnostic & Tester.
Verifies serial communication, firmware ACKs, and physical servo motion.

Run:
    python -m src.test_servo --port COM13
"""
from __future__ import annotations

import argparse
import sys
import time
import serial


def run_diagnostic(port: str, baud: int = 115200):
    print("=" * 65)
    print(f"  ESP8266 SERVO HARDWARE DIAGNOSTIC & TESTER ({port})")
    print("=" * 65)
    print("Wiring Checklist (SG90 / Standard Servo):")
    print("  1. RED Wire    -> 'VIN' or '5V' pin on ESP8266 (Needs 5V from USB)")
    print("  2. BROWN/BLACK -> 'GND' pin on ESP8266")
    print("  3. YELLOW/ORANGE -> 'D1' (GPIO5) or 'D2' (GPIO4) pin on ESP8266")
    print("-" * 65)

    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        ser.setDTR(False)
        ser.setRTS(False)
        time.sleep(2.0)  # Wait for ESP8266 boot
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print(f"[Serial] Connected successfully to {port} @ {baud} baud.")
    except Exception as e:
        print(f"[Serial Error] Failed to open {port}: {e}")
        return

    # Check for startup banner
    while ser.in_waiting:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if line:
            print(f"[ESP8266 Boot] {line}")

    print("\nSelect Test Mode:")
    print("  [1] Automated Continuous Sweep (Left-Center-Right)")
    print("  [2] Interactive Manual Angle Testing (Type angle 15-165)")
    print("  [Q] Exit")
    
    choice = input("\nEnter choice [1/2/Q] (default: 1): ").strip()
    if choice.lower() == "q":
        ser.close()
        return

    if choice == "2":
        print("\n--- Manual Angle Control ---")
        print("Type an angle between 15 and 165, then press Enter. Type 'q' to stop.")
        while True:
            val = input("Target Angle (15-165) > ").strip()
            if val.lower() in ("q", "exit"):
                break
            if not val.isdigit():
                print("Please enter a numeric angle.")
                continue
            angle = int(val)
            if not (10 <= angle <= 170):
                print("Angle must be between 10 and 170.")
                continue

            ser.write(f"{angle}\n".encode("ascii"))
            ser.flush()
            time.sleep(0.1)

            response = ""
            while ser.in_waiting:
                response += ser.readline().decode("utf-8", errors="ignore").strip() + " "
            
            print(f"-> Sent {angle} deg | ESP8266 Response: {response if response.strip() else 'No ACK'}")
    else:
        print("\n--- Starting Automated Sweep ---")
        print("Moving servo: 45° -> 90° -> 135° -> 90° -> 30° -> 150° -> 90°")
        print("Press Ctrl+C to stop.\n")

        test_sequence = [45, 90, 135, 90, 30, 150, 90]
        try:
            for cycle in range(1, 4):
                print(f"--- Cycle {cycle}/3 ---")
                for angle in test_sequence:
                    print(f"Moving to: {angle:3d}° ... ", end="", flush=True)
                    ser.write(f"{angle}\n".encode("ascii"))
                    ser.flush()
                    time.sleep(0.6)

                    response = ""
                    while ser.in_waiting:
                        response += ser.readline().decode("utf-8", errors="ignore").strip() + " "

                    print(f"ACK: {response.strip() if response.strip() else 'OK'}")

            print("\n[Diagnostic Result]:")
            print("  - If ESP8266 replied with ACK and the servo MOVED: Hardware is 100% OK!")
            print("  - If ESP8266 replied with ACK but servo DID NOT MOVE:")
            print("      * Check RED wire: Is it plugged into 'VIN' (5V) on ESP8266?")
            print("      * Check SIGNAL wire: Is it plugged into D1 (GPIO5) or D2 (GPIO4)?")
            print("      * Check power: SG90 needs sufficient USB current to turn the motor gears.")

        except KeyboardInterrupt:
            print("\nSweep cancelled by user.")

    # Return to 90 degrees center
    ser.write(b"90\n")
    ser.flush()
    ser.close()
    print("\nDiagnostic completed. Port closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test ESP8266 Servo motor sweep and diagnostics")
    parser.add_argument("--port", default="COM13", help="COM port (e.g. COM13)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    args = parser.parse_args()
    run_diagnostic(args.port, args.baud)
