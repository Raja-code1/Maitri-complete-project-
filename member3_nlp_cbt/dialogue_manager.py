"""
Member 3: Dialogue Manager
Controls adaptive conversational turns, pacing, and multi-turn empathetic spaceflight dialogue.
"""

import time
from collections import deque
from typing import Dict, List, Optional

from config.schemas import (
    DialogueTurn,
    MultimodalFusionContext,
    PsychologicalIntervention,
)
from member3_nlp_cbt.psychological_engine import PsychologicalEngine
from member3_nlp_cbt.situation_templates import SituationTemplateManager
from member3_nlp_cbt.offline_llm_client import OfflineLLMClient


class DialogueManager:
    """
    Orchestrates adaptive conversation flows, CBT/tactical interventions, and dialogue turns.
    """

    def __init__(self):
        self.psych_engine = PsychologicalEngine()
        self.templates = SituationTemplateManager()
        self.llm_client = OfflineLLMClient()
        self.history: deque = deque(maxlen=20)
        self.last_intervention_time: float = 0.0

    def respond(
        self,
        astronaut_utterance: str,
        fusion_context: MultimodalFusionContext,
        situation_key: str = "NOMINAL_ROUTINE",
        is_operational: bool = True,
    ) -> DialogueTurn:
        """
        Process astronaut input along with current multimodal context to generate supportive turn.
        """
        now = time.time()
        
        # 1. Log astronaut turn
        self.history.append(
            DialogueTurn(speaker="ASTRONAUT", text=astronaut_utterance, timestamp=now)
        )
        
        # 2. Select evidence-based psychological intervention based on multimodal metrics
        intervention: PsychologicalIntervention = self.psych_engine.select_intervention(
            stress_score=fusion_context.stress_index,
            fatigue_score=fusion_context.fatigue_index,
            vocal_strain=fusion_context.audio_state.vocal_strain_score,
            is_operational_task=is_operational,
            keyword_flags=[astronaut_utterance.lower()],
        )
        
        # 3. Generate adaptive, situation-aware companion response
        reply_text = self.llm_client.generate_response(
            astronaut_utterance=astronaut_utterance,
            fusion_context=fusion_context,
            intervention=intervention,
            situation_key=situation_key,
        )
        
        # 4. Create and record MAITRI turn
        maitri_turn = DialogueTurn(
            speaker="MAITRI",
            text=reply_text,
            timestamp=now,
            intervention=intervention,
        )
        self.history.append(maitri_turn)
        
        return maitri_turn

    def get_conversation_history(self) -> List[Dict]:
        return [
            {
                "speaker": t.speaker,
                "text": t.text,
                "timestamp": t.timestamp,
                "intervention_type": t.intervention.intervention_type if t.intervention else None,
            }
            for t in self.history
        ]
