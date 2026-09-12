import argparse
import cv2
import mediapipe as mp

from .camera import open_camera, print_camera_list


def main():
    parser = argparse.ArgumentParser(description="MediaPipe Face Detection")
    parser.add_argument("--cam", default="auto", help="Camera index or 'auto' for physical external camera")
    parser.add_argument("--list-cams", action="store_true", help="List detected cameras and exit")
    args = parser.parse_args()

    if args.list_cams:
        print_camera_list()
        return

    # Initialize MediaPipe Face Detection
    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils

    face_detection = mp_face_detection.FaceDetection(
        model_selection=0,
        min_detection_confidence=0.5
    )

    # Open physical camera by default
    camera = open_camera(args.cam)

    print("Face detection started.")
    print("Press Q to quit.")

    while True:
        success, frame = camera.read()

        if not success or frame is None:
            print("ERROR: Could not read frame.")
            break

        # OpenCV uses BGR; MediaPipe expects RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        results = face_detection.process(rgb_frame)

        # Draw detection boxes
        if results.detections:
            for detection in results.detections:
                mp_drawing.draw_detection(frame, detection)

        # Display result
        cv2.imshow("Face Detection", frame)

        # Press Q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    face_detection.close()
    cv2.destroyAllWindows()

    print("Face detection stopped.")


if __name__ == "__main__":
    main()