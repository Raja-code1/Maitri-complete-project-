"""
Member 4: MAITRI Central Core Orchestrator
Master integration engine binding Member 1, Member 2, Member 3, Member 4, and Member 5.
"""

import time
from typing import Dict, Optional, Any
import numpy as np

from member1_cv.vision_pipeline import VisionPipeline
from member2_audio.audio_pipeline import AudioPipeline
from member3_nlp_cbt.dialogue_manager import DialogueManager
from member4_fusion.multimodal_fusion import MultimodalFusionEngine
from member4_fusion.edge_runtime import EdgeRuntime
from member5_ground_telemetry.alert_engine import AlertEngine
from member5_ground_telemetry.telemetry_protocol import TelemetryProtocol
from member5_ground_telemetry.ground_station_logger import GroundStationLogger


class MaitriCore:
    """
    MAITRI Core: Standalone Multimodal AI Assistant for Astronaut Physical & Psychological Well-Being.
    """

    def __init__(self, astronaut_id: str = "ASTRO-01-RAKESH"):
        self.astronaut_id = astronaut_id
        
        # Member 1: Computer Vision & Physical Fatigue Lead
        self.vision_pipeline = VisionPipeline()
        
        # Member 2: Audio & Speech Analysis Lead
        self.audio_pipeline = AudioPipeline()
        
        # Member 3: Conversational AI & Psychological Support Lead
        self.dialogue_manager = DialogueManager()
        
        # Member 4: Fusion & Edge Integration Lead
        self.fusion_engine = MultimodalFusionEngine()
        self.edge_runtime = EdgeRuntime()
        
        # Member 5: Ground Telemetry & Alert System Lead
        self.alert_engine = AlertEngine()
        self.telemetry_protocol = TelemetryProtocol()
        self.ground_logger = GroundStationLogger()

    def process_multimodal_step(
        self,
        # Member 1 (CV) inputs
        frame: Optional[np.ndarray] = None,
        simulated_ear: Optional[float] = None,
        simulated_mar: Optional[float] = None,
        simulated_brow: Optional[float] = None,
        simulated_jaw: Optional[float] = None,
        head_pitch: float = 0.0,
        head_roll: float = 0.0,
        # Member 2 (Audio) inputs
        audio_array: Optional[np.ndarray] = None,
        simulated_pitch: Optional[float] = None,
        simulated_jitter: Optional[float] = None,
        simulated_shimmer: Optional[float] = None,
        transcript: Optional[str] = None,
        audio_duration_sec: float = 3.0,
        # Member 3 (Situation / Task) context
        situation_key: str = "NOMINAL_ROUTINE",
        is_operational_task: bool = True,
        timestamp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end multimodal perception, fusion, dialogue, and ground telemetry step.
        """
        t_start = time.perf_counter()
        now = timestamp if timestamp is not None else time.time()
        
        # STEP 1 (Member 1): Vision & Fatigue Perception
        visual_state = self.vision_pipeline.process_frame(
            frame=frame,
            simulated_ear=simulated_ear,
            simulated_mar=simulated_mar,
            simulated_brow=simulated_brow,
            simulated_jaw=simulated_jaw,
            head_pitch=head_pitch,
            head_roll=head_roll,
            current_time=now,
        )
        
        # STEP 2 (Member 2): Audio & Speech Perception
        audio_state = self.audio_pipeline.process_audio(
            audio_array=audio_array,
            simulated_pitch=simulated_pitch,
            simulated_jitter=simulated_jitter,
            simulated_shimmer=simulated_shimmer,
            simulated_transcript=transcript,
            duration_sec=audio_duration_sec,
            current_time=now,
        )
        
        # STEP 3 (Member 4): Multimodal Fusion & AWBI Calculation
        fusion_context = self.fusion_engine.fuse(
            visual_state=visual_state,
            audio_state=audio_state,
            astronaut_id=self.astronaut_id,
        )
        
        # STEP 4 (Member 3): Conversational Companion & Psychological Intervention
        astronaut_utterance = audio_state.transcript or "Status check."
        dialogue_turn = self.dialogue_manager.respond(
            astronaut_utterance=astronaut_utterance,
            fusion_context=fusion_context,
            situation_key=situation_key,
            is_operational=is_operational_task,
        )
        
        # STEP 5 (Member 5): Ground Alert Classification & CCSDS Telemetry Encoding
        alert = self.alert_engine.evaluate_telemetry(
            fusion_context=fusion_context,
            intervention=dialogue_turn.intervention,
        )
        
        telemetry_packet = self.telemetry_protocol.generate_packet(
            fusion_context=fusion_context,
            alert=alert,
            intervention=dialogue_turn.intervention,
        )
        
        # Log to Ground Station & Edge Memory
        self.ground_logger.log_packet(telemetry_packet)
        total_time_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        self.edge_runtime.record_cycle(fusion_context, total_time_ms)
        
        return {
            "cycle_timestamp": now,
            "total_execution_latency_ms": total_time_ms,
            "member1_visual_state": visual_state.model_dump(),
            "member2_audio_state": audio_state.model_dump(),
            "member3_dialogue": dialogue_turn.model_dump(),
            "member4_fusion_context": fusion_context.model_dump(),
            "member5_telemetry_packet": telemetry_packet.model_dump(),
            "member5_active_alert": alert.model_dump(),
            "edge_runtime_health": self.edge_runtime.get_runtime_health(),
        }
