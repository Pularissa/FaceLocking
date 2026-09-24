# src/haar_5pt.py
"""
Face Detection + 5-Point Landmarks + Similarity Transform Alignment
Supports MediaPipe and OpenCV fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional
import cv2
import numpy as np

# Canonical ArcFace 112x112 reference landmark positions
ARCFACE_REF_5PTS = np.array(
    [
        [38.2946, 51.6963],  # Left Eye
        [73.5318, 51.5014],  # Right Eye
        [56.0252, 71.7366],  # Nose Tip
        [41.5493, 92.3655],  # Left Mouth Corner
        [70.7266, 92.2041],  # Right Mouth Corner
    ],
    dtype=np.float32,
)

# FaceMesh 5-point indices
IDX_LEFT_EYE = 33
IDX_RIGHT_EYE = 263
IDX_NOSE_TIP = 1
IDX_MOUTH_LEFT = 61
IDX_MOUTH_RIGHT = 291


@dataclass
class FaceBox5pt:
    x1: int
    y1: int
    x2: int
    y2: int
    kps: np.ndarray  # (5, 2) float32: [left_eye, right_eye, nose, mouth_left, mouth_right]
    expression: str = ""


def _distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def _eye_aspect_ratio(points: np.ndarray) -> float:
    return (_distance(points[1], points[5]) + _distance(points[2], points[4])) / max(
        2.0 * _distance(points[0], points[3]), 1e-6
    )


def _expression_from_landmarks(landmarks, face_width: float) -> str:
    left_eye = np.array(
        [[landmarks[i].x, landmarks[i].y] for i in [33, 160, 158, 133, 153, 144]],
        dtype=np.float32,
    )
    right_eye = np.array(
        [[landmarks[i].x, landmarks[i].y] for i in [263, 387, 385, 362, 380, 373]],
        dtype=np.float32,
    )
    eye_ratio = (_eye_aspect_ratio(left_eye) + _eye_aspect_ratio(right_eye)) / 2.0

    left_corner = np.array([landmarks[61].x, landmarks[61].y], dtype=np.float32)
    right_corner = np.array([landmarks[291].x, landmarks[291].y], dtype=np.float32)
    upper_lip = np.array([landmarks[13].x, landmarks[13].y], dtype=np.float32)
    lower_lip = np.array([landmarks[14].x, landmarks[14].y], dtype=np.float32)
    mouth_width = _distance(left_corner, right_corner)
    mouth_center_y = (upper_lip[1] + lower_lip[1]) / 2.0
    corner_lift = mouth_center_y - (left_corner[1] + right_corner[1]) / 2.0
    smile_width = mouth_width / max(face_width, 1e-6)
    smile_lift = corner_lift / max(face_width, 1e-6)

    if eye_ratio < 0.20:
        return "BLINK / EYES CLOSED"
    if smile_width > 0.36 or smile_lift > 0.006:
        return "SMILE"
    return ""


def align_face_5pt(
    img: np.ndarray,
    kps: np.ndarray,
    out_size: Tuple[int, int] = (112, 112),
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Computes similarity transform (rotation + scale + translation)
    to warp detected 5 keypoints onto canonical ArcFace coordinates.
    """
    if kps is None or len(kps) != 5:
        return None, None

    src_pts = np.asarray(kps, dtype=np.float32)
    dst_pts = ARCFACE_REF_5PTS.copy()

    if out_size != (112, 112):
        scale_x = out_size[0] / 112.0
        scale_y = out_size[1] / 112.0
        dst_pts[:, 0] *= scale_x
        dst_pts[:, 1] *= scale_y

    M, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.LMEDS)
    if M is None:
        return None, None

    warped = cv2.warpAffine(
        img,
        M,
        (int(out_size[0]), int(out_size[1])),
        borderValue=0.0,
        flags=cv2.INTER_LINEAR,
    )
    return warped, M


class Haar5ptDetector:
    """
    Multi-engine 5-point face detector.
    Works with MediaPipe FaceMesh or OpenCV.
    """

    def __init__(
        self,
        min_size: Tuple[int, int] = (60, 60),
        smooth_alpha: float = 0.80,
        debug: bool = False,
    ):
        self.min_size = min_size
        self.smooth_alpha = smooth_alpha
        self.debug = debug
        self.backend = None

        # Try MediaPipe FaceMesh
        try:
            import mediapipe as mp
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh"):
                self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=5,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                self.backend = "mp_solutions"
        except Exception as e:
            if debug:
                print(f"[Haar5ptDetector] MediaPipe init notice: {e}")

        # Try OpenCV Cascade if MediaPipe was not initialized
        if self.backend is None:
            try:
                if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
                    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                    cascade = cv2.CascadeClassifier(cascade_path)
                    if not cascade.empty():
                        self.face_cascade = cascade
                        self.backend = "haar_fallback"
            except Exception:
                pass

        if self.backend is None:
            self.backend = "center_crop_fallback"

    def detect(self, frame: np.ndarray, max_faces: int = 5) -> List[FaceBox5pt]:
        H, W = frame.shape[:2]
        detected_faces = []

        if self.backend == "mp_solutions":
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mesh_results = self.face_mesh.process(rgb)

            if mesh_results.multi_face_landmarks:
                for face_landmarks in mesh_results.multi_face_landmarks[:max_faces]:
                    lm = face_landmarks.landmark
                    idxs = [
                        IDX_LEFT_EYE,
                        IDX_RIGHT_EYE,
                        IDX_NOSE_TIP,
                        IDX_MOUTH_LEFT,
                        IDX_MOUTH_RIGHT,
                    ]
                    pts = [[lm[i].x * W, lm[i].y * H] for i in idxs]
                    kps = np.array(pts, dtype=np.float32)

                    if kps[0, 0] > kps[1, 0]:
                        kps[[0, 1]] = kps[[1, 0]]
                    if kps[3, 0] > kps[4, 0]:
                        kps[[3, 4]] = kps[[4, 3]]

                    min_x, min_y = np.min(kps, axis=0)
                    max_x, max_y = np.max(kps, axis=0)
                    bw = max_x - min_x
                    bh = max_y - min_y
                    margin_x = bw * 0.45
                    margin_y = bh * 0.55

                    x1 = int(max(0, min_x - margin_x))
                    y1 = int(max(0, min_y - margin_y))
                    x2 = int(min(W, max_x + margin_x))
                    y2 = int(min(H, max_y + margin_y))

                    expression = _expression_from_landmarks(lm, max_x - min_x)
                    detected_faces.append(FaceBox5pt(x1, y1, x2, y2, kps, expression))
                return detected_faces

        elif self.backend == "haar_fallback" and hasattr(self, "face_cascade"):
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            haar_faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=self.min_size,
            )

            for (x, y, w, h) in haar_faces[:max_faces]:
                kps = np.array(
                    [
                        [x + 0.30 * w, y + 0.37 * h],
                        [x + 0.70 * w, y + 0.37 * h],
                        [x + 0.50 * w, y + 0.58 * h],
                        [x + 0.35 * w, y + 0.78 * h],
                        [x + 0.65 * w, y + 0.78 * h],
                    ],
                    dtype=np.float32,
                )
                detected_faces.append(FaceBox5pt(x, y, x + w, y + h, kps))

        return detected_faces
