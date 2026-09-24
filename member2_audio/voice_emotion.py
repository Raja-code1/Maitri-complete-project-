"""
Member 2: Voice Emotion Recognition (SER)
Classifies vocal emotion, dimensional Valence/Arousal, and vocal strain from acoustic features.
"""

from typing import Dict, List, Tuple
import numpy as np

from config.settings import (
    JITTER_ALERT_THRESHOLD,
    SHIMMER_ALERT_THRESHOLD,
    PITCH_MIN_HZ,
    PITCH_MAX_HZ,
)
from config.schemas import AcousticFeatures


class VoiceEmotionRecognizer:
    """
    Speech Emotion Recognition (SER) classifier optimized for edge inference.
    """

    VOICE_EMOTIONS = ["calm", "focused", "stressed", "anxious", "fatigued", "panicked", "neutral"]

    def __init__(self):
        # Baseline reference for astronaut voice (calm nominal state)
        self.baseline_pitch_hz = 135.0
        self.baseline_jitter = 0.012
        self.baseline_shimmer = 0.030

    def compute_vocal_strain(self, features: AcousticFeatures) -> float:
        """
        Calculate continuous vocal strain score (0.0 = calm/relaxed, 100.0 = severe vocal constriction/stress).
        """
        strain = 0.0
        
        # High jitter (vocal fold perturbation from autonomic sympathetic surge)
        if features.jitter_local > self.baseline_jitter:
            jitter_excess = (features.jitter_local - self.baseline_jitter) / JITTER_ALERT_THRESHOLD
            strain += min(35.0, jitter_excess * 30.0)
            
        # High shimmer (amplitude instability)
        if features.shimmer_local > self.baseline_shimmer:
            shimmer_excess = (features.shimmer_local - self.baseline_shimmer) / SHIMMER_ALERT_THRESHOLD
            strain += min(25.0, shimmer_excess * 20.0)
            
        # Elevated pitch above baseline
        if features.f0_pitch_hz > self.baseline_pitch_hz + 25.0:
            pitch_excess = (features.f0_pitch_hz - (self.baseline_pitch_hz + 25.0)) / 100.0
            strain += min(25.0, pitch_excess * 25.0)
            
        # Low HNR (breathiness / roughness)
        if features.hnr_db < 12.0:
            strain += min(15.0, (12.0 - features.hnr_db) * 1.5)
            
        return round(float(np.clip(strain, 0.0, 100.0)), 1)

    def classify_voice_emotion(
        self, features: AcousticFeatures, word_count: int = 10, duration_sec: float = 3.0
    ) -> Tuple[str, Dict[str, float], float, float, float]:
        """
        Classify voice emotion and dimensional valence/arousal.
        Returns: (primary_emotion, probabilities, valence, arousal, vocal_strain)
        """
        vocal_strain = self.compute_vocal_strain(features)
        
        # Arousal (0.0 calm to 1.0 hyperaroused/excited)
        # Driven by pitch height, spectral centroid brightness, and RMS energy
        arousal_pitch = (features.f0_pitch_hz - 80.0) / 300.0
        arousal_centroid = (features.spectral_centroid_hz - 1000.0) / 3000.0
        arousal = float(np.clip(0.5 * arousal_pitch + 0.5 * arousal_centroid, 0.0, 1.0))
        
        # Valence (-1.0 negative distress to +1.0 positive satisfaction)
        # Low jitter/shimmer and high HNR correlate with positive/balanced valence
        negativity_strain = vocal_strain / 100.0
        valence = float(np.clip(0.5 - (negativity_strain * 1.2), -1.0, 1.0))
        
        # Calculate emotion score vector
        scores: Dict[str, float] = {e: 0.05 for e in self.VOICE_EMOTIONS}
        
        if vocal_strain >= 70.0 or (features.f0_pitch_hz > 240.0 and features.jitter_local > 0.04):
            scores["panicked"] += 0.80
            scores["stressed"] += 0.60
        elif vocal_strain >= 40.0 or features.jitter_local > 0.025:
            scores["stressed"] += 0.70
            scores["anxious"] += 0.65
        elif features.f0_pitch_hz < 110.0 and features.shimmer_local > 0.045 and features.hnr_db < 13.0:
            scores["fatigued"] += 0.85
        elif 0.3 <= arousal <= 0.65 and vocal_strain < 25.0:
            scores["focused"] += 0.75
            scores["calm"] += 0.60
        else:
            scores["neutral"] += 0.65
            scores["calm"] += 0.70

        # Softmax normalization
        raw_vals = np.array([scores[e] for e in self.VOICE_EMOTIONS])
        exp_vals = np.exp(raw_vals - np.max(raw_vals))
        probs = exp_vals / np.sum(exp_vals)
        
        prob_dict = {
            self.VOICE_EMOTIONS[i]: round(float(probs[i]), 3)
            for i in range(len(self.VOICE_EMOTIONS))
        }
        
        primary_idx = int(np.argmax(probs))
        primary_emotion = self.VOICE_EMOTIONS[primary_idx]
        
        # Estimate Speech Rate (Words Per Minute)
        if duration_sec > 0.1:
            speech_rate_wpm = round(float((word_count / duration_sec) * 60.0), 1)
        else:
            speech_rate_wpm = 125.0
            
        return primary_emotion, prob_dict, round(valence, 2), round(arousal, 2), vocal_strain
