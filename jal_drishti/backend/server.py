"""
Member 5: FastAPI REST & Geospatial Streaming Server
Serves WebGIS UI, simulation execution APIs, layer streaming, and .shp/.kml file downloads.
"""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from jal_drishti.config import INDIAN_BASINS, STATIC_DIR, EXPORT_DIR
from jal_drishti.backend.orchestrator import SimulationOrchestrator

app = FastAPI(
    title="Jal-Drishti Hydrodynamic Dam-Break Simulation Framework",
    description="Dual Hydrodynamic (SPH vs Delft3D) Dam Break Inundation, GEE Satellite Validation & HADR Decision Support",
    version="1.0.0"
)

# Enable CORS for local and web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = SimulationOrchestrator()

# Pydantic Request Models
class SimulationRequest(BaseModel):
    basin_id: str = "rishi_ganga"
    dam_height_m: Optional[float] = None
    reservoir_volume_mcm: Optional[float] = None
    breach_width_m: Optional[float] = None
    breach_depth_m: Optional[float] = None
    breach_time_hrs: Optional[float] = None
    manning_n: Optional[float] = None
    sim_duration_hrs: Optional[float] = None

@app.get("/api/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": "Jal-Drishti Hydrodynamic Server",
        "active_basins_loaded": len(INDIAN_BASINS),
        "supported_models": ["Smoothed Particle Hydrodynamics (SPH)", "Delft3D (2D Saint-Venant SWE)"]
    }

@app.get("/api/basins")
async def get_basins():
    """Returns available Indian river basins, default parameters, and infrastructure."""
    return {"basins": INDIAN_BASINS}

@app.get("/api/basins/{basin_id}")
async def get_basin_detail(basin_id: str):
    if basin_id not in INDIAN_BASINS:
        raise HTTPException(status_code=404, detail="Basin ID not found")
    return INDIAN_BASINS[basin_id]

@app.post("/api/simulate")
async def start_simulation(req: SimulationRequest):
    """Dispatches background hydrodynamic simulation and returns task_id."""
    params = req.dict(exclude_none=True)
    task_id = orchestrator.dispatch_simulation(params)
    return {
        "status": "QUEUED",
        "task_id": task_id,
        "message": "Simulation dispatched to multi-model engine"
    }

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """Polls simulation progress."""
    return orchestrator.get_task_status(task_id)

@app.get("/api/results/{task_id}")
async def get_results(task_id: str):
    """Retrieves full simulation metrics, comparison data, and GeoJSON layers."""
    status = orchestrator.get_task_status(task_id)
    if status.get("status") == "COMPLETED" and "results" in status:
        return status["results"]
    elif status.get("status") == "ERROR":
        raise HTTPException(status_code=500, detail=status.get("message", "Simulation failed"))
    else:
        return status

@app.get("/api/export/shapefile/{task_id}")
async def download_shapefile(task_id: str):
    """Downloads ESRI Shapefile bundle (.shp, .shx, .dbf, .prj) as a ZIP archive."""
    # Find matching zip in export directory
    matching = list(EXPORT_DIR.glob(f"*{task_id}*shapefile.zip"))
    if not matching:
        raise HTTPException(status_code=404, detail="Shapefile not found for this task")
    file_path = matching[0]
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/zip"
    )

@app.get("/api/export/kml/{task_id}")
async def download_kml(task_id: str):
    """Downloads Google Earth OGC KML 2.2 file."""
    matching = list(EXPORT_DIR.glob(f"*{task_id}*.kml"))
    if not matching:
        raise HTTPException(status_code=404, detail="KML file not found for this task")
    file_path = matching[0]
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.google-earth.kml+xml"
    )

@app.get("/api/export/hadr-report/{task_id}")
async def download_hadr_report(task_id: str):
    """Downloads HADR situation report."""
    matching = list(EXPORT_DIR.glob(f"*{task_id}*.md"))
    if not matching:
        raise HTTPException(status_code=404, detail="HADR report not found")
    file_path = matching[0]
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="text/markdown"
    )

# Mount WebGIS Static Frontend
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Jal-Drishti API is running. Web interface static file not yet loaded."}
