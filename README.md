# 5-Point Landmark Face Recognition & Tracking System

High-accuracy face recognition and tracking system using 5-point facial landmark alignment (Haar cascades / MediaPipe), ArcFace 512-D ONNX embeddings, and closed-loop servo tracking via ESP8266.

## Setup and Run Order

Run these commands from the project root in PowerShell:

```powershell
& .\.venv-1\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.camera --list-cams
```

Test the camera before face recognition:

```powershell
python -m src.camera --cam 1
```

Press `Q` to close the live view. The camera index may differ on another computer; use the index marked `[SELECTED PHYSICAL]` by `--list-cams`.

Enroll one person. Keep the face well lit and move slightly between samples:

```powershell
python -m src.enroll --name "Larissa Prisca" --cam 1 --samples 15
```

Start recognition and tracking without hardware first:

```powershell
python -m src.track_target --target "Larissa Prisca" --cam 1
```

Face lock controls:

- Press `L` while the recognized target is visible to lock that face.
- Press `U` to unlock and return to automatic target selection.
- Press `SPACE` to pause/resume servo tracking.
- Press `Q` to exit.

The lock uses the last selected face position to keep the servo from switching to another matching face. It remains armed during brief occlusion and reacquires the nearest recognized face when it returns.

Expression messages:

- When the recognized face closes their eyes or blinks, the window shows `Message: BLINK / EYES CLOSED`.
- When the recognized face smiles, the window shows `Message: SMILE`.
- Messages also print in the terminal and are debounced to avoid repeated spam.

After the on-screen recognition is correct, connect the ESP8266 and run either:

```powershell
python -m src.test_servo --port COM13
python -m src.track_target --target "Larissa Prisca" --cam 1 --port COM13
```

Replace `COM13` with the COM port shown in Windows Device Manager. The ESP8266 firmware must be uploaded first, with the servo signal on `D1`, a separate 5 V servo supply, and a shared ground.

Required hardware:

- Windows PC with Python 3.11 and a working webcam. Use `python -m src.camera --list-cams` to find the camera index.
- ESP8266 NodeMCU or D1 Mini, when servo movement is required.
- SG90 or compatible servo. Connect signal to `D1/GPIO5`, red to a stable 5 V supply, and brown/black to GND.
- Common ground between the ESP8266 and the servo supply.
- USB cable from the ESP8266 to the PC. Upload `firmware/esp8266_servo/esp8266_servo.ino` with Arduino IDE, then use the detected COM port.

If camera enumeration works but opening a camera fails, close Teams, Zoom, OBS, Camera, and other programs using the webcam, then check Windows Settings > Privacy & security > Camera and enable desktop-app camera access. The camera utility also tries an FFmpeg DirectShow fallback by device name and will use the integrated camera if the selected external camera does not produce frames. Reconnect the USB camera and repeat `python -m src.camera --list-cams`.

## Camera Configuration

The system automatically detects and prioritizes **physical external USB cameras** (e.g. `Wed Camera`) over the PC's built-in laptop camera (`Integrated Camera`) and virtual cameras (`EShare Virtual Camera`).

### List Connected Cameras
To see all connected cameras and which device is selected:
```bash
python -m src.camera --list-cams
```

Output:
```text
=================================================================
INDEX   | TYPE                 | DEVICE NAME
=================================================================
  0     | Internal PC Camera   | Integrated Camera
  1     | Virtual Camera       | EShare Virtual Camera
  2     | Physical External    | Wed Camera -> [SELECTED PHYSICAL]
=================================================================
```

### Automatic Physical Camera Usage
All entry points automatically select the physical camera by default (`--cam auto`):
- **Camera Test / Live HUD**: `python -m src.camera`
- **Face Detection**: `python -m src.detect`
- **Target Face Enrollment**: `python -m src.enroll --name TargetName`
- **Target Tracking & Servo Base**: `python -m src.track_target --target TargetName --port COM13`

### Manual Camera Override
If you want to manually specify a camera index or network stream:
```bash
# Explicit camera index (e.g. 2)
python -m src.track_target --target TargetName --cam 2

# IP / RTSP / HTTP Camera Stream
python -m src.track_target --target TargetName --cam http://192.168.1.100:8080/video
```
