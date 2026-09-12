import cv2

class CSICamera:
    def __init__(self, device_id=0, width=640, height=480):
        # Open camera using V4L2 backend for CSI module
        self.cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open D4S01ASUNNYN1611 camera on /dev/video{device_id}")

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        self.cap.release()