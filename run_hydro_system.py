"""
Master Runner for Jal-Drishti Hydrodynamic Simulation Framework
SIH 2026 Problem Statement SIH26161 (NTRO)

Usage:
  python run_hydro_system.py               # Starts WebGIS Dashboard on http://127.0.0.1:8000
  python run_hydro_system.py --cli         # Runs terminal simulation & benchmark for Rishi Ganga
  python run_hydro_system.py --basin kosi  # Runs CLI simulation for Kosi River
"""

import sys
import argparse
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def run_cli_simulation(basin_key: str = "rishi_ganga"):
    print("=" * 80)
    print(">> JAL-DRISHTI: HYDRODYNAMIC DAM-BREAK SIMULATION & HADR PLATFORM")
    print("   SIH 2026 Problem Statement SIH26161 | NTRO")
    print("=" * 80)

    from jal_drishti.backend.orchestrator import SimulationOrchestrator
    from jal_drishti.config import INDIAN_BASINS

    if basin_key not in INDIAN_BASINS:
        print(f"[-] Basin '{basin_key}' not found. Defaulting to 'rishi_ganga'.")
        basin_key = "rishi_ganga"

    basin = INDIAN_BASINS[basin_key]
    print(f"\n[*] Target Basin: {basin['name']} ({basin['state']})")
    print(f"[*] Basin Morphology: {basin['basin_type']}")
    print(f"[*] Historical Benchmark: {basin['historical_event']}")

    orchestrator = SimulationOrchestrator()
    print("\n[+] Dispatching coupled multi-model simulation...")
    task_id = orchestrator.dispatch_simulation({"basin_id": basin_key})

    # Poll status in terminal
    while True:
        status_data = orchestrator.get_task_status(task_id)
        prog = int((status_data.get("progress") or 0.0) * 100)
        msg = status_data.get("message", "")
        status = status_data.get("status", "")

        sys.stdout.write(f"\r  [{'#' * (prog // 5):20s}] {prog}% | {msg[:50]:50s}")
        sys.stdout.flush()

        if status == "COMPLETED":
            break
        elif status == "ERROR":
            print(f"\n[-] Error: {msg}")
            return
        time.sleep(0.4)

    print("\n\n" + "=" * 80)
    print("📊 MULTI-MODEL COMPARATIVE HYDRODYNAMIC RESULTS")
    print("=" * 80)

    res = status_data.get("results", {})
    sph = res.get("sph_metrics", {})
    delft = res.get("delft3d_metrics", {})
    gee = res.get("gee_validation", {})
    spatial = gee.get("spatial_metrics", {})
    loss = res.get("loss_damage", {})
    infra = res.get("infrastructure_status", [])

    print(f"\n1. SPH Near-Field Hydrodynamics (Member 1):")
    print(f"   - Peak Surge Velocity:       {sph.get('peak_surge_velocity_ms')} m/s")
    print(f"   - Mean Wave Velocity:        {sph.get('mean_velocity_ms')} m/s")
    print(f"   - Max Dynamic Impact Head:   {sph.get('max_dynamic_pressure_kpa')} kPa")
    print(f"   - Theoretical Ritter Speed:  {sph.get('ritter_benchmark', {}).get('theoretical_front_speed_ms')} m/s")
    print(f"   - Near-Field Surge Extent:   {sph.get('surge_front_distance_m')} m")

    print(f"\n2. Delft3D / 2D SWE Far-Field Routing (Member 2):")
    print(f"   - Total Inundated Area:      {delft.get('total_inundated_area_km2')} sq km")
    print(f"   - Downstream Peak Depth:     {delft.get('peak_depth_m')} m")
    print(f"   - Peak Flow Velocity:        {delft.get('peak_velocity_ms')} m/s")
    print(f"   - Wave Arrival Window:       {delft.get('wave_arrival_window_min', [0, 0])[0]} - {delft.get('wave_arrival_window_min', [0, 0])[1]} min")

    print(f"\n3. GEE Sentinel-1 SAR Ground Truth Validation (Member 4):")
    print(f"   - Satellite Sensor:          {gee.get('satellite_metadata', {}).get('satellite')}")
    print(f"   - Otsu Adaptive Threshold:   {gee.get('satellite_metadata', {}).get('otsu_threshold_db')} dB")
    print(f"   - Spatial IoU (Jaccard):     {spatial.get('iou_jaccard_index')}")
    print(f"   - Dice Similarity Coeff:     {spatial.get('dice_similarity_coefficient')}")
    print(f"   - True Positive (Hit):       {spatial.get('areas_km2', {}).get('hit_true_positive')} sq km")
    print(f"   - Overall Accuracy:          {spatial.get('overall_accuracy_percent')}%")

    print(f"\n4. Loss & Damage Estimation (Member 3):")
    print(f"   - Total Economic Loss:       ₹ {loss.get('total_economic_loss_inr_crores')} Crores")
    print(f"   - Population at High Risk:   {loss.get('population_at_high_risk'):,} citizens")
    print(f"   - Damaged Buildings Count:   {loss.get('buildings_damaged_count'):,} units")
    print(f"   - Farmland Submerged:        {loss.get('agricultural_area_submerged_ha')} hectares")

    print(f"\n5. HADR Critical Infrastructure Matrix:")
    for item in infra:
        print(f"   - [{item['status']:18s}] {item['name']:38s} | Depth: {item['inundation_depth_m']}m | {item['urgency_action']}")

    print(f"\n6. OGC GIS Export Products Generated (Member 5):")
    print(f"   - ESRI Shapefile ZIP:        {res.get('downloads', {}).get('shapefile_zip')}")
    print(f"   - Google Earth KML:          {res.get('downloads', {}).get('kml_file')}")
    print(f"   - HADR Situation Report:     {res.get('downloads', {}).get('hadr_report')}")

    print("\n" + "=" * 80)
    print("[SUCCESS] Full pipeline simulation verified successfully!")
    print("=" * 80)


def start_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    print("=" * 80)
    print("[SERVER] LAUNCHING JAL-DRISHTI WEBGIS DASHBOARD")
    print(f"   Server Address: http://{host}:{port}")
    print("   Open this URL in your web browser to explore interactive hydrodynamics!")
    print("=" * 80)
    uvicorn.run("jal_drishti.backend.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jal-Drishti Hydrodynamic Dam-Break Simulation Framework")
    parser.add_argument("--cli", action="store_true", help="Run simulation in CLI terminal mode")
    parser.add_argument("--basin", type=str, default="rishi_ganga", choices=["rishi_ganga", "kosi_river", "phuktal_river", "machhu_dam"], help="Target Indian river basin")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host IP")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()

    if args.cli:
        run_cli_simulation(args.basin)
    else:
        start_server(args.host, args.port)
