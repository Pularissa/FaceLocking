import time
import serial
import cv2
from camera import CSICamera
from detect import calculate_vertical_error

# Configure Serial Port (Update COM port for Windows or /dev/ttyUSB0 for Linux)
SERIAL_PORT = '/dev/ttyACM0'  
BAUD_RATE = 9600

def main():
    # Initialize Camera and Serial Connection
    cam = CSICamera(device_id=0, width=640, height=480)
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for serial connection to establish
        print(f"Connected to motor controller on {SERIAL_PORT}")
    except Exception as e:
        print(f"Serial connection skipped/failed: {e}")
        ser = None

    # Using OpenCV Haar Cascade for quick face detection demo
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    print("Starting tracking loop. Press 'q' to exit.")
    while True:
        frame = cam.get_frame()
        if frame is None:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) > 0:
            # Take the largest face found
            x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
            face_box = (x, y, x + w, y + h)

            # Calculate Vertical Error
            v_error, center_y = calculate_vertical_error(frame, face_box)

            # Draw visual indicators
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.line(frame, (0, int(frame.shape[0]/2)), (frame.shape[1], int(frame.shape[0]/2)), (255, 0, 0), 1)

            # Send error to Microcontroller over Serial
            if ser and ser.is_open:
                ser.write(f"{int(v_error)}\n".encode('utf-8'))

        cv2.imshow("Vertical Tracking - D4S01ASUNNYN1611", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    if ser:
        ser.close()

if __name__ == "__main__":
    main()