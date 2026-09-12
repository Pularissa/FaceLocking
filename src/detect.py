import cv2

def calculate_vertical_error(frame, face_box):
    """
    Calculates vertical distance from frame center to face center.
    Returns:
        v_error (float): Distance in pixels (+ value = face is BELOW center, - value = face is ABOVE center)
        center_y (float): The face center Y coordinate
    """
    frame_h = frame.shape[0]
    frame_center_y = frame_h / 2.0
    
    # Extract coordinates [x1, y1, x2, y2]
    _, y1, _, y2 = face_box
    face_center_y = (y1 + y2) / 2.0
    
    v_error = face_center_y - frame_center_y
    return v_error, face_center_y