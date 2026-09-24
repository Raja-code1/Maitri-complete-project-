"""
Comprehensive Test Suite for MAITRI Multimodal Assistant
Validates Member 1, Member 2, Member 3, Member 4, and Member 5 modules.
"""

import unittest
import numpy as np
import time
import os
import sys

# Ensure repository root is in pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Member 1
from member1_cv.facial_emotion import FacialEmotionRecognizer
from member1_cv.fatigue_detector import FatigueDetector
from member1_cv.micro_expression import MicroExpressionAnalyzer
from member1_cv.vision_pipeline import VisionPipeline

# Member 2
from member2_audio.acoustic_features import AcousticFeatureExtractor
from member2_audio.voice_emotion import VoiceEmotionRecognizer
from member2_audio.speech_to_text import OfflineSpeechToText
from member2_audio.audio_pipeline import AudioPipeline

# Member 3
from member3_nlp_cbt.psychological_engine import PsychologicalEngine
from member3_nlp_cbt.situation_templates import SituationTemplateManager
from member3_nlp_cbt.offline_llm_client import OfflineLLMClient
from member3_nlp_cbt.dialogue_manager import DialogueManager

# Member 4
from member4_fusion.wellbeing_indexer import WellBeingIndexer
from member4_fusion.multimodal_fusion import MultimodalFusionEngine
from member4_fusion.edge_runtime import EdgeRuntime
from member4_fusion.maitri_core import MaitriCore

# Member 5
from member5_ground_telemetry.alert_engine import AlertEngine
from member5_ground_telemetry.telemetry_protocol import TelemetryProtocol, CCSDSPacketEncoder
from member5_ground_telemetry.ground_station_logger import GroundStationLogger
from member5_ground_telemetry.emergency_scenarios import EmergencyScenarioGenerator

from data.test_assets import generate_synthetic_audio, generate_synthetic_face_frame


