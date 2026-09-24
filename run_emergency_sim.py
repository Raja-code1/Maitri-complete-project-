"""
MAITRI Automated Emergency Scenario Runner & Telemetry Verification Suite
Simulates 4 mission situations to validate Member 1, 2, 3, 4, and 5 integrations.
"""

import time
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from member4_fusion.maitri_core import MaitriCore
from member5_ground_telemetry.emergency_scenarios import EmergencyScenarioGenerator


def print_banner(text: str, char="="):
    print("\n" + char * 80)
    print(f" {text}")
    print(char * 80)


def run_all_simulations():
    print_banner("MAITRI: MULTIMODAL AI ASSISTANT FOR ASTRONAUT WELL-BEING - MISSION SIMULATOR")
    print("Bharatiya Antariksh Station (BAS) | ISRO Mission Control Simulation")
    print("Initializing offline edge core engine...\n")
    
    core = MaitriCore(astronaut_id="ASTRO-01-RAKESH")
    scenarios = EmergencyScenarioGenerator.get_all_scenarios()
    
    passed_scenarios = 0
    
    for idx, sc in enumerate(scenarios, 1):
        print_banner(f"TEST RUN {idx}/4: {sc['name'].upper()} [{sc['scenario_id']}]", char="-")
        print(f"Situation Context : {sc['situation_key']}")
        print(f"Astronaut Utterance: \"{sc['astronaut_utterance']}\"")
        
        v = sc["visual_inputs"]
        a = sc["audio_inputs"]
        
        # Execute unified multimodal cycle
        res = core.process_multimodal_step(
            simulated_ear=v["ear"],
            simulated_mar=v["mar"],
            simulated_brow=v["brow_ratio"],
            simulated_jaw=v["jaw_ratio"],
            head_pitch=v["head_pitch"],
            head_roll=v["head_roll"],
            simulated_pitch=a["pitch_hz"],
            simulated_jitter=a["jitter"],
            simulated_shimmer=a["shimmer"],
            transcript=a["transcript"],
            audio_duration_sec=a["duration_sec"],
            situation_key=sc["situation_key"],
        )
        
        m1 = res["member1_visual_state"]
        m2 = res["member2_audio_state"]
        m3 = res["member3_dialogue"]
        m4 = res["member4_fusion_context"]
        m5 = res["member5_active_alert"]
        pkt = res["member5_telemetry_packet"]
        
        print("\n" + "." * 70)
        print("  [MEMBER 1: VISION & FATIGUE OUTPUT]")
        print(f"    - Primary Emotion  : {m1['primary_emotion'].upper()} (conf: {m1['confidence']:.2f})")
        print(f"    - Fatigue Level    : {m1['fatigue_level'].upper()} (score: {m1['fatigue_score']}/100)")
        print(f"    - EAR: {m1['fatigue_metrics']['ear']:.2f} | MAR: {m1['fatigue_metrics']['mar']:.2f} | PERCLOS: {m1['fatigue_metrics']['perclos']*100:.1f}% | Blink: {m1['fatigue_metrics']['blink_rate_bpm']} bpm")
        print(f"    - Posture          : {m1['fatigue_metrics']['posture_stability'].upper()} (Head Pitch: {m1['fatigue_metrics']['head_pitch_deg']} deg)")
        print(f"    - Micro-Tension    : {m1['micro_expressions']['tension_score']:.2f} (Brow Furrow: {m1['micro_expressions']['brow_furrow']:.2f}, Jaw: {m1['micro_expressions']['jaw_clench']:.2f})")
        
        print("\n  [MEMBER 2: AUDIO & SPEECH OUTPUT]")
        print(f"    - Vocal Emotion    : {m2['audio_emotion'].upper()} (Valence: {m2['valence']}, Arousal: {m2['arousal']})")
        print(f"    - Vocal Strain     : {m2['vocal_strain_score']}/100")
        print(f"    - F0 Pitch         : {m2['acoustic_features']['f0_pitch_hz']} Hz | Jitter: {m2['acoustic_features']['jitter_local']*100:.2f}% | Shimmer: {m2['acoustic_features']['shimmer_local']*100:.2f}%")
        print(f"    - Speech Rate      : {m2['speech_rate_wpm']} WPM")
        
        print("\n  [MEMBER 4: MULTIMODAL FUSION & WELL-BEING]")
        print(f"    - AWBI Score       : {m4['awbi_score']:.1f} / 100 [{m4['psychological_balance']}]")
        print(f"    - Stress Index     : {m4['stress_index']:.1f} / 100")
        print(f"    - Fatigue Index    : {m4['fatigue_index']:.1f} / 100")
        print(f"    - Cognitive Load   : {m4['cognitive_load_index']:.1f} / 100")
        print(f"    - Cross Congruence : {m4['cross_modal_congruence']*100:.0f}%")
        if m4["dominant_concern"]:
            print(f"    - Dominant Concern : {m4['dominant_concern']}")
            
        print("\n  [MEMBER 3: PSYCHOLOGICAL NLP COMPANION]")
        intervention = m3.get("intervention") or {}
        print(f"    - Active Protocol  : {intervention.get('protocol_name', 'None')}")
        print(f"    - Guidance Reply   : \"{m3['text']}\"")
        if intervention.get("pacing_steps"):
            print(f"    - Protocol Step 1  : {intervention['pacing_steps'][0]}")
            
        print("\n  [MEMBER 5: GROUND TELEMETRY & ALERT ESCALATION]")
        print(f"    - Alert Severity   : [{m5['severity']}] {m5['title']}")
        print(f"    - Recommended Act. : {m5['recommended_action']}")
        print(f"    - Surgeon Notified : {m5['notified_flight_surgeon']} | Director Notified: {m5['notified_mission_director']}")
        print(f"    - CCSDS Packet ID  : {pkt['packet_id']} (APID: 0x03A5, Seq: {pkt['ccsds_header']['packet_sequence_count']})")
        print(f"    - CRC-32 Checksum  : {pkt['crc32_checksum']} (Hex Frame: {pkt['hex_payload'][:24]}...)")
        
        # Validate CRC-32 integrity
        crc_ok = core.telemetry_protocol.verify_packet_integrity(pkt["hex_payload"], pkt["crc32_checksum"])
        print(f"    - Telemetry Check  : {'PASS (Checksum Verified)' if crc_ok else 'FAIL'}")
        
        print(f"\n  [EDGE RUNTIME LATENCY]: {res['total_execution_latency_ms']} ms (Budget: <100 ms)")
        
        # Verify alert matches expected or safe escalation
        expected_sev = sc["expected_alert_severity"]
        actual_sev = m5["severity"]
        sev_rank = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
        if sev_rank[actual_sev] >= sev_rank[expected_sev]:
            print(f"\n  >>> RESULT: PASSED (Expected at least {expected_sev}, Triggered {actual_sev})")
            passed_scenarios += 1
        else:
            print(f"\n  >>> RESULT: FAILED (Expected {expected_sev}, Got {actual_sev})")
            
        time.sleep(0.05)

    print_banner(f"MISSION SIMULATION SUMMARY: {passed_scenarios}/{len(scenarios)} SCENARIOS PASSED")
    report = core.ground_logger.generate_ground_summary_report()
    print(f"Ground Station Report: {json.dumps(report, indent=2)}")
    print(f"Edge Runtime Health  : {json.dumps(core.edge_runtime.get_runtime_health(), indent=2)}")


if __name__ == "__main__":
    run_all_simulations()
