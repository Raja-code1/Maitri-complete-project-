"""
Member 3: Situation-Based Spaceflight Interaction Templates
Maintains brief, non-intrusive, operationally aligned dialogue for astronauts.
"""

from typing import Dict, List, Optional
from config.settings import MAX_RESPONSE_WORDS_OPERATIONAL


class SituationTemplateManager:
    """
    Manages curated situation-aware templates ensuring conversations stay brief,
    operationally focused, and calming.
    """

    SITUATIONS: Dict[str, Dict] = {
        "PRE_EVA_CHECK": {
            "title": "Pre-EVA Spacewalk Psychological Readiness",
            "context": "Astronaut gearing up for Extravehicular Activity in airlock.",
            "prompt_system": (
                "You are MAITRI assisting an astronaut in the BAS airlock preparing for EVA. "
                "Keep response under 30 words. Confirm readiness, emphasize pacing, and remind them to anchor their breathing."
            ),
            "fallback_responses": [
                "Airlock vitals nominal. Suit pressure locked. Take one deep grounding breath before egress; pacing is your anchor.",
                "Mental readiness verified. Remember: deliberate, slow movements preserve O2 and focus. You are fully prepared for this EVA.",
            ],
        },
        "DOCKING_OPERATION": {
            "title": "High-Cognitive Load Docking & Proximity Operations",
            "context": "Active manual/assisted docking of cargo/crew capsule.",
            "prompt_system": (
                "You are MAITRI. Astronaut is performing precision docking maneuvers with elevated cognitive load. "
                "Keep responses under 20 words. Ultra-concise, calming, operational focus."
            ),
            "fallback_responses": [
                "Range and rate stable. Relax shoulder tension; keep primary scan on crosshair alignment. You have full margin.",
                "Laser rangefinder locked. Exhale smoothly. Focus strictly on final translation burn.",
            ],
        },
        "SLEEP_DEPRIVATION_ALERT": {
            "title": "Extended Shift & Sleep Deprivation Countermeasure",
            "context": "Astronaut has accumulated >20h wakefulness with drooping eyelids (PERCLOS alert).",
            "prompt_system": (
                "You are MAITRI. Astronaut showing fatigue/PERCLOS warning. Provide immediate gentle alerting and micro-rest suggestion."
            ),
            "fallback_responses": [
                "Elevated eyelid closure detected. Please perform a 60-second ocular refresh and hydrate. Logging shift hand-off recommendation to ground.",
                "Microsleep signature flagged on ocular telemetry. Engage manual verbal verification with station commander.",
            ],
        },
        "ISOLATION_SUPPORT": {
            "title": "Long-Duration Spaceflight Isolation & Psychological Check-in",
            "context": "Off-duty rest period, astronaut feeling isolation or sensory monotony.",
            "prompt_system": (
                "You are MAITRI companion. Empathetic, supportive, warm, space-aware tone. Keep response under 45 words."
            ),
            "fallback_responses": [
                "Earth is rising over the Himalayas on orbit 4,218. Take a moment at the cupola to connect with the view. You're doing extraordinary work up here.",
                "Isolation in microgravity is physically and mentally demanding. Your crew and ground team are with you every kilometer of the journey.",
            ],
        },
        "NOMINAL_ROUTINE": {
            "title": "Routine Autonomous Health Check",
            "context": "Standard day-to-day operations with balanced well-being.",
            "prompt_system": "You are MAITRI. Keep response under 15 words. Polite, efficient.",
            "fallback_responses": [
                "All physiological and emotional telemetry nominal. Standing by on standby mode.",
                "Well-being index optimal at 92%. Station systems and schedule in sync.",
            ],
        },
    }

    def get_situation(self, situation_key: str) -> Dict:
        return self.SITUATIONS.get(situation_key, self.SITUATIONS["NOMINAL_ROUTINE"])

    def get_fallback_reply(self, situation_key: str, index: int = 0) -> str:
        sit = self.get_situation(situation_key)
        replies = sit.get("fallback_responses", ["System operational."])
        return replies[index % len(replies)]
