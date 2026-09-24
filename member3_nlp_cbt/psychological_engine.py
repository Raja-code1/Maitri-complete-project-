"""
Member 3: Advanced Evidence-Based Psychological Interventions Engine
Integrates Cognitive Behavioral Therapy (CBT), Rational Emotive Behavior Therapy (REBT),
Tactical 4-4-4-4 Box Breathing, 4-7-8 Recovery, and 5-4-3-2-1 Sensory Grounding for Spaceflight.
"""

from typing import Dict, List, Optional
from config.schemas import PsychologicalIntervention


class PsychologicalEngine:
    """
    JARVIS-Grade Psychological Support & Intervention Engine for Space Station Astronauts.
    Combines Beckian Cognitive Behavioral Therapy (CBT) and Ellis Rational Emotive Behavior Therapy (REBT).
    """

    PROTOCOLS: Dict[str, Dict] = {
        "REBT_ABCDE": {
            "name": "REBT (Rational Emotive Behavior Therapy) - ABCDE Disputation",
            "duration": 50,
            "operational_safe": True,
            "theory": "Albert Ellis Rational Emotive Behavior Therapy for High-Stakes Operations",
            "steps": [
                "A (Activating Event): Identify the operational stressor or telemetry anomaly without catastrophizing.",
                "B (Irrational Belief): Disarm demanding 'musts' ('I MUST not make errors; the station depends solely on me').",
                "C (Consequence): Acknowledge physiological stress reaction as normal adaptive sympathetic drive.",
                "D (Disputation): Challenge irrational belief: 'Mistakes are managed through 3x redundancy and ground cross-checks.'",
                "E (Effective New Philosophy): Rational acceptance: 'I will execute the immediate checklist procedure calmly.'",
            ],
            "purpose": "Eliminates cognitive panic, perfectionistic paralysis, and catastrophic escalation during flight anomalies.",
        },
        "CBT_COGNITIVE_RESTRUCTURING": {
            "name": "CBT (Cognitive Behavioral Therapy) - Cognitive Restructuring",
            "duration": 45,
            "operational_safe": True,
            "theory": "Beckian Cognitive Therapy for Operational Spaceflight",
            "steps": [
                "Identify Automatic Negative Thought (ANT) such as tunnel vision or overgeneralization.",
                "Examine empirical telemetry evidence: Separate subjective fear from verified instrument readouts.",
                "Generate balanced alternative cognition: Anchor onto checklist SOPs.",
                "Commit cognitive focus strictly to the single immediate physical action.",
            ],
            "purpose": "Breaks cognitive fixation, reduces operational errors, restores logical problem-solving.",
        },
        "BOX_BREATHING": {
            "name": "Tactical Box Breathing (4-4-4-4 Autonomic Reset)",
            "duration": 60,
            "operational_safe": True,
            "theory": "Vagus Nerve Autonomic Downregulation",
            "steps": [
                "Inhale smoothly through your nose... 1, 2, 3, 4.",
                "Hold breath gently... 1, 2, 3, 4.",
                "Exhale slowly through your mouth... 1, 2, 3, 4.",
                "Hold empty... 1, 2, 3, 4. Repeating cycle.",
            ],
            "purpose": "Rapid autonomic downregulation of heart rate variability and cortisol surge.",
        },
        "BREATHING_4_7_8": {
            "name": "4-7-8 Parasympathetic Recovery & Sleep Onset",
            "duration": 90,
            "operational_safe": False,
            "theory": "Deep Parasympathetic Activation",
            "steps": [
                "Exhale completely with a gentle whoosh.",
                "Inhale through nose quietly for 4 seconds.",
                "Hold breath firmly for 7 seconds.",
                "Exhale audibly through mouth for 8 seconds.",
            ],
            "purpose": "Induces deep parasympathetic recovery and counteracts circadian sleep disruption.",
        },
        "SENSORY_GROUNDING": {
            "name": "5-4-3-2-1 Sensory Orientation Protocol",
            "duration": 120,
            "operational_safe": False,
            "theory": "Somatic Somatosensory Re-anchoring in Microgravity",
            "steps": [
                "Notice 5 instruments or structural fixtures around the BAS module.",
                "Acknowledge 4 physical contact points (tether, foot restraint, glove tension).",
                "Listen for 3 ambient sounds (avionics hum, ECLSS pump rhythm, cooling loop).",
                "Identify 2 sensory nuances in the air circulation.",
                "Take 1 deep grounding breath and verify your operational horizon.",
            ],
            "purpose": "Counteracts spatial disorientation, isolation claustrophobia, or sensory detachment.",
        },
        "OPERATIONAL_MICRO_REST": {
            "name": "60-Second Ocular & Cognitive Micro-Rest",
            "duration": 60,
            "operational_safe": True,
            "theory": "Ocular PERCLOS Refresh & Cognitive Reset",
            "steps": [
                "Disengage gaze from primary display matrix for 20 seconds.",
                "Focus on distant station module bulkhead or Earth horizon through cupola.",
                "Perform gentle cervical spine rotation and shoulder girdle release.",
                "Re-engage display with relaxed focal depth.",
            ],
            "purpose": "Relieves visual display fatigue, dry-eye irritation, and microgravity ocular tension.",
        },
    }

    def select_intervention(
        self,
        stress_score: float,
        fatigue_score: float,
        vocal_strain: float,
        is_operational_task: bool = True,
        keyword_flags: Optional[List[str]] = None,
    ) -> PsychologicalIntervention:
        """
        Select the most clinically appropriate spaceflight intervention based on multimodal metrics.
        """
        keywords = [k.lower() for k in (keyword_flags or [])]
        kw_blob = " ".join(keywords)
        
        # 1. Critical Panic / Disorientation / Acute Distress
        if any(k in kw_blob for k in ["panicking", "panic", "disoriented", "losing my mind", "cant breathe", "can't breathe"]) or (
            stress_score >= 70.0 and vocal_strain >= 50.0
        ) or stress_score >= 75.0:
            if is_operational_task:
                p = self.PROTOCOLS["BOX_BREATHING"]
                return PsychologicalIntervention(
                    intervention_type="BOX_BREATHING",
                    protocol_name=p["name"],
                    trigger_reason="High acute autonomic stress surge detected during operational task.",
                    pacing_steps=p["steps"],
                    duration_sec=p["duration"],
                    is_operational_safe=p["operational_safe"],
                )
            else:
                p = self.PROTOCOLS["SENSORY_GROUNDING"]
                return PsychologicalIntervention(
                    intervention_type="SENSORY_GROUNDING",
                    protocol_name=p["name"],
                    trigger_reason="Severe disorientation / psychological distress flagged.",
                    pacing_steps=p["steps"],
                    duration_sec=p["duration"],
                    is_operational_safe=p["operational_safe"],
                )
                
        # 2. REBT Trigger (Catastrophizing, Perfectionism, Demandingness, Failure Anxiety)
        if any(k in kw_blob for k in ["fail", "mistake", "must not", "cant do this", "can't do this", "ruined", "pressure"]):
            p = self.PROTOCOLS["REBT_ABCDE"]
            return PsychologicalIntervention(
                intervention_type="REBT_ABCDE",
                protocol_name=p["name"],
                trigger_reason="Operational catastrophizing and irrational perfectionism pattern identified.",
                pacing_steps=p["steps"],
                duration_sec=p["duration"],
                is_operational_safe=p["operational_safe"],
            )

        # 3. Acute Physical & Visual Fatigue / Eye Droop
        if fatigue_score >= 45.0:
            if is_operational_task:
                p = self.PROTOCOLS["OPERATIONAL_MICRO_REST"]
                return PsychologicalIntervention(
                    intervention_type="MICRO_REST",
                    protocol_name=p["name"],
                    trigger_reason=f"Elevated physical fatigue ({fatigue_score:.0f}/100) and PERCLOS strain.",
                    pacing_steps=p["steps"],
                    duration_sec=p["duration"],
                    is_operational_safe=p["operational_safe"],
                )
            else:
                p = self.PROTOCOLS["BREATHING_4_7_8"]
                return PsychologicalIntervention(
                    intervention_type="BREATHING_4_7_8",
                    protocol_name=p["name"],
                    trigger_reason="High fatigue accumulation during off-duty recovery window.",
                    pacing_steps=p["steps"],
                    duration_sec=p["duration"],
                    is_operational_safe=p["operational_safe"],
                )
                
        # 4. Moderate Cognitive Stress / Task Frustration -> CBT Restructuring
        if stress_score >= 35.0 or vocal_strain >= 35.0:
            p = self.PROTOCOLS["CBT_COGNITIVE_RESTRUCTURING"]
            return PsychologicalIntervention(
                intervention_type="CBT_COGNITIVE_RESTRUCTURING",
                protocol_name=p["name"],
                trigger_reason="Cognitive stress accumulation and vocal tension detected.",
                pacing_steps=p["steps"],
                duration_sec=p["duration"],
                is_operational_safe=p["operational_safe"],
            )
            
        # 5. Nominal State
        return PsychologicalIntervention(
            intervention_type="NONE",
            protocol_name="Autonomous Monitoring",
            trigger_reason="All physiological and emotional parameters within nominal limits.",
            pacing_steps=["Maintain current operational rhythm."],
            duration_sec=0,
            is_operational_safe=True,
        )
