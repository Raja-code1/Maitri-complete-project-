"""
Pydantic Data Schemas for MAITRI
Multimodal AI Assistant for Psychological & Physical Well-Being of Astronauts
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import time


# ============================================================================
# MEMBER 1 SCHEMAS: COMPUTER VISION & FATIGUE
# ============================================================================

class VisualMicroExpression(BaseModel):
    brow_furrow: float = Field(0.0, ge=0.0, le=1.0, description="Eyebrow tension / furrow index")
    jaw_clench: float = Field(0.0, ge=0.0, le=1.0, description="Jaw clench / masseter tension")
    tension_score: float = Field(0.0, ge=0.0, le=1.0, description="Composite micro-expression tension")
    asymmetry_index: float = Field(0.0, ge=0.0, le=1.0, description="Facial movement asymmetry")


class VisualFatigueData(BaseModel):
    ear: float = Field(0.30, ge=0.0, le=1.0, description="Eye Aspect Ratio (EAR)")
    mar: float = Field(0.15, ge=0.0, le=2.0, description="Mouth Aspect Ratio (MAR)")
    perclos: float = Field(0.02, ge=0.0, le=1.0, description="Percentage of Eye Closure (PERCLOS)")
    blink_rate_bpm: float = Field(16.0, ge=0.0, description="Estimated blink rate per minute")
    is_yawning: bool = Field(False, description="Whether currently yawning")
    is_drowsy: bool = Field(False, description="Drowsiness state flag")
    head_pitch_deg: float = Field(0.0, description="Head pitch angle in degrees (droop indicator)")
    head_roll_deg: float = Field(0.0, description="Head roll angle in degrees")
    posture_stability: str = Field("stable", description="'stable', 'slumped', 'unsteady'")


class VisualStateData(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    face_detected: bool = True
    primary_emotion: str = Field("neutral", description="Primary classified emotion")
    emotion_confidences: Dict[str, float] = Field(
        default_factory=lambda: {"neutral": 0.90, "stressed": 0.05, "exhausted": 0.05}
    )
    fatigue_level: str = Field("low", description="'low', 'moderate', 'high', 'severe'")
    fatigue_score: float = Field(10.0, ge=0.0, le=100.0, description="Continuous fatigue score 0-100")
    fatigue_metrics: VisualFatigueData = Field(default_factory=VisualFatigueData)
    micro_expressions: VisualMicroExpression = Field(default_factory=VisualMicroExpression)
    confidence: float = Field(0.95, ge=0.0, le=1.0)


# ============================================================================
# MEMBER 2 SCHEMAS: AUDIO & SPEECH ANALYSIS
# ============================================================================

class AcousticFeatures(BaseModel):
    f0_pitch_hz: float = Field(140.0, ge=0.0, description="Mean Fundamental Frequency (F0)")
    pitch_variance: float = Field(15.0, description="Pitch standard deviation")
    jitter_local: float = Field(0.015, ge=0.0, description="Relative pitch perturbation (jitter)")
    shimmer_local: float = Field(0.035, ge=0.0, description="Relative amplitude perturbation (shimmer)")
    hnr_db: float = Field(18.0, description="Harmonics-to-Noise Ratio in dB")
    spectral_centroid_hz: float = Field(1800.0, description="Spectral brightness / centroid")
    zero_crossing_rate: float = Field(0.05, description="Zero crossing rate")
    rms_energy_db: float = Field(-22.0, description="Root Mean Square vocal energy")
    mfcc_features: List[float] = Field(default_factory=list, description="Top MFCC coefficients")


class AudioStateData(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    speech_detected: bool = True
    transcript: str = Field("", description="Offline transcribed speech")
    transcript_confidence: float = Field(0.95, ge=0.0, le=1.0)
    audio_emotion: str = Field("calm", description="Acoustic emotion label")
    emotion_probabilities: Dict[str, float] = Field(
        default_factory=lambda: {"calm": 0.85, "stressed": 0.10, "fatigued": 0.05}
    )
    valence: float = Field(0.2, ge=-1.0, le=1.0, description="Valence (-1 negative to +1 positive)")
    arousal: float = Field(0.3, ge=0.0, le=1.0, description="Arousal (0 calm to 1 hyperaroused)")
    vocal_strain_score: float = Field(15.0, ge=0.0, le=100.0, description="0-100 vocal tension index")
    speech_rate_wpm: float = Field(125.0, description="Speaking rate in words per minute")
    acoustic_features: AcousticFeatures = Field(default_factory=AcousticFeatures)


# ============================================================================
# MEMBER 3 SCHEMAS: CONVERSATIONAL AI & PSYCHOLOGICAL SUPPORT
# ============================================================================

class PsychologicalIntervention(BaseModel):
    intervention_type: str = Field("NONE", description="'NONE', 'CBT_RESTRUCTURING', 'BOX_BREATHING', 'SENSORY_GROUNDING', 'MICRO_REST', 'TACTICAL_PAUSE'")
    protocol_name: str = Field("Autonomous Monitoring", description="Human-readable protocol name")
    trigger_reason: str = Field("Nominal baseline maintained", description="Clinical rationale")
    pacing_steps: List[str] = Field(default_factory=list, description="Step-by-step guidance commands")
    duration_sec: int = Field(0, description="Recommended intervention duration in seconds")
    is_operational_safe: bool = Field(True, description="Safe to execute during flight tasks")


class DialogueTurn(BaseModel):
    speaker: str = Field("MAITRI", description="'ASTRONAUT' or 'MAITRI'")
    text: str
    timestamp: float = Field(default_factory=time.time)
    intervention: Optional[PsychologicalIntervention] = None


# ============================================================================
# MEMBER 4 SCHEMAS: MULTIMODAL FUSION & WELL-BEING
# ============================================================================

class MultimodalFusionContext(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    astronaut_id: str = Field("ASTRO-01-RAKESH", description="Astronaut callsign")
    
    # Raw modal summaries
    visual_state: VisualStateData = Field(default_factory=VisualStateData)
    audio_state: AudioStateData = Field(default_factory=AudioStateData)
    
    # Unified Indices
    awbi_score: float = Field(88.0, ge=0.0, le=100.0, description="Astronaut Well-Being Index (0=Critical, 100=Optimal)")
    stress_index: float = Field(15.0, ge=0.0, le=100.0, description="0-100 unified stress index")
    fatigue_index: float = Field(12.0, ge=0.0, le=100.0, description="0-100 unified fatigue index")
    cognitive_load_index: float = Field(25.0, ge=0.0, le=100.0, description="0-100 cognitive load")
    psychological_balance: str = Field("OPTIMAL", description="'OPTIMAL', 'MILD_STRAIN', 'MODERATE_STRESS', 'HIGH_STRAIN', 'CRITICAL'")
    
    # Fusion details
    cross_modal_congruence: float = Field(0.92, ge=0.0, le=1.0, description="Agreement between audio and visual emotion")
    dominant_concern: Optional[str] = None
    fusion_latency_ms: float = Field(12.5, description="End-to-end edge fusion latency in milliseconds")


# ============================================================================
# MEMBER 5 SCHEMAS: GROUND TELEMETRY & ALERT SYSTEM
# ============================================================================

class TelemetryAlert(BaseModel):
    alert_id: str = Field(..., description="Unique alert identifier")
    timestamp: float = Field(default_factory=time.time)
    severity: str = Field("GREEN", description="'GREEN', 'YELLOW', 'ORANGE', 'RED'")
    title: str
    description: str
    recommended_action: str
    notified_flight_surgeon: bool = False
    notified_mission_director: bool = False


class CCSDSPacketHeader(BaseModel):
    version_number: int = 0
    packet_type: int = 0  # 0=Telemetry, 1=Telecommand
    secondary_header_flag: int = 1
    application_process_id: int = 0x03A5  # APID for MAITRI
    sequence_flags: int = 3  # Unsegmented
    packet_sequence_count: int = 0
    packet_data_length: int = 0


class GroundTelemetryPacket(BaseModel):
    packet_id: str
    timestamp: float = Field(default_factory=time.time)
    station_id: str = "BAS-ORBIT-01"
    mission_id: str = "GAGANYAAN-BAS-CONTINUOUS-01"
    astronaut_id: str = "ASTRO-01-RAKESH"
    
    # CCSDS encapsulation
    ccsds_header: CCSDSPacketHeader = Field(default_factory=CCSDSPacketHeader)
    
    # Telemetry Payload
    awbi_score: float
    stress_index: float
    fatigue_index: float
    cognitive_load: float
    visual_emotion: str
    audio_emotion: str
    perclos_val: float
    pitch_mean_hz: float
    vocal_strain_score: float
    
    # Active Alert & Intervention
    current_alert: TelemetryAlert
    active_intervention: Optional[PsychologicalIntervention] = None
    
    # Integrity check
    crc32_checksum: str = ""
    hex_payload: str = ""
    is_downlink_acknowledged: bool = False
