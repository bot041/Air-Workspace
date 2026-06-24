# AirScript Architecture

## Pipeline

Camera -> Hand Tracker -> Gesture Detector -> State Machine -> Object Manager -> Renderer -> Workspace / Output Tray

## Modules

- `camera.webcam` – OpenCV webcam capture.
- `tracking.hand_tracker` – MediaPipe Hands wrapper.
- `tracking.gesture_detector` – Classifies index-only, two-finger, pinch, and palm gestures.
- `drawing.stroke` / `smoother` – Stroke storage and smoothing.
- `objects.stroke_object` / `object_manager` – Object model and workspace/tray collections.
- `selection.selection_manager` – Selected object and drag offset.
- `eraser.eraser` – Partial stroke erasure and full object deletion.
- `panels.workspace` / `output_tray` – PyQt6 UI panels.
- `ui.theme` – Simple Ink and Neon AR renderers.
- `core.state_machine` / `app_controller` – Application state and update loop.
