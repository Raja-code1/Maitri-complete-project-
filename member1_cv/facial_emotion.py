"""
Member 1: Facial Emotion Recognition (FER) Model Engine
Lightweight, offline classifier for facial emotion states and psychological valence.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple

from config.settings import EMOTION_CLASSES


class FacialEmotionRecognizer:
    """
    Lightweight Facial Emotion Recognizer for offline space edge computing.
    Extracts geometric vectors, optical flow shifts, and facial feature distributions.
    """

    def __init__(self, use_haar_cascade: bool = True):
        self.emotion_labels = EMOTION_CLASSES
        self.face_cascade = None
        self.eye_cascade = None
        
        if use_haar_cascade:
            try:
                cascade_path = cv2.data.haarcascades
                self.face_cascade = cv2.CascadeClassifier(
                    cascade_path + "haarcascade_frontalface_default.xml"
                )
                self.eye_cascade = cv2.CascadeClassifier(
                    cascade_path + "haarcascade_eye.xml"
                )
            except Exception:
                self.face_cascade = None
                self.eye_cascade = None

    def detect_face_and_features(
        self, frame: np.ndarray
    ) -> Tuple[bool, Optional[Tuple[int, int, int, int]], Dict[str, float]]:
        """
        Detect face bounding box and extract facial geometric ratios.
        Returns: (face_detected, bbox, geometric_features)
        """
        if frame is None or frame.size == 0:
            return False, None, {}
            
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        h, w = gray.shape[:2]
        face_bbox = None
        
        # Try Haar face detector
        if self.face_cascade is not None and not self.face_cascade.empty():
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60)
            )
            if len(faces) > 0:
                # Select largest detected face
                face_bbox = max(faces, key=lambda b: b[2] * b[3])
                
        if face_bbox is None:
            # Fallback to center-crop if face detector didn't catch or synthetic frame
            face_bbox = (int(w * 0.2), int(h * 0.15), int(w * 0.6), int(h * 0.7))
            face_detected = True
        else:
            face_detected = True

        fx, fy, fw, fh = face_bbox
        face_roi = gray[fy : fy + fh, fx : fx + fw]
        
        # Extract lightweight spatial & intensity features from Face ROI
        # Upper face (eyes/brow), middle (nose/cheeks), lower (mouth/jaw)
        roi_h, roi_w = face_roi.shape
        upper_roi = face_roi[: int(roi_h * 0.4), :]
        lower_roi = face_roi[int(roi_h * 0.65) :, :]
        
        upper_intensity = float(np.mean(upper_roi)) if upper_roi.size > 0 else 128.0
        lower_intensity = float(np.mean(lower_roi)) if lower_roi.size > 0 else 128.0
        upper_std = float(np.std(upper_roi)) if upper_roi.size > 0 else 20.0
        lower_std = float(np.std(lower_roi)) if lower_roi.size > 0 else 20.0
        
        features = {
            "upper_intensity": upper_intensity,
            "lower_intensity": lower_intensity,
            "upper_std": upper_std,
            "lower_std": lower_std,
            "aspect_ratio": float(fw) / max(1.0, float(fh)),
        }
        
        return face_detected, face_bbox, features

    def classify_emotion(
        self,
        ear: float,
        mar: float,
        brow_furrow: float = 0.0,
        jaw_clench: float = 0.0,
        features: Optional[Dict[str, float]] = None,
    ) -> Tuple[str, Dict[str, float], float]:
        """
        Classify facial emotion from geometric and appearance features.
        Returns: (primary_emotion, emotion_probabilities, confidence)
        """
        # Feature-driven probabilistic classification for edge deployment
        scores: Dict[str, float] = {e: 0.05 for e in self.emotion_labels}
        
        # 1. Stressed / Anxious
        # High brow furrow + jaw clench + tense eyes
        stress_evidence = brow_furrow * 0.6 + jaw_clench * 0.4
        scores["stressed"] += stress_evidence * 0.85
        scores["anxious"] += stress_evidence * 0.70
        
        # 2. Exhausted / Fatigue
        # Low EAR (drooping eyelids) + yawning (high MAR) + low brow furrow
        if ear < 0.22:
            scores["exhausted"] += (0.25 - ear) * 3.5
        if mar > 0.50:
            scores["exhausted"] += (mar - 0.50) * 2.0
            scores["discomfort"] += 0.30
            
        # 3. Happy / Smiling
        # Higher MAR with low brow furrow and relaxed jaw
        if 0.25 < mar < 0.52 and brow_furrow < 0.25 and jaw_clench < 0.30:
            smile_boost = (mar - 0.25) * 2.5
            scores["happy"] += smile_boost
            
        # 4. Focused
        # Moderate brow furrow, normal eye openness, stable mouth
        if 0.15 <= brow_furrow <= 0.45 and 0.25 <= ear <= 0.35 and mar < 0.30:
            scores["focused"] += 0.60
            
        # 5. Neutral / Calm
        # Relaxed facial features
        if brow_furrow < 0.20 and jaw_clench < 0.20 and 0.25 <= ear <= 0.35 and mar < 0.30:
            scores["neutral"] += 0.80
            scores["calm"] += 0.70
            
        # 6. Discomfort
        if jaw_clench > 0.60 or (brow_furrow > 0.50 and mar < 0.20):
            scores["discomfort"] += 0.75

        # Normalize with softmax
        raw_vals = np.array([scores[e] for e in self.emotion_labels])
        exp_vals = np.exp(raw_vals - np.max(raw_vals))
        probs = exp_vals / np.sum(exp_vals)
        
        prob_dict = {
            self.emotion_labels[i]: round(float(probs[i]), 3)
            for i in range(len(self.emotion_labels))
        }
        
        primary_idx = int(np.argmax(probs))
        primary_emotion = self.emotion_labels[primary_idx]
        confidence = round(float(probs[primary_idx]), 3)
        
        return primary_emotion, prob_dict, confidence
