# 🌌 MAITRI: Multimodal AI Assistant for Psychological & Physical Well-Being of Astronauts

**MAITRI** (Multimodal AI Assistant for Psychological & Physical Well-Being of Astronauts) is an edge-optimized, offline-first multimodal AI companion engineered for the **Bharatiya Antariksh Station (BAS)** and **ISRO spaceflight missions**.

MAITRI provides continuous non-intrusive monitoring of astronaut physical fatigue and emotional equilibrium, provides evidence-based psychological support (CBT, Box-Breathing, Grounding), and autonomously downlinks space-grade CCSDS telemetry packets and alerts to Ground Control (ISTRAC/TMC).

---

## 🚀 Architecture & 5-Member Core Systems

```
maitri/
├── config/
│   ├── settings.py               # Spaceflight thresholds, APID, sample rates, AWBI boundaries
│   └── schemas.py                # Pydantic data contracts for all 5 subsystems
│
├── member1_cv/                   # Member 1: Computer Vision & Physical Fatigue
│   ├── facial_emotion.py         # Lightweight offline facial emotion recognition (FER)
│   ├── fatigue_detector.py       # Eye Aspect Ratio (EAR), PERCLOS, Blink Rate, MAR Yawn, Head Droop
│   ├── micro_expression.py       # Brow furrow, jaw tension & localized strain dynamics
│   └── vision_pipeline.py        # Central CV pipeline outputting VisualStateData
│
├── member2_audio/                # Member 2: Audio & Speech Analysis
│   ├── acoustic_features.py      # DSP F0 Pitch, Jitter, Shimmer, HNR, MFCCs, Spectral Centroid
│   ├── voice_emotion.py          # Speech Emotion Recognition (SER) & Vocal Strain Score (0-100)
│   ├── speech_to_text.py         # Offline STT & Spaceflight Emergency Keyword Spotting
│   └── audio_pipeline.py         # Central Audio pipeline outputting AudioStateData
│
├── member3_nlp_cbt/              # Member 3: Conversational AI & Psychological Support
│   ├── psychological_engine.py   # Space Psychology Protocols (Box Breathing, 4-7-8, 5-4-3-2-1, CBT)
│   ├── situation_templates.py    # Operational Situation Templates (EVA, Docking, Sleep Deprivation)
│   ├── offline_llm_client.py     # Offline LLM connector (Ollama) + Standalone Neurosymbolic Engine
│   └── dialogue_manager.py       # Adaptive brief conversational turn orchestrator
│
├── member4_fusion/               # Member 4: Fusion & Edge Integration
│   ├── wellbeing_indexer.py      # Astronaut Well-Being Index (AWBI: 0-100), Stress & Fatigue Indices
│   ├── multimodal_fusion.py      # Late + Early Cross-Modal Fusion & Conflict Detection
│   ├── edge_runtime.py           # Offline memory ring-buffers, Latency tracking (<100ms budget)
│   └── maitri_core.py            # Central Orchestrator binding Members 1, 2, 3, 4, 5
│
├── member5_ground_telemetry/     # Member 5: Ground Telemetry & Alert System
│   ├── alert_engine.py           # Multi-tier Alert Classifier (GREEN, YELLOW, ORANGE, RED)
│   ├── telemetry_protocol.py     # Space CCSDS Packet Framing, Hex Serializer, CRC-32 Checksum
│   ├── emergency_scenarios.py    # Deterministic mission emergency test generators
│   └── ground_station_logger.py  # ISTRAC Ground Control Telemetry Logger & Mission Reports
│
├── api/
│   └── server.py                 # FastAPI REST & WebSocket streaming server
├── data/
│   └── test_assets.py            # Synthetic audio waveform & facial frame generators
├── tests/
│   └── test_all_members.py       # 13 automated unit & integration test suites
├── cli_demo.py                   # Interactive ASCII telemetry terminal dashboard
├── run_emergency_sim.py          # Automated mission scenario execution & verification suite
└── requirements.txt              # Zero-cloud offline dependencies
```
risk.
