"""
MAITRI Interactive Command Line Interface (CLI)
Astronaut Well-Being Companion & ISRO Ground Telemetry Console
"""

import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from member4_fusion.maitri_core import MaitriCore
from member5_ground_telemetry.emergency_scenarios import EmergencyScenarioGenerator


def render_ascii_bar(label: str, value: float, max_val: float = 100.0, width: int = 25) -> str:
    filled = int((min(value, max_val) / max_val) * width)
    empty = width - filled
    bar = "#" * filled + "-" * empty
    return f"{label:<16} [{bar}] {value:>5.1f}%"


def main():
    core = MaitriCore(astronaut_id="ASTRO-01-RAKESH")
    
    print("\n" + "=" * 75)
    print("  [*] MAITRI: MULTIMODAL ASTRONAUT WELL-BEING ASSISTANT")
    print("  Bharatiya Antariksh Station (BAS) | ISRO Standalone Edge System")
    print("=" * 75)
    print("  1. Run Scenario A: Nominal Orbital Routine (Green)")
    print("  2. Run Scenario B: Extended Spacewalk EVA Fatigue (Yellow/Orange)")
    print("  3. Run Scenario C: 36h Sleep Deprivation Docking Slump (Orange)")
    print("  4. Run Scenario D: Critical Hypoxia / Panic Event (Red Escalation)")
    print("  5. Custom Utterance & Telemetry Ingestion")
    print("  6. Run Full Autonomous Verification Cycle")
    print("  0. Exit")
    print("-" * 75)

    scenarios = EmergencyScenarioGenerator.get_all_scenarios()
    
    # Check if an argument was passed on command line
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        _execute_choice(choice, core, scenarios)
        return

    # Interactive Loop
    while True:
        try:
            choice = input("\nSelect an option (1-6, or 0 to exit): ").strip()
            if not choice:
                continue
            if choice == "0":
                print("Exiting MAITRI console. Stay safe in orbit.")
                break
            _execute_choice(choice, core, scenarios)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting MAITRI console.")
            break


def _execute_choice(choice: str, core: MaitriCore, scenarios):
    if choice in ["1", "2", "3", "4"]:
        idx = int(choice) - 1
        sc = scenarios[idx]
        v = sc["visual_inputs"]
        a = sc["audio_inputs"]
        print(f"\n[*] Running {sc['name']}...")
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
        display_cycle_results(res)

    elif choice == "5":
        try:
            custom_text = input("Enter astronaut speech / status text: ").strip()
            if not custom_text:
                custom_text = "Checking station cupola window and air circulation."
        except Exception:
            custom_text = "Checking station cupola window and air circulation."
            
        print(f"\n[*] Processing custom input: \"{custom_text}\"...")
        res = core.process_multimodal_step(
            transcript=custom_text,
            simulated_ear=0.25,
            simulated_mar=0.22,
            simulated_brow=0.35,
            simulated_pitch=145.0,
            simulated_jitter=0.022,
            situation_key="NOMINAL_ROUTINE",
        )
        display_cycle_results(res)

    elif choice == "6":
        from run_emergency_sim import run_all_simulations
        run_all_simulations()
    else:
        print(f"Unknown option '{choice}'. Please enter 1, 2, 3, 4, 5, 6, or 0.")


def display_cycle_results(res):
    m1 = res["member1_visual_state"]
    m2 = res["member2_audio_state"]
    m3 = res["member3_dialogue"]
    m4 = res["member4_fusion_context"]
    m5 = res["member5_active_alert"]
    pkt = res["member5_telemetry_packet"]

    print("\n" + "+" + "=" * 73 + "+")
    print(f"|  MAITRI TELEMETRY CONSOLE | TIME: {time.strftime('%H:%M:%S', time.gmtime(res['cycle_timestamp']))} UTC | STATUS: {m5['severity']:<7} |")
    print("+" + "=" * 73 + "+")
    print(f"|  AWBI (Well-Being): {m4['awbi_score']:>5.1f}/100  | Status: {m4['psychological_balance']:<16}               |")
    print(f"|  {render_ascii_bar('AWBI Index', m4['awbi_score'])}        |")
    print(f"|  {render_ascii_bar('Stress Index', m4['stress_index'])}        |")
    print(f"|  {render_ascii_bar('Fatigue Index', m4['fatigue_index'])}        |")
    print(f"|  {render_ascii_bar('Cognitive Load', m4['cognitive_load_index'])}        |")
    print("+" + "-" * 73 + "+")
    print(f"|  [CV] Facial Emotion: {m1['primary_emotion'].upper():<10} | PERCLOS: {m1['fatigue_metrics']['perclos']*100:>4.1f}% | Blink: {m1['fatigue_metrics']['blink_rate_bpm']:>4.1f} bpm |")
    print(f"|  [AUD] Vocal Tone   : {m2['audio_emotion'].upper():<10} | Pitch: {m2['acoustic_features']['f0_pitch_hz']:>5.1f} Hz | Jitter: {m2['acoustic_features']['jitter_local']*100:>4.2f}%   |")
    print(f"|  [AUD] Transcript   : \"{m2['transcript'][:50]:<50}\" |")
    print("+" + "-" * 73 + "+")
    print(f"|  [MAITRI COMPANION]                                                     |")
    print(f"|  Protocol: {m3.get('intervention', {}).get('protocol_name', 'None'):<60} |")
    print(f"|  Reply   : \"{m3['text'][:60]:<60}\" |")
    print("+" + "-" * 73 + "+")
    print(f"|  [GROUND ALERT] [{m5['severity']}] {m5['title'][:55]:<55} |")
    print(f"|  CCSDS Frame: {pkt['packet_id']} | APID: 0x03A5 | CRC-32: {pkt['crc32_checksum']}          |")
    print(f"|  Edge Latency: {res['total_execution_latency_ms']:>5.2f} ms (<100ms offline budget)                           |")
    print("+" + "=" * 73 + "+\n")


if __name__ == "__main__":
    main()
