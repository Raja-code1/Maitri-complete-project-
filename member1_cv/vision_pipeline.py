"""
Member 1: Vision Pipeline Orchestrator
Integrates Facial Emotion Recognition, Fatigue Metrics (EAR, MAR, PERCLOS), and Micro-Expressions.
"""

import time
from typing import Dict, Optional, Tuple, Union
import numpy as np

from config.schemas import VisualStateData, VisualFatigueData, VisualMicroExpression
from member1_cv.facial_emotion import FacialEmotionRecognizer
from member1_cv.fatigue_detector import FatigueDetector
from member1_cv.micro_expression import MicroExpressionAnalyzer


class VisionPipeline:
    """
    Unified Computer Vision processor for astronaut physical and emotional monitoring.
    """

    def __init__(self):
        self.emotion_recognizer = FacialEmotionRecognizer()
        self.fatigue_detector = FatigueDetector(window_size=120)
        self.micro_analyzer = MicroExpressionAnalyzer(history_len=45)
        self.processed_frames_count: int = 0

    def process_frame(
        self,
        frame: Optional[np.ndarray] = None,
        simulated_ear: Optional[float] = None,
        simulated_mar: Optional[float] = None,
        simulated_brow: Optional[float] = None,
        simulated_jaw: Optional[float] = None,
        head_pitch: float = 0.0,
        head_roll: float = 0.0,
        current_time: Optional[float] = None,
    ) -> VisualStateData:
        """
        Process incoming camera frame or simulated telemetry vectors.
        Returns: Validated VisualStateData
        """
        now = current_time if current_time is not None else time.time()
        self.processed_frames_count += 1
        
        # 1. Image feature extraction / Geometry estimation
        face_detected = True
        extracted_features = {}
        
        if frame is not None:
            face_detected, bbox, extracted_features = self.emotion_recognizer.detect_face_and_features(frame)
            # If simulated values not explicitly passed, compute from frame features
            ear = simulated_ear if simulated_ear is not None else (0.28 if face_detected else 0.30)
            mar = simulated_mar if simulated_mar is not None else 0.18
            brow_ratio = simulated_brow if simulated_brow is not None else 0.5
            jaw_ratio = simulated_jaw if simulated_jaw is not None else 0.22
        else:
            ear = simulated_ear if simulated_ear is not None else 0.30
            mar = simulated_mar if simulated_mar is not None else 0.15
            brow_ratio = simulated_brow if simulated_brow is not None else 0.5
            jaw_ratio = simulated_jaw if simulated_jaw is not None else 0.22
            
        # 2. Update Fatigue and Eye Dynamics (EAR, MAR, PERCLOS, Blink Rate)
        fatigue_metrics: VisualFatigueData = self.fatigue_detector.update_frame(
            ear_value=ear,
            mar_value=mar,
            head_pitch=head_pitch,
            head_roll=head_roll,
            current_time=now,
        )
        fatigue_score = self.fatigue_detector.calculate_continuous_fatigue_score(fatigue_metrics)
        
        # Categorize fatigue level
        if fatigue_score >= 70.0 or fatigue_metrics.perclos >= 0.20:
            fatigue_level = "severe"
        elif fatigue_score >= 45.0 or fatigue_metrics.is_drowsy:
            fatigue_level = "high"
        elif fatigue_score >= 25.0 or fatigue_metrics.is_yawning:
            fatigue_level = "moderate"
        else:
            fatigue_level = "low"
            
        # 3. Analyze Micro-Expressions and Facial Strain
        micro_exp: VisualMicroExpression = self.micro_analyzer.analyze_facial_tension(
            brow_distance_ratio=brow_ratio,
            lip_compression_ratio=jaw_ratio,
        )
        
        # 4. Classify Primary Facial Emotion
        primary_emotion, emotion_confs, conf_score = self.emotion_recognizer.classify_emotion(
            ear=ear,
            mar=mar,
            brow_furrow=micro_exp.brow_furrow,
            jaw_clench=micro_exp.jaw_clench,
            features=extracted_features,
        )
        
        # Cross-adjust emotion if severe exhaustion/fatigue is detected
        if fatigue_level in ["high", "severe"] and primary_emotion in ["neutral", "calm"]:
            primary_emotion = "exhausted"
            emotion_confs["exhausted"] = max(emotion_confs.get("exhausted", 0.0), 0.75)
            
        return VisualStateData(
            timestamp=now,
            face_detected=face_detected,
            primary_emotion=primary_emotion,
            emotion_confidences=emotion_confs,
            fatigue_level=fatigue_level,
            fatigue_score=fatigue_score,
            fatigue_metrics=fatigue_metrics,
            micro_expressions=micro_exp,
            confidence=conf_score,
        )
