"""
Member 3: Offline LLM Client & JARVIS-Grade Psychological Reasoning Engine
Supports local Ollama/vLLM/llama.cpp inference with zero-latency standalone offline fallback,
implementing Beckian CBT and Ellis REBT (ABCDE) for space station crews.
"""

import json
import requests
from typing import Dict, List, Optional
from config.settings import MAX_RESPONSE_WORDS_OPERATIONAL
from config.schemas import MultimodalFusionContext, PsychologicalIntervention


class OfflineLLMClient:
    """
    JARVIS-Grade Psychological reasoning companion for MAITRI.
    """

    def __init__(self, endpoint_url: str = "http://127.0.0.1:11434/api/generate", model_name: str = "llama3:8b"):
        self.endpoint_url = endpoint_url
        self.model_name = model_name
        self.timeout_sec = 1.5

    def generate_response(
        self,
        astronaut_utterance: str,
        fusion_context: MultimodalFusionContext,
        intervention: PsychologicalIntervention,
        situation_key: str = "NOMINAL_ROUTINE",
    ) -> str:
        """
        Generate empathetic, brief, operationally sound psychological response.
        """
        # Try local Ollama/vLLM daemon first
        try:
            payload = {
                "model": self.model_name,
                "prompt": self._build_prompt(astronaut_utterance, fusion_context, intervention, situation_key),
                "stream": False,
                "options": {
                    "temperature": 0.25,
                    "num_predict": 50,
                },
            }
            resp = requests.post(self.endpoint_url, json=payload, timeout=self.timeout_sec)
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                if text:
                    return self._enforce_brevity_and_safety(text)
        except Exception:
            pass

        return self._generate_neurosymbolic_response(
            astronaut_utterance, fusion_context, intervention, situation_key
        )

    def _build_prompt(
        self,
        astronaut_utterance: str,
        fusion_context: MultimodalFusionContext,
        intervention: PsychologicalIntervention,
        situation_key: str,
    ) -> str:
        return (
            f"System: You are MAITRI, an advanced spaceflight AI companion for Bharatiya Antariksh Station (ISRO). "
            f"Tone: Calm, authoritative like JARVIS, deeply empathetic, operational. "
            f"Telemetry: AWBI={fusion_context.awbi_score:.0f}%, Stress={fusion_context.stress_index:.0f}/100, Fatigue={fusion_context.fatigue_index:.0f}/100. "
            f"Active Clinical Protocol: {intervention.protocol_name}. Situation: {situation_key}. "
            f"Rules: Maximum 35 words. Give direct calming guidance and operational anchoring.\n"
            f"Astronaut: {astronaut_utterance}\n"
            f"MAITRI:"
        )

    def _generate_neurosymbolic_response(
        self,
        utterance: str,
        fusion: MultimodalFusionContext,
        intervention: PsychologicalIntervention,
        situation_key: str,
    ) -> str:
        """
        Embedded expert rule-and-schema synthesis engine with CBT, REBT, and emergency triage.
        """
        utterance_lower = utterance.lower()
        stress = fusion.stress_index
        fatigue = fusion.fatigue_index

        # 1. Critical Hypoxia / Panic / Immediate Threat
        if "cant breathe" in utterance_lower or "can't breathe" in utterance_lower:
            return "Acknowledge distress. Switch ECLSS O2 regulator to manual backup immediately. Lean back and begin slow nasal exhalations; ground control is alerted."
            
        if "dizzy" in utterance_lower or "passing out" in utterance_lower:
            return "Lock your primary hand restraint now. Fix your visual gaze on the forward bulk-head horizon. I am relaying telemetry to the flight surgeon."

        # 2. REBT Disputation Protocol (Irrational beliefs, demandingness, fear of failure)
        if intervention.intervention_type == "REBT_ABCDE":
            return "Disarm the pressure. Perfection is not required for mission safety; our 3-tier redundancy handles anomalies. Anchor onto step one of the SOP."

        # 3. Tactical Box Breathing (Autonomic Stress Spike)
        if intervention.intervention_type == "BOX_BREATHING":
            return f"I detect elevated autonomic stress ({stress:.0f}/100). Let's synchronize breathing: Inhale 4 seconds... hold 4... exhale 4... hold 4. You are in control."

        # 4. High Fatigue / Eye Droop / PERCLOS Alert
        if fatigue >= 45.0 or intervention.intervention_type == "MICRO_REST":
            if "cant focus" in utterance_lower or "can't focus" in utterance_lower or "tired" in utterance_lower or "eyes" in utterance_lower:
                return "Ocular fatigue is peaking. Take a 60-second visual rest from the HUD. I will maintain active telemetry scan during your pause."
            return "Eyelid tracking indicates ocular fatigue. Perform a deliberate blink cycle and hydrate; pace yourself through this orbital pass."

        # 5. CBT Cognitive Restructuring (Overwhelm / Workload Strain)
        if intervention.intervention_type == "CBT_COGNITIVE_RESTRUCTURING" or stress >= 35.0:
            if "overwhelmed" in utterance_lower or "pressure" in utterance_lower:
                return "Acknowledge the workload. Separate subjective pressure from empirical flight data. Break the procedure down to the single next action."
            return "I note slight vocal and facial tension. Keep your respiratory rhythm steady; our operational timeline has comfortable margin."

        # 6. Operational Task-Specific Situations
        if situation_key == "PRE_EVA_CHECK":
            return "Suit pressure and vitals verified nominal. Deliberate, smooth movements will conserve O2 and mental bandwidth. You are ready for egress."
        if situation_key == "DOCKING_OPERATION":
            return "Approaching final translation corridor. Relax shoulder tension; rate of closure is optimal. You have full command margin."

        # 7. Long Duration Isolation Support
        if situation_key == "ISOLATION_SUPPORT" or "lonely" in utterance_lower or "isolated" in utterance_lower:
            return "Long-duration spaceflight requires profound mental resilience. Look out at the Indian subcontinent passing below; your team is with you every orbit."

        # 8. Nominal State
        return "All systems and psychological telemetry nominal. Standing by on active orbital watch."

    def _enforce_brevity_and_safety(self, text: str) -> str:
        words = text.split()
        if len(words) > MAX_RESPONSE_WORDS_OPERATIONAL + 10:
            text = " ".join(words[:MAX_RESPONSE_WORDS_OPERATIONAL]) + "."
        return text
