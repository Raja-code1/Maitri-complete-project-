"""
Member 2: Audio Pipeline Orchestrator
Integrates Acoustic Feature Extraction (Pitch, Jitter, Shimmer, MFCCs), SER, and Offline STT.
"""

import time
from typing import Dict, Optional, Tuple, Union
import numpy as np

from config.schemas import AudioStateData, AcousticFeatures
from member2_audio.acoustic_features import AcousticFeatureExtractor
from member2_audio.voice_emotion import VoiceEmotionRecognizer
from member2_audio.speech_to_text import OfflineSpeechToText


class AudioPipeline:
    """
    Unified Audio and Speech Analysis pipeline for astronaut vocal monitoring.
    """

    def __init__(self):
        self.feature_extractor = AcousticFeatureExtractor()
        self.emotion_recognizer = VoiceEmotionRecognizer()
        self.stt_engine = OfflineSpeechToText()
        self.processed_audio_chunks: int = 0

    def process_audio(
        self,
        audio_array: Optional[np.ndarray] = None,
        simulated_pitch: Optional[float] = None,
        simulated_jitter: Optional[float] = None,
        simulated_shimmer: Optional[float] = None,
        simulated_transcript: Optional[str] = None,
        transcript: Optional[str] = None,
        duration_sec: float = 3.0,
        current_time: Optional[float] = None,
    ) -> AudioStateData:
        """
        Process audio waveform or telemetry parameters and output validated AudioStateData.
        """
        now = current_time if current_time is not None else time.time()
        self.processed_audio_chunks += 1
        raw_text = transcript if transcript is not None else simulated_transcript
        
        # 1. Feature Extraction (Acoustic & Prosodic)
        if audio_array is not None and len(audio_array) > 256:
            features = self.feature_extractor.extract_all(audio_array)
        else:
            # Simulated / parametric fallback
            f0 = simulated_pitch if simulated_pitch is not None else 138.0
            jitter = simulated_jitter if simulated_jitter is not None else 0.014
            shimmer = simulated_shimmer if simulated_shimmer is not None else 0.032
            features = AcousticFeatures(
                f0_pitch_hz=round(f0, 1),
                pitch_variance=round(12.0 + (jitter * 200.0), 1),
                jitter_local=round(jitter, 4),
                shimmer_local=round(shimmer, 4),
                hnr_db=round(max(5.0, 22.0 - (jitter * 300.0)), 1),
                spectral_centroid_hz=round(1750.0 + (f0 - 130.0) * 3.0, 1),
                zero_crossing_rate=0.048,
                rms_energy_db=-21.5,
                mfcc_features=[-12.5, 3.2, -1.8, 0.4, -0.2, 0.8, -0.5, 0.1, -0.3, 0.2, -0.1, 0.0, 0.1],
            )
            
        # 2. Transcription & Distress Keyword Spotting
        transcript, stt_conf, keywords = self.stt_engine.transcribe(
            simulated_text=raw_text
        )
        
        word_count = len(transcript.split()) if transcript else 0
        
        # 3. Voice Emotion Recognition (SER) & Vocal Strain
        (
            primary_emotion,
            emotion_probs,
            valence,
            arousal,
            vocal_strain,
        ) = self.emotion_recognizer.classify_voice_emotion(
            features=features,
            word_count=word_count,
            duration_sec=duration_sec,
        )
        
        # Cross-adjust if critical distress keywords are present in speech
        if len(keywords.get("distress_keywords", [])) > 0:
            if primary_emotion in ["calm", "neutral"]:
                primary_emotion = "stressed"
            vocal_strain = min(100.0, vocal_strain + 25.0)
            valence = max(-1.0, valence - 0.4)
            arousal = min(1.0, arousal + 0.3)
            emotion_probs["stressed"] = max(emotion_probs.get("stressed", 0.0), 0.70)
            
        return AudioStateData(
            timestamp=now,
            speech_detected=True,
            transcript=transcript,
            transcript_confidence=stt_conf,
            audio_emotion=primary_emotion,
            emotion_probabilities=emotion_probs,
            valence=valence,
            arousal=arousal,
            vocal_strain_score=vocal_strain,
            speech_rate_wpm=round(float((word_count / max(0.5, duration_sec)) * 60.0), 1),
            acoustic_features=features,
        )