class TestMaitriSystem(unittest.TestCase):

    def setUp(self):
        self.core = MaitriCore(astronaut_id="TEST-ASTRO-01")

    # =========================================================================
    # MEMBER 1 TESTS: VISION & FATIGUE
    # =========================================================================
    def test_member1_fatigue_detector(self):
        detector = FatigueDetector(window_size=30)
        
        # Test nominal open eyes
        data_open = detector.update_frame(ear_value=0.30, mar_value=0.15)
        self.assertFalse(data_open.is_drowsy)
        self.assertFalse(data_open.is_yawning)
        
        # Test closed eyes sequence to trigger PERCLOS and drowsiness
        for _ in range(10):
            data_closed = detector.update_frame(ear_value=0.12, mar_value=0.15)
            
        self.assertGreater(data_closed.perclos, 0.15)
        self.assertTrue(data_closed.is_drowsy)
        
        score = detector.calculate_continuous_fatigue_score(data_closed)
        self.assertGreaterEqual(score, 30.0)

    def test_member1_micro_expressions(self):
        analyzer = MicroExpressionAnalyzer()
        exp = analyzer.analyze_facial_tension(
            brow_distance_ratio=0.15,  # high furrow
            lip_compression_ratio=0.10,  # jaw clench
        )
        self.assertGreater(exp.brow_furrow, 0.6)
        self.assertGreater(exp.jaw_clench, 0.5)
        self.assertGreater(exp.tension_score, 0.5)

    def test_member1_vision_pipeline_synthetic_frame(self):
        pipeline = VisionPipeline()
        frame = generate_synthetic_face_frame(eye_open=True, smiling=True)
        result = pipeline.process_frame(frame=frame)
        self.assertTrue(result.face_detected)
        self.assertIn(result.primary_emotion, ["neutral", "calm", "happy", "focused"])
        self.assertIsNotNone(result.fatigue_metrics)

    # =========================================================================
    # MEMBER 2 TESTS: AUDIO & SPEECH
    # =========================================================================
    def test_member2_acoustic_features_synthetic(self):
        extractor = AcousticFeatureExtractor(sample_rate=16000)
        audio = generate_synthetic_audio(duration_sec=1.0, f0_hz=150.0, jitter_amount=0.01)
        features = extractor.extract_all(audio)
        
        self.assertGreater(features.f0_pitch_hz, 80.0)
        self.assertLess(features.f0_pitch_hz, 300.0)
        self.assertGreater(features.jitter_local, 0.0)
        self.assertEqual(len(features.mfcc_features), 13)

    def test_member2_voice_emotion_and_strain(self):
        recognizer = VoiceEmotionRecognizer()
        from config.schemas import AcousticFeatures
        
        # High stress / jittered features
        stressed_feat = AcousticFeatures(
            f0_pitch_hz=230.0,
            pitch_variance=35.0,
            jitter_local=0.045,
            shimmer_local=0.090,
            hnr_db=10.0,
            spectral_centroid_hz=2600.0,
            zero_crossing_rate=0.08,
            rms_energy_db=-14.0,
            mfcc_features=[],
        )
        strain = recognizer.compute_vocal_strain(stressed_feat)
        self.assertGreater(strain, 50.0)
        
        emo, probs, val, aro, st = recognizer.classify_voice_emotion(stressed_feat)
        self.assertIn(emo, ["stressed", "anxious", "panicked"])
        self.assertGreater(aro, 0.4)

    def test_member2_keyword_spotting(self):
        stt = OfflineSpeechToText()
        text = "I am dizzy and can't breathe, please advise."
        transcript, conf, kw = stt.transcribe(simulated_text=text)
        self.assertTrue(
            any("breathe" in k for k in kw["distress_keywords"]),
            f"Expected breathing distress keyword, got {kw['distress_keywords']}"
        )
        self.assertIn("dizzy", kw["distress_keywords"])

    # =========================================================================
    # MEMBER 3 TESTS: CONVERSATIONAL PSYCHOLOGY & CBT
    # =========================================================================
    def test_member3_psychological_engine(self):
        engine = PsychologicalEngine()
        
        # High stress triggers Box Breathing
        interv_stress = engine.select_intervention(stress_score=75.0, fatigue_score=20.0, vocal_strain=60.0)
        self.assertEqual(interv_stress.intervention_type, "BOX_BREATHING")
        self.assertTrue(len(interv_stress.pacing_steps) >= 3)
        
        # High fatigue triggers Micro-Rest
        interv_fatigue = engine.select_intervention(stress_score=20.0, fatigue_score=65.0, vocal_strain=15.0)
        self.assertEqual(interv_fatigue.intervention_type, "MICRO_REST")

    def test_member3_offline_dialogue(self):
        dm = DialogueManager()
        fusion_ctx = self.core.fusion_engine.fuse(
            visual_state=self.core.vision_pipeline.process_frame(simulated_ear=0.30),
            audio_state=self.core.audio_pipeline.process_audio(simulated_pitch=135.0),
        )
        turn = dm.respond(
            astronaut_utterance="All systems functioning on orbit.",
            fusion_context=fusion_ctx,
            situation_key="NOMINAL_ROUTINE",
        )
        self.assertEqual(turn.speaker, "MAITRI")
        self.assertIsNotNone(turn.text)
        self.assertLess(len(turn.text.split()), 50)

    # =========================================================================
    # MEMBER 4 TESTS: MULTIMODAL FUSION & AWBI
    # =========================================================================
    def test_member4_multimodal_indexer(self):
        indexer = WellBeingIndexer()
        v_fresh = self.core.vision_pipeline.process_frame(simulated_ear=0.32, simulated_mar=0.15)
        a_calm = self.core.audio_pipeline.process_audio(simulated_pitch=135.0, simulated_jitter=0.01)
        
        awbi, stress, fatigue, cog, balance = indexer.compute_all_indices(v_fresh, a_calm)
        self.assertGreaterEqual(awbi, 80.0)
        self.assertEqual(balance, "OPTIMAL")

    def test_member4_cross_modal_congruence_detection(self):
        engine = MultimodalFusionEngine()
        # Visual smiling with screaming vocal tremor
        v = self.core.vision_pipeline.process_frame(simulated_ear=0.30, simulated_mar=0.35)
        a = self.core.audio_pipeline.process_audio(simulated_pitch=260.0, simulated_jitter=0.05)
        
        congruence, concern = engine.check_cross_modal_congruence(v, a)
        self.assertLess(congruence, 0.70)
        self.assertIsNotNone(concern)

    # =========================================================================
    # MEMBER 5 TESTS: GROUND TELEMETRY & CCSDS PROTOCOL
    # =========================================================================
    def test_member5_ground_alert_and_ccsds_crc32(self):
        telemetry = TelemetryProtocol()
        alert_eng = AlertEngine()
        
        # Simulate Critical Hypoxia scenario
        v_crit = self.core.vision_pipeline.process_frame(simulated_ear=0.18, simulated_brow=0.1)
        a_crit = self.core.audio_pipeline.process_audio(
            simulated_pitch=280.0,
            simulated_jitter=0.06,
            transcript="I can't breathe! Hypoxia alarm!",
        )
        fusion = self.core.fusion_engine.fuse(v_crit, a_crit)
        alert = alert_eng.evaluate_telemetry(fusion)
        
        self.assertEqual(alert.severity, "RED")
        self.assertTrue(alert.notified_flight_surgeon)
        self.assertTrue(alert.notified_mission_director)
        
        # Test CCSDS serialization & CRC-32 integrity
        pkt = telemetry.generate_packet(fusion, alert)
        self.assertEqual(pkt.ccsds_header.application_process_id, 0x03A5)
        self.assertTrue(len(pkt.hex_payload) > 0)
        
        # Verify CRC-32
        is_valid = telemetry.verify_packet_integrity(pkt.hex_payload, pkt.crc32_checksum)
        self.assertTrue(is_valid)

    # =========================================================================
    # END-TO-END LATENCY & CORE INTEGRATION TEST
    # =========================================================================
    def test_end_to_end_core_latency_under_100ms(self):
        res = self.core.process_multimodal_step()
        latency_ms = res["total_execution_latency_ms"]
        self.assertLess(latency_ms, 100.0)
        self.assertIn("member1_visual_state", res)
        self.assertIn("member2_audio_state", res)
        self.assertIn("member3_dialogue", res)
        self.assertIn("member4_fusion_context", res)
        self.assertIn("member5_telemetry_packet", res)

    def test_fastapi_rest_endpoints(self):
        from fastapi.testclient import TestClient
        from api.server import app
        client = TestClient(app)
        
        # Test status root HTML or JSON
        resp = client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ONLINE_STANDALONE_EDGE")
        
        # Test index.html served at /
        resp_ui = client.get("/")
        self.assertEqual(resp_ui.status_code, 200)
        
        # Test scenario execution
        resp_sc = client.post("/api/v1/scenarios/D/execute")
        self.assertEqual(resp_sc.status_code, 200)
        data = resp_sc.json()
        self.assertEqual(data["actual_result"]["member5_active_alert"]["severity"], "RED")
        
        # Test ground summary
        resp_gr = client.get("/api/v1/ground/report")
        self.assertEqual(resp_gr.status_code, 200)
        self.assertIn("total_packets_received", resp_gr.json())


if __name__ == "__main__":
    unittest.main()
