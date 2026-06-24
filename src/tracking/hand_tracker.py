import os
import time

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions


class HandTracker:
    """MediaPipe HandLandmarker task wrapper for live video."""

    def __init__(self, max_hands=1, process_size=(640, 480)):
        model_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "models", "hand_landmarker.task")
        )
        base_options = BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=0.45,
            min_hand_presence_confidence=0.45,
            min_tracking_confidence=0.45,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.process_size = process_size

    def process(self, frame):
        small = cv2.resize(frame, self.process_size, interpolation=cv2.INTER_LINEAR)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(time.time() * 1000)
        result = self.detector.detect_for_video(mp_image, timestamp_ms)
        if result.hand_landmarks:
            return result.hand_landmarks[0]
        return None

    def close(self):
        self.detector.close()
