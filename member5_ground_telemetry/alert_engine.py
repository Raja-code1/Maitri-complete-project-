"""
Member 5: Multi-Tier Ground Alert & Escalation Engine
Evaluates psychological and physical telemetry against flight safety parameters to trigger alerts.
"""

import time
import uuid
from typing import Dict, List, Optional, Tuple

from config.settings import (
    AWBI_ADVISORY_MAX,
    AWBI_CAUTION_MAX,
    AWBI_CRITICAL_MAX,
    ALERT_SEVERITIES,
)
from config.schemas import (
    MultimodalFusionContext,
    TelemetryAlert,
    PsychologicalIntervention,
)


class AlertEngine:
    """
    Classifies flight crew telemetry and manages ground escalation triggers.
    """

    def __init__(self):
        self.alert_counter: int = 0
        self.active_alerts: List[TelemetryAlert] = []

    def evaluate_telemetry(
        self,
        fusion_context: MultimodalFusionContext,
        intervention: Optional[PsychologicalIntervention] = None,
    ) -> TelemetryAlert:
        """
        Evaluate multimodal fusion context and produce a structured TelemetryAlert.
        """
        self.alert_counter += 1
        now = time.time()
        alert_id = f"ALT-{int(now)}-{self.alert_counter:04d}"
        
        awbi = fusion_context.awbi_score
        stress = fusion_context.stress_index
        fatigue = fusion_context.fatigue_index
        perclos = fusion_context.visual_state.fatigue_metrics.perclos
        vocal_strain = fusion_context.audio_state.vocal_strain_score
        transcript_text = fusion_context.audio_state.transcript.lower()
        
        # Check for Critical RED triggers
        is_critical = (
            awbi <= AWBI_CRITICAL_MAX
            or stress >= 80.0
            or "cant breathe" in transcript_text
            or "can't breathe" in transcript_text
            or "hypoxia" in transcript_text
            or "passing out" in transcript_text
            or (perclos > 0.25 and fatigue > 80.0)
        )
        
        # Check for ORANGE Caution triggers
        is_caution = (
            awbi <= AWBI_CAUTION_MAX
            or fatigue >= 65.0
            or stress >= 65.0
            or perclos >= 0.18
            or vocal_strain >= 70.0
            or "disoriented" in transcript_text
            or "dizzy" in transcript_text
        )
        
        # Check for YELLOW Advisory triggers (Mild Strain / Early Warning)
        is_advisory = (
            awbi < 80.0
            or fatigue >= 30.0
            or stress >= 28.0
            or vocal_strain >= 35.0
            or fusion_context.visual_state.fatigue_metrics.is_yawning
            or fusion_context.visual_state.primary_emotion in ["stressed", "anxious", "exhausted"]
        )
        
        if is_critical:
            severity = "RED"
            title = "CRITICAL: Severe Crew Distress / Physiological Alert"
            description = (
                f"Severe physiological or cognitive breakdown detected (AWBI: {awbi:.1f}, "
                f"Stress: {stress:.1f}, Fatigue: {fatigue:.1f}). Acute safety risk."
            )
            action = "IMMEDIATE ESCALATION TO ISTRAC MISSION DIRECTOR & FLIGHT SURGEON. Abort high-risk tasks."
            notif_surgeon = True
            notif_director = True
        elif is_caution:
            severity = "ORANGE"
            title = "CAUTION: Elevated Fatigue / Cognitive Load Risk"
            description = (
                f"Substantial fatigue or stress accumulation (AWBI: {awbi:.1f}, "
                f"PERCLOS: {perclos*100:.1f}%, Vocal Strain: {vocal_strain:.1f})."
            )
            action = "Log to Ground Station. Flight Surgeon advisory generated. Initiate shift rotation relief."
            notif_surgeon = True
            notif_director = False
        elif is_advisory:
            severity = "YELLOW"
            title = "ADVISORY: Mild Strain / Fatigue Onset"
            description = (
                f"Mild physiological/emotional stress or ocular fatigue detected (AWBI: {awbi:.1f})."
            )
            action = "Autonomous onboard psychological guidance active. No immediate ground intervention needed."
            notif_surgeon = False
            notif_director = False
        else:
            severity = "GREEN"
            title = "NOMINAL: Balanced Well-Being State"
            description = f"Crew well-being index optimal at {awbi:.1f}%. All parameters within flight tolerances."
            action = "Continue standard flight schedule."
            notif_surgeon = False
            notif_director = False

        alert = TelemetryAlert(
            alert_id=alert_id,
            timestamp=now,
            severity=severity,
            title=title,
            description=description,
            recommended_action=action,
            notified_flight_surgeon=notif_surgeon,
            notified_mission_director=notif_director,
        )
        
        if severity in ["YELLOW", "ORANGE", "RED"]:
            self.active_alerts.append(alert)
            
        return alert
