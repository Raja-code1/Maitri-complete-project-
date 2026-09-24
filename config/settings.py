"""
MAITRI System Configuration
Multimodal AI Assistant for Psychological & Physical Well-Being of Astronauts
Bharatiya Antariksh Station (BAS) / ISRO Missions
"""

import os
from typing import Dict, List

# System identification
SYSTEM_NAME = "MAITRI"
SYSTEM_VERSION = "2.4.0-EDGE"
STATION_ID = "BAS-ORBIT-01"
MISSION_NAME = "GAGANYAAN-BAS-CONTINUOUS-01"

# Computer Vision & Fatigue Thresholds (Member 1)
EAR_EYE_CLOSED_THRESHOLD = 0.20        # Eye Aspect Ratio below this indicates eyelid closure
EAR_DROWSY_THRESHOLD = 0.24            # Borderline eye openness
MAR_YAWN_THRESHOLD = 0.58              # Mouth Aspect Ratio above this indicates yawning
PERCLOS_ALERT_THRESHOLD = 0.15         # > 15% eyelid closure over 60s window indicates acute fatigue
BLINK_RATE_LOW_THRESHOLD = 8.0         # Blinks/min below 8 indicates fixed gaze / cognitive trance
BLINK_RATE_HIGH_THRESHOLD = 28.0       # Blinks/min above 28 indicates high stress / ocular strain
HEAD_DROOP_ANGLE_THRESHOLD = 18.0      # Degrees downward pitch indicating head droop / sleep onset

# Audio & Speech Analysis Thresholds (Member 2)
AUDIO_SAMPLE_RATE = 16000              # 16kHz standard for offline STT & SER
PITCH_MIN_HZ = 50.0                    # Human vocal fundamental frequency min
PITCH_MAX_HZ = 500.0                   # Human vocal fundamental frequency max
JITTER_ALERT_THRESHOLD = 0.035         # > 3.5% jitter indicates significant vocal cord tremor / stress
SHIMMER_ALERT_THRESHOLD = 0.080        # > 8.0% shimmer indicates vocal fatigue / instability
SPEECH_RATE_SLOW_WPM = 90              # Words/min below 90 indicates cognitive slowing / lethargy
SPEECH_RATE_FAST_WPM = 185             # Words/min above 185 indicates anxiety / panic

# Psychological & Intervention Thresholds (Member 3)
MAX_CONVERSATION_TURNS_OPERATIONAL = 4 # Keep dialogue concise during operational tasks
MAX_RESPONSE_WORDS_OPERATIONAL = 45    # Brevity limit for high-workload scenarios
CBT_INTERVENTION_COOLDOWN_SEC = 300    # 5-minute cooldown between unsolicited interventions

# Multimodal Fusion & Well-Being Weights (Member 4)
FUSION_WEIGHTS: Dict[str, float] = {
    "visual_emotion": 0.30,
    "fatigue_perclos": 0.25,
    "audio_emotion_tone": 0.25,
    "text_sentiment_context": 0.20,
}

# Astronaut Well-Being Index (AWBI) Classification
# 80-100: Optimal / Balanced
# 60-79: Mild Strain (Nominal)
# 40-59: Moderate Stress / Fatigue (Advisory)
# 20-39: High Strain (Caution)
# 0-19: Critical / Severe Distress (Emergency)
AWBI_OPTIMAL_MIN = 80.0
AWBI_ADVISORY_MAX = 59.9
AWBI_CAUTION_MAX = 39.9
AWBI_CRITICAL_MAX = 19.9

# Ground Telemetry & Alert Protocol (Member 5)
GROUND_STATION_ID = "ISTRAC-BLR-01"
TELEMETRY_PACKET_APID = 0x03A5         # CCSDS Application Process ID for MAITRI Health Packets
TELEMETRY_INTERVAL_SEC = 5.0           # Nominal reporting interval
TELEMETRY_BURST_INTERVAL_SEC = 1.0     # Critical event reporting interval
SIMULATED_UPLINK_DELAY_SEC = 0.45      # Low Earth Orbit / Lunar lag simulation

# Emotion & Alert Categories
EMOTION_CLASSES: List[str] = [
    "neutral", "calm", "happy", "focused", "stressed", "anxious", "exhausted", "sad", "discomfort"
]

ALERT_SEVERITIES = {
    "GREEN": "Nominal / Balanced State",
    "YELLOW": "Advisory / Mild Stress or Fatigue Detected",
    "ORANGE": "Caution / Moderate Cognitive or Physical Strain",
    "RED": "Critical / Emergency Escalation Required",
}
