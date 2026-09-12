def detect_vertical_movement(kps):
    """
    Detect whether the head is looking up, down, or center.
    kps order:
    left_eye, right_eye, nose, mouth_left, mouth_right
    """

    left_eye = kps[0]
    right_eye = kps[1]
    nose = kps[2]
    mouth_left = kps[3]
    mouth_right = kps[4]

    # Average eye and mouth positions
    eye_y = (left_eye[1] + right_eye[1]) / 2
    mouth_y = (mouth_left[1] + mouth_right[1]) / 2

    # Vertical position of nose between eyes and mouth
    face_height = mouth_y - eye_y

    if face_height <= 0:
        return "CENTER"

    nose_ratio = (nose[1] - eye_y) / face_height

    if nose_ratio < 0.38:
        return "LOOKING UP"

    elif nose_ratio > 0.62:
        return "LOOKING DOWN"

    else:
        return "CENTER"