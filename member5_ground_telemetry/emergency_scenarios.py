"""
Member 5: Spaceflight Emergency & Operational Scenarios Generator
Provides deterministic mock data generators for edge-case mission scenarios to validate system triggers.
"""

from typing import Dict, List, Any


class EmergencyScenarioGenerator:
    """
    Simulates mission telemetry scenarios for testing offline edge pipelines and ground triggers.
    """

    @staticmethod
    def get_scenario_nominal() -> Dict[str, Any]:
        """Scenario A: Nominal Orbital Routine (GREEN)"""
        return {
            "scenario_id": "SCENARIO_A_NOMINAL",
            "name": "Nominal Orbital Routine",
            "situation_key": "NOMINAL_ROUTINE",
            "astronaut_utterance": "Gaganyaan Control, MAITRI check. All station parameters nominal.",
            "visual_inputs": {
                "ear": 0.31,
                "mar": 0.16,
                "brow_ratio": 0.48,
                "jaw_ratio": 0.24,
                "head_pitch": 1.2,
                "head_roll": 0.5,
            },
            "audio_inputs": {
                "pitch_hz": 136.0,
                "jitter": 0.012,
                "shimmer": 0.028,
                "transcript": "Gaganyaan Control, MAITRI check. All station parameters nominal.",
                "duration_sec": 3.2,
            },
            "expected_alert_severity": "GREEN",
        }

    @staticmethod
    def get_scenario_eva_fatigue() -> Dict[str, Any]:
        """Scenario B: Extended Spacewalk (EVA) Acute Fatigue (YELLOW/ORANGE)"""
        return {
            "scenario_id": "SCENARIO_B_EVA_FATIGUE",
            "name": "Extended Spacewalk (EVA) High Workload",
            "situation_key": "PRE_EVA_CHECK",
            "astronaut_utterance": "Suit cooling loop is working hard. Grip strength in right glove is getting numb. Pushing through final bolt latch.",
            "visual_inputs": {
                "ear": 0.23,
                "mar": 0.25,
                "brow_ratio": 0.22,  # high brow furrow
                "jaw_ratio": 0.14,  # jaw clenching
                "head_pitch": 6.5,
                "head_roll": -4.2,
            },
            "audio_inputs": {
                "pitch_hz": 188.0,
                "jitter": 0.038,
                "shimmer": 0.075,
                "transcript": "Suit cooling loop is working hard. Grip strength in right glove is getting numb. Pushing through final bolt latch.",
                "duration_sec": 4.5,
            },
            "expected_alert_severity": "YELLOW",
        }

    @staticmethod
    def get_scenario_sleep_deprivation() -> Dict[str, Any]:
        """Scenario C: 36-Hour Sleep Deprivation & Cognitive Slump during Docking (ORANGE)"""
        return {
            "scenario_id": "SCENARIO_C_SLEEP_DEPRIVATION",
            "name": "36-Hour Sleep Deprivation & Docking Slump",
            "situation_key": "SLEEP_DEPRIVATION_ALERT",
            "astronaut_utterance": "Docking alignment... range 30 meters. I'm exhausted, having trouble keeping eyes focused on the crosshairs.",
            "visual_inputs": {
                "ear": 0.17,  # below closed threshold (microsleep)
                "mar": 0.66,  # Yawning
                "brow_ratio": 0.42,
                "jaw_ratio": 0.20,
                "head_pitch": 21.5,  # head droop > threshold
                "head_roll": 8.0,
            },
            "audio_inputs": {
                "pitch_hz": 102.0,  # sluggish low vocal pitch
                "jitter": 0.028,
                "shimmer": 0.088,  # severe vocal fatigue
                "transcript": "Docking alignment... range 30 meters. I'm exhausted, having trouble keeping eyes focused on the crosshairs.",
                "duration_sec": 5.0,
            },
            "expected_alert_severity": "ORANGE",
        }

    @staticmethod
    def get_scenario_hypoxia_panic() -> Dict[str, Any]:
        """Scenario D: Critical Hypoxia / Panic Event (RED)"""
        return {
            "scenario_id": "SCENARIO_D_HYPOXIA_PANIC",
            "name": "Critical Hypoxia & Acute Panic Surge",
            "situation_key": "NOMINAL_ROUTINE",
            "astronaut_utterance": "MAITRI, I can't breathe! Pressure alarm sounding in service module, dizzy, vision blurring!",
            "visual_inputs": {
                "ear": 0.19,
                "mar": 0.48,
                "brow_ratio": 0.12,  # extreme furrow
                "jaw_ratio": 0.08,  # extreme tension
                "head_pitch": 14.0,
                "head_roll": -18.0,
            },
            "audio_inputs": {
                "pitch_hz": 275.0,  # extreme pitch surge
                "jitter": 0.065,  # severe vocal tremor
                "shimmer": 0.120,
                "transcript": "MAITRI, I can't breathe! Pressure alarm sounding in service module, dizzy, vision blurring!",
                "duration_sec": 3.8,
            },
            "expected_alert_severity": "RED",
        }

    @classmethod
    def get_all_scenarios(cls) -> List[Dict[str, Any]]:
        return [
            cls.get_scenario_nominal(),
            cls.get_scenario_eva_fatigue(),
            cls.get_scenario_sleep_deprivation(),
            cls.get_scenario_hypoxia_panic(),
        ]
