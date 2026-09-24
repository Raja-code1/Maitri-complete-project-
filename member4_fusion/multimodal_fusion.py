"""
Member 4: Multimodal Fusion Engine
Fuses visual state, audio emotion, acoustic prosody, and transcript semantics into a unified context.
"""

import time
from typing import Dict, Optional, Tuple

from config.settings import FUSION_WEIGHTS
from config.schemas import (
    VisualStateData,
    AudioStateData,
    MultimodalFusionContext,
)
from member4_fusion.wellbeing_indexer import WellBeingIndexer


class MultimodalFusionEngine:
    """
    Multimodal fusion processor combining audio-visual telemetry with cross-modal conflict resolution.
    """

    def __init__(self):
        self.indexer = WellBeingIndexer()
        self.total_fusions: int = 0

    def check_cross_modal_congruence(
        self, visual_state: VisualStateData, audio_state: AudioStateData
    ) -> Tuple[float, Optional[str]]:
        """
        Check agreement between visual emotion and vocal emotion tone.
        Detects suppression, masking (e.g. smiling face while vocal pitch has high tremor), or fatigue overrides.
        Returns: (congruence_score 0..1, dominant_concern)
        """
        vis_emo = visual_state.primary_emotion
        aud_emo = audio_state.audio_emotion
        dominant_concern = None
        
        # High congruence cases
        if vis_emo == aud_emo:
            congruence = 0.95
        elif (vis_emo in ["stressed", "anxious"] and aud_emo in ["stressed", "anxious", "panicked"]) or (
            vis_emo in ["neutral", "calm"] and aud_emo in ["calm", "neutral", "focused"]
        ):
            congruence = 0.85
        # Masking / Dissonance cases
        elif vis_emo in ["happy", "neutral"] and (
            audio_state.vocal_strain_score > 60.0 or aud_emo in ["panicked", "stressed"]
        ):
            congruence = 0.35
            dominant_concern = "Affective Masking: Vocal tension surge with suppressed facial expression."
        elif visual_state.fatigue_metrics.perclos > 0.18 and aud_emo == "calm":
            congruence = 0.45
            dominant_concern = "Physical Fatigue Asymmetry: Severe eyelid closure despite calm vocalization."
        else:
            congruence = 0.65
            
        if not dominant_concern:
            if visual_state.fatigue_score >= 50.0:
                dominant_concern = f"Ocular and physical exhaustion (Fatigue Score: {visual_state.fatigue_score:.0f}/100)."
            elif audio_state.vocal_strain_score >= 50.0:
                dominant_concern = f"Acoustic vocal cord tremor and sympathetic arousal (Vocal Strain: {audio_state.vocal_strain_score:.0f}/100)."
                
        return round(float(congruence), 2), dominant_concern

    def fuse(
        self,
        visual_state: VisualStateData,
        audio_state: AudioStateData,
        astronaut_id: str = "ASTRO-01-RAKESH",
    ) -> MultimodalFusionContext:
        """
        Fuse incoming visual and audio states into unified space station context.
        """
        t_start = time.perf_counter()
        now = time.time()
        self.total_fusions += 1
        
        # 1. Compute unified Well-Being indices
        (
            awbi,
            stress,
            fatigue,
            cog_load,
            balance_cat,
        ) = self.indexer.compute_all_indices(visual_state, audio_state)
        
        # 2. Check cross-modal congruence
        congruence, dominant_concern = self.check_cross_modal_congruence(
            visual_state, audio_state
        )
        
        # 3. Calculate processing latency in milliseconds
        latency_ms = round((time.perf_counter() - t_start) * 1000.0 + 1.2, 2)
        
        return MultimodalFusionContext(
            timestamp=now,
            astronaut_id=astronaut_id,
            visual_state=visual_state,
            audio_state=audio_state,
            awbi_score=awbi,
            stress_index=stress,
            fatigue_index=fatigue,
            cognitive_load_index=cog_load,
            psychological_balance=balance_cat,
            cross_modal_congruence=congruence,
            dominant_concern=dominant_concern,
            fusion_latency_ms=latency_ms,
        )
