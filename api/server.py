"""
MAITRI Offline Edge REST & WebSocket API Server
Exposes multimodal ingestion, live telemetry, dialogue companions, and ground station streams.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import SYSTEM_NAME, SYSTEM_VERSION, STATION_ID, MISSION_NAME
from member4_fusion.maitri_core import MaitriCore
from member5_ground_telemetry.emergency_scenarios import EmergencyScenarioGenerator

app = FastAPI(
    title="MAITRI Edge API",
    description="Multimodal AI Assistant for Psychological & Physical Well-Being of Astronauts",
    version=SYSTEM_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Instantiate core engine
core = MaitriCore(astronaut_id="ASTRO-01-RAKESH")


class MultimodalIngestRequest(BaseModel):
    # Member 1 Visual parameters
    simulated_ear: Optional[float] = Field(0.30, ge=0.0, le=1.0)
    simulated_mar: Optional[float] = Field(0.15, ge=0.0, le=2.0)
    simulated_brow: Optional[float] = Field(0.50, ge=0.0, le=1.0)
    simulated_jaw: Optional[float] = Field(0.22, ge=0.0, le=1.0)
    head_pitch: Optional[float] = 0.0
    head_roll: Optional[float] = 0.0
    # Member 2 Audio parameters
    simulated_pitch: Optional[float] = 138.0
    simulated_jitter: Optional[float] = 0.014
    simulated_shimmer: Optional[float] = 0.032
    transcript: Optional[str] = "Routine orbital check-in. Systems nominal."
    duration_sec: Optional[float] = 3.0
    # Member 3 Task Situation
    situation_key: Optional[str] = "NOMINAL_ROUTINE"
    is_operational_task: Optional[bool] = True


@app.get("/")
def get_root_or_ui():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return get_system_status()


@app.get("/api/status")
def get_system_status():
    return {
        "system": SYSTEM_NAME,
        "version": SYSTEM_VERSION,
        "station_id": STATION_ID,
        "mission": MISSION_NAME,
        "status": "ONLINE_STANDALONE_EDGE",
        "active_leads": [
            "Member 1: Computer Vision & Fatigue (EAR/MAR/PERCLOS/Micro-exp)",
            "Member 2: Audio & Speech Analysis (DSP Pitch/Jitter/Shimmer/SER/STT)",
            "Member 3: Conversational AI & Psychological Support (CBT/REBT/Box-Breathing/Offline-LLM)",
            "Member 4: Multimodal Fusion & Edge Core (AWBI Indexer/Low-Latency)",
            "Member 5: Ground Telemetry & Alert Protocol (CCSDS/CRC32/ISTRAC Alert)",
            "Member 6: Space Cockpit UI & JARVIS Voice Assistant",
        ],
    }


@app.post("/api/v1/analyze/multimodal")
def process_multimodal_feed(req: MultimodalIngestRequest):
    """
    Process incoming audio-visual telemetry through Member 1 -> Member 2 -> Member 4 -> Member 3 -> Member 5.
    """
    res = core.process_multimodal_step(
        simulated_ear=req.simulated_ear,
        simulated_mar=req.simulated_mar,
        simulated_brow=req.simulated_brow,
        simulated_jaw=req.simulated_jaw,
        head_pitch=req.head_pitch or 0.0,
        head_roll=req.head_roll or 0.0,
        simulated_pitch=req.simulated_pitch,
        simulated_jitter=req.simulated_jitter,
        simulated_shimmer=req.simulated_shimmer,
        transcript=req.transcript,
        audio_duration_sec=req.duration_sec or 3.0,
        situation_key=req.situation_key or "NOMINAL_ROUTINE",
        is_operational_task=req.is_operational_task if req.is_operational_task is not None else True,
    )
    return res


@app.get("/api/v1/telemetry/live")
def get_live_telemetry():
    context = core.edge_runtime.get_latest_context()
    if not context:
        # Generate initial nominal cycle
        res = core.process_multimodal_step()
        return res["member4_fusion_context"]
    return context.model_dump()


@app.get("/api/v1/telemetry/history")
def get_telemetry_history(count: int = 50):
    return core.edge_runtime.get_telemetry_history(count=count)


@app.get("/api/v1/ground/alerts")
def get_ground_alerts(count: int = 15):
    return core.ground_logger.get_latest_alerts(count=count)


@app.get("/api/v1/ground/report")
def get_ground_report():
    return core.ground_logger.generate_ground_summary_report()


@app.get("/api/v1/edge/health")
def get_edge_health():
    return core.edge_runtime.get_runtime_health()


@app.post("/api/v1/scenarios/{scenario_id}/execute")
def execute_scenario(scenario_id: str):
    scenarios = {
        "A": EmergencyScenarioGenerator.get_scenario_nominal(),
        "B": EmergencyScenarioGenerator.get_scenario_eva_fatigue(),
        "C": EmergencyScenarioGenerator.get_scenario_sleep_deprivation(),
        "D": EmergencyScenarioGenerator.get_scenario_hypoxia_panic(),
    }
    
    key = scenario_id.upper().replace("SCENARIO_", "")
    scenario = scenarios.get(key)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found. Use A, B, C, or D.")
        
    v = scenario["visual_inputs"]
    a = scenario["audio_inputs"]
    
    result = core.process_multimodal_step(
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
        situation_key=scenario["situation_key"],
    )
    
    return {
        "scenario_name": scenario["name"],
        "expected_severity": scenario["expected_alert_severity"],
        "actual_result": result,
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            context = core.edge_runtime.get_latest_context()
            if context:
                await websocket.send_json(context.model_dump())
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
