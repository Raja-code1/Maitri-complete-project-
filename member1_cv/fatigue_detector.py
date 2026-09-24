"""
Member 1: Fatigue & Physical Discomfort Detector
Calculates Eye Aspect Ratio (EAR), PERCLOS, Blink Rate, Mouth Aspect Ratio (MAR) Yawn Detection, and Head Droop.
"""

import time
import math
from collections import deque
from typing import Dict, List, Optional, Tuple
import numpy as np

from config.settings import (
    EAR_EYE_CLOSED_THRESHOLD,
    EAR_DROWSY_THRESHOLD,
    MAR_YAWN_THRESHOLD,
    PERCLOS_ALERT_THRESHOLD,
    BLINK_RATE_LOW_THRESHOLD,
    BLINK_RATE_HIGH_THRESHOLD,
    HEAD_DROOP_ANGLE_THRESHOLD,
)
from config.schemas import VisualFatigueData


class FatigueDetector:
    """
    Real-time fatigue, PERCLOS, blink rate, and yawn analysis engine.
    Designed for zero-latency offline edge inference.
    """

    def __init__(self, window_size: int = 150):
        """
        Args:
            window_size: Number of frames in rolling buffer (~5-10s at 15-30fps) for PERCLOS.
        """
        self.window_size = window_size
        self.ear_history: deque = deque(maxlen=window_size)
        self.closed_eye_history: deque = deque(maxlen=window_size)
        self.blink_timestamps: deque = deque(maxlen=60)  # blinks in last 60s
        
        self.eye_closed_streak: int = 0
        self.is_eye_currently_closed: bool = False
        self.yawn_streak: int = 0
        self.total_blinks: int = 0
        self.last_blink_time: float = time.time()

    def compute_ear(self, eye_landmarks: Optional[np.ndarray] = None) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) from eye landmark points.
        If landmarks are provided as (6, 2) array:
        EAR = (|p2 - p6| + |p3 - p5|) / (2 * |p1 - p4|)
        """
        if eye_landmarks is None or len(eye_landmarks) < 6:
            return 0.30  # Default nominal open eye
        
        # Vertical distances
        d_v1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        d_v2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        # Horizontal distance
        d_h = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        
        if d_h < 1e-5:
            return 0.30
        
        ear = (d_v1 + d_v2) / (2.0 * d_h)
        return float(ear)

    def compute_mar(self, mouth_landmarks: Optional[np.ndarray] = None) -> float:
        """
        Calculate Mouth Aspect Ratio (MAR) for yawn detection.
        MAR = (|m2 - m8| + |m3 - m7| + |m4 - m6|) / (2 * |m1 - m5|)
        """
        if mouth_landmarks is None or len(mouth_landmarks) < 8:
            return 0.15  # Default closed/relaxed mouth
        
        d_v1 = np.linalg.norm(mouth_landmarks[1] - mouth_landmarks[7])
        d_v2 = np.linalg.norm(mouth_landmarks[2] - mouth_landmarks[6])
        d_v3 = np.linalg.norm(mouth_landmarks[3] - mouth_landmarks[5])
        d_h = np.linalg.norm(mouth_landmarks[0] - mouth_landmarks[4])
        
        if d_h < 1e-5:
            return 0.15
        
        mar = (d_v1 + d_v2 + d_v3) / (2.0 * d_h)
        return float(mar)

    def update_frame(
        self,
        ear_value: float,
        mar_value: float,
        head_pitch: float = 0.0,
        head_roll: float = 0.0,
        current_time: Optional[float] = None,
    ) -> VisualFatigueData:
        """
        Process a single video frame's geometric metrics and return comprehensive fatigue state.
        """
        now = current_time if current_time is not None else time.time()
        
        # Track EAR and closure state
        is_closed = ear_value < EAR_EYE_CLOSED_THRESHOLD
        self.ear_history.append(ear_value)
        self.closed_eye_history.append(1 if is_closed else 0)
        
        # Blink detection logic (transition from closed to open or closed threshold streak)
        if is_closed:
            self.eye_closed_streak += 1
            if not self.is_eye_currently_closed and self.eye_closed_streak >= 1:
                self.is_eye_currently_closed = True
        else:
            if self.is_eye_currently_closed and self.eye_closed_streak <= 15:
                # Valid blink (duration between 50ms and 500ms)
                self.total_blinks += 1
                self.blink_timestamps.append(now)
                self.last_blink_time = now
            self.is_eye_currently_closed = False
            self.eye_closed_streak = 0
            
        # Clean older blink timestamps beyond 60 seconds
        while self.blink_timestamps and (now - self.blink_timestamps[0]) > 60.0:
            self.blink_timestamps.popleft()
            
        blink_rate_bpm = float(len(self.blink_timestamps))
        
        # Compute PERCLOS (% of time eye is closed in rolling window)
        if len(self.closed_eye_history) > 0:
            perclos = sum(self.closed_eye_history) / len(self.closed_eye_history)
        else:
            perclos = 0.0
            
        # Yawn detection
        is_yawning = mar_value > MAR_YAWN_THRESHOLD
        if is_yawning:
            self.yawn_streak += 1
        else:
            self.yawn_streak = 0
            
        # Drowsiness detection: PERCLOS alert, prolonged eye closure, or high yawning
        is_drowsy = (
            perclos >= PERCLOS_ALERT_THRESHOLD
            or self.eye_closed_streak > 20  # eye closed for > 0.8s
            or (ear_value < EAR_DROWSY_THRESHOLD and self.yawn_streak > 15)
        )
        
        # Posture stability evaluation
        if abs(head_pitch) > HEAD_DROOP_ANGLE_THRESHOLD:
            posture_stability = "slumped"
        elif abs(head_roll) > 25.0:
            posture_stability = "unsteady"
        else:
            posture_stability = "stable"
            
        return VisualFatigueData(
            ear=round(ear_value, 3),
            mar=round(mar_value, 3),
            perclos=round(perclos, 3),
            blink_rate_bpm=round(blink_rate_bpm, 1),
            is_yawning=bool(is_yawning),
            is_drowsy=bool(is_drowsy),
            head_pitch_deg=round(head_pitch, 1),
            head_roll_deg=round(head_roll, 1),
            posture_stability=posture_stability,
        )

    def calculate_continuous_fatigue_score(self, fatigue_data: VisualFatigueData) -> float:
        """
        Derive continuous physical fatigue score (0.0 = completely fresh, 100.0 = severe exhaustion).
        """
        score = 0.0
        
        # PERCLOS contributes up to 45 points
        # If PERCLOS is 0.20 (20%), score += 45 * min(1.0, 0.20 / 0.25)
        score += min(45.0, (fatigue_data.perclos / PERCLOS_ALERT_THRESHOLD) * 35.0)
        
        # Yawn contributes up to 25 points
        if fatigue_data.is_yawning:
            score += 25.0
        elif fatigue_data.mar > 0.40:
            score += (fatigue_data.mar - 0.40) * 40.0
            
        # Blink rate anomaly contributes up to 15 points
        if fatigue_data.blink_rate_bpm > BLINK_RATE_HIGH_THRESHOLD:
            # High ocular strain
            score += min(15.0, (fatigue_data.blink_rate_bpm - BLINK_RATE_HIGH_THRESHOLD) * 1.5)
        elif fatigue_data.blink_rate_bpm < BLINK_RATE_LOW_THRESHOLD and fatigue_data.blink_rate_bpm > 0:
            # Staring / cognitive freezing
            score += min(15.0, (BLINK_RATE_LOW_THRESHOLD - fatigue_data.blink_rate_bpm) * 2.0)
            
        # Slumped posture contributes 15 points
        if fatigue_data.posture_stability == "slumped":
            score += 15.0
        elif fatigue_data.posture_stability == "unsteady":
            score += 8.0
            
        return round(float(np.clip(score, 0.0, 100.0)), 1)
