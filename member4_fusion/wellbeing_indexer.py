"""
Member 4: Astronaut Well-Being Index (AWBI) Calculator
Synthesizes multidimensional physiological & psychological metrics into unified indices.
"""

from typing import Dict, Tuple
import numpy as np

from config.settings import (
    AWBI_OPTIMAL_MIN,
    AWBI_ADVISORY_MAX,
    AWBI_CAUTION_MAX,
    AWBI_CRITICAL_MAX,
)
from config.schemas import VisualStateData, AudioStateData


class WellBeingIndexer:
    """
    Computes unified Astronaut Well-Being Index (AWBI), Stress Index, Fatigue Index,
    and Cognitive Load for ISRO space station crew.
    """

    def compute_stress_index(
        self, visual_state: VisualStateData, audio_state: AudioStateData
    ) -> float:
        """
        Compute unified stress score (0-100) from visual tension, vocal strain, and valence.
        """
        # Visual stress component (0-100)
        vis_tension = visual_state.micro_expressions.tension_score * 100.0
        vis_emo_stress = (
            visual_state.emotion_confidences.get("stressed", 0.0)
            + visual_state.emotion_confidences.get("anxious", 0.0)
        ) * 50.0
        visual_stress_comp = 0.6 * vis_tension + 0.4 * vis_emo_stress
        
        # Audio stress component (0-100)
        aud_strain = audio_state.vocal_strain_score
        aud_arousal = audio_state.arousal * 100.0
        aud_neg_valence = max(0.0, -audio_state.valence) * 100.0
        audio_stress_comp = 0.5 * aud_strain + 0.25 * aud_arousal + 0.25 * aud_neg_valence
        
        # Unified Stress Score
        stress_score = 0.45 * visual_stress_comp + 0.55 * audio_stress_comp
        return round(float(np.clip(stress_score, 0.0, 100.0)), 1)

    def compute_fatigue_index(
        self, visual_state: VisualStateData, audio_state: AudioStateData
    ) -> float:
        """
        Compute unified physical fatigue score (0-100) from PERCLOS, yawning, and vocal acoustic slowing.
        """
        vis_fatigue = visual_state.fatigue_score
        
        # Audio fatigue indicators (low vocal energy, low pitch, high shimmer)
        aud_fatigue_score = 0.0
        if audio_state.audio_emotion == "fatigued":
            aud_fatigue_score += 40.0
        if audio_state.acoustic_features.f0_pitch_hz < 115.0:
            aud_fatigue_score += 25.0
        if audio_state.acoustic_features.shimmer_local > 0.05:
            aud_fatigue_score += 20.0
        if audio_state.speech_rate_wpm < 95.0 and audio_state.speech_rate_wpm > 0:
            aud_fatigue_score += 15.0
            
        fatigue_score = 0.65 * vis_fatigue + 0.35 * aud_fatigue_score
        return round(float(np.clip(fatigue_score, 0.0, 100.0)), 1)

    def compute_cognitive_load_index(
        self, visual_state: VisualStateData, audio_state: AudioStateData
    ) -> float:
        """
        Estimate cognitive workload (0-100) from ocular dynamics and speech rate variations.
        """
        cog_load = 20.0  # baseline
        
        # Ocular blink extremes
        blink = visual_state.fatigue_metrics.blink_rate_bpm
        if blink > 28.0:
            cog_load += min(35.0, (blink - 28.0) * 2.0)
        elif blink < 8.0 and blink > 0:
            cog_load += min(30.0, (8.0 - blink) * 3.5)
            
        # Brow furrowing indicates cognitive concentration/effort
        cog_load += visual_state.micro_expressions.brow_furrow * 25.0
        
        # Speech rate anomalies
        wpm = audio_state.speech_rate_wpm
        if wpm > 175.0:
            cog_load += min(20.0, (wpm - 175.0) * 0.8)
        elif wpm < 85.0 and wpm > 0:
            cog_load += min(20.0, (85.0 - wpm) * 0.8)
            
        return round(float(np.clip(cog_load, 0.0, 100.0)), 1)

    def compute_all_indices(
        self, visual_state: VisualStateData, audio_state: AudioStateData
    ) -> Tuple[float, float, float, float, str]:
        """
        Derive AWBI, Stress, Fatigue, Cognitive Load, and Psychological Balance Category.
        Returns: (awbi_score, stress_index, fatigue_index, cognitive_load, balance_category)
        """
        stress = self.compute_stress_index(visual_state, audio_state)
        fatigue = self.compute_fatigue_index(visual_state, audio_state)
        cog_load = self.compute_cognitive_load_index(visual_state, audio_state)
        
        # AWBI (100 = optimal equilibrium, 0 = critical distress)
        awbi_raw = 100.0 - (0.42 * stress + 0.38 * fatigue + 0.20 * cog_load)
        awbi = round(float(np.clip(awbi_raw, 0.0, 100.0)), 1)
        
        # Determine Psychological Balance Classification
        if awbi >= AWBI_OPTIMAL_MIN:
            category = "OPTIMAL"
        elif awbi > AWBI_ADVISORY_MAX:
            category = "MILD_STRAIN"
        elif awbi > AWBI_CAUTION_MAX:
            category = "MODERATE_STRESS"
        elif awbi > AWBI_CRITICAL_MAX:
            category = "HIGH_STRAIN"
        else:
            category = "CRITICAL"
            
        return awbi, stress, fatigue, cog_load, category
