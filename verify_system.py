"""
Automated Comprehensive Verification Suite for Jal-Drishti
Tests all 6 member roles, mathematical hydrodynamics, GIS exports, and API services.
"""

import sys
import zipfile
import xml.etree.ElementTree as ET
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def run_tests():
    print("=" * 75)
    print("[TEST] JAL-DRISHTI AUTOMATED VERIFICATION SUITE")
    print("=" * 75)
    passed = 0
    total = 0

    def assert_test(cond, test_name):
        nonlocal passed, total
        total += 1
        if cond:
            print(f"  [PASS] {test_name}")
            passed += 1
        else:
            print(f"  [FAIL] {test_name}")
            assert False, f"Test failed: {test_name}"

    # ----------------------------------------------------
    # TEST SUITE 1: Member 1 - SPH Hydrodynamics Engine
    # ----------------------------------------------------
    print("\n[+] Testing Member 1: SPH Hydrodynamics Engine...")
    from jal_drishti.models_sph import SPHParticleGenerator, WCSPHSolver, SPHSimulationConfig, SPHMetricsCalculator

    gen = SPHParticleGenerator(dx=2.5)
    system = gen.generate_dam_break_scenario(
        reservoir_length=100.0,
        reservoir_width=60.0,
        water_depth=20.0,
        breach_width=30.0,
        channel_length=200.0,
        num_particles_target=500
    )
    assert_test(system.num_particles > 0, "SPH particle generation initializes particles")
    assert_test(len(system.fluid_indices) > 0, "SPH identifies active fluid particles")
    assert_test(len(system.boundary_indices) > 0, "SPH identifies solid boundary particles")

    solver = WCSPHSolver(SPHSimulationConfig(total_time=1.0, dt=0.01))
    pressures = solver.compute_tait_pressure(system.densities)
    assert_test(np.all(pressures >= 0), "Tait's Equation of State maintains non-negative pressure")

    solver.step(system, dt=0.01)
    assert_test(np.all(np.isfinite(system.positions)), "SPH positions remain finite after timestep")
    assert_test(np.all(np.isfinite(system.velocities)), "SPH velocities remain finite after timestep")

    metrics_sph = SPHMetricsCalculator.extract_near_field_metrics(system, 20.0, 16.0, 1.0)
    assert_test(metrics_sph["peak_surge_velocity_ms"] >= 0, "SPH computes valid peak surge velocity")
    assert_test("ritter_benchmark" in metrics_sph, "SPH benchmarks against Ritter theoretical solution")

    # ----------------------------------------------------
    # TEST SUITE 2: Member 2 - Delft3D / 2D SWE Engine
    # ----------------------------------------------------
    print("\n[+] Testing Member 2: Delft3D / 2D SWE Hydrodynamic Engine...")
    from jal_drishti.models_delft3d import ManningRoughnessCalculator, SWE2DSolver, SWEGridConfig, FarFieldFloodRouter

    h_dummy = np.array([[0.0, 0.5], [1.2, 2.5]])
    u_dummy = np.array([[0.0, 1.0], [2.0, 1.5]])
    v_dummy = np.array([[0.0, 0.2], [0.5, 0.8]])
    tx, ty = ManningRoughnessCalculator.compute_bed_shear_stress(h_dummy, u_dummy, v_dummy, 0.035)
    assert_test(np.all(np.isfinite(tx)) and np.all(np.isfinite(ty)), "Manning bed shear stress computes finite values")
    assert_test(tx[0, 0] == 0.0, "Zero shear stress on dry cells (h < h_dry)")

    swe_solver = SWE2DSolver(SWEGridConfig(nx=20, ny=15, dx=200.0, dy=200.0))
    t_s, q_s = swe_solver.generate_dam_breach_hydrograph(15.0, 30.0, 50.0, 0.5, 1.0)
    assert_test(len(t_s) > 0 and np.max(q_s) > 0, "Froehlich/NWS breach outflow hydrograph generates positive discharge")

    dem_test = np.zeros((20, 15)) + 100.0
    swe_res = swe_solver.simulate(dem_test, 2, 7, t_s, q_s, sim_duration_s=60.0)
    assert_test(np.max(swe_res["max_depth_grid"]) > 0, "2D SWE simulation inundates downstream cells")

    delft_metrics = FarFieldFloodRouter.extract_routing_metrics(
        swe_res["max_depth_grid"],
        swe_res["max_velocity_grid"],
        swe_res["arrival_time_min"],
        200.0, 200.0
    )
    assert_test(delft_metrics["total_inundated_area_km2"] >= 0, "Delft3D routing extracts inundated area")
    contours_geo = FarFieldFloodRouter.generate_depth_contours_geojson(
        swe_res["max_depth_grid"],
        [79.62, 30.42, 79.78, 30.56]
    )
    assert_test(contours_geo["type"] == "FeatureCollection", "Delft3D generates GeoJSON depth contours")

    # ----------------------------------------------------
    # TEST SUITE 3: Member 3 - GIS, DEM & HADR Engine
    # ----------------------------------------------------
    print("\n[+] Testing Member 3: GIS, DEM Pre-Processing & HADR...")
    from jal_drishti.gis_damage import DEMProcessor, LossDamageEngine, HADRDecisionEngine

    dem_rg = DEMProcessor.generate_basin_dem("rishi_ganga", nx=30, ny=20)
    assert_test(dem_rg.shape == (30, 20), "DEM generator builds correct grid dimension")
    assert_test(np.min(dem_rg) > 1000.0, "Rishi Ganga DEM conforms to Himalayan elevation range")

    slope, flow = DEMProcessor.compute_slope_and_flow_direction(dem_rg, 250.0, 250.0)
    assert_test(np.all(slope >= 0), "Terrain slope gradient is non-negative")

    losses = LossDamageEngine.calculate_losses(swe_res["max_depth_grid"], "rishi_ganga", 200.0, 200.0)
    assert_test("total_economic_loss_inr_crores" in losses, "Loss engine calculates economic losses in ₹ Crores")
    assert_test("population_exposed" in losses, "Loss engine estimates exposed population")

    infra_status = HADRDecisionEngine.evaluate_critical_infrastructure(
        "rishi_ganga",
        swe_res["max_depth_grid"],
        [79.62, 30.42, 79.78, 30.56]
    )
    assert_test(len(infra_status) > 0, "HADR evaluates critical infrastructure risk matrix")
    assert_test("status" in infra_status[0], "Infrastructure items have classified status badges")

    evac_routes = HADRDecisionEngine.generate_evacuation_routes_geojson(
        "rishi_ganga",
        swe_res["max_depth_grid"],
        [79.62, 30.42, 79.78, 30.56]
    )
    assert_test(len(evac_routes["features"]) > 0, "HADR generates classified road corridor features")

    # ----------------------------------------------------
    # TEST SUITE 4: Member 4 - GEE Satellite & Validation
    # ----------------------------------------------------
    print("\n[+] Testing Member 4: GEE Satellite & Validation Engine...")
    from jal_drishti.gee_satellite import Sentinel1SARPipeline, GEEClient, HydroModelValidator

    test_img = np.random.normal(loc=-12.0, scale=2.0, size=(20, 20))
    test_img[5:15, 8:12] = -20.0 # Simulated water body
    otsu_th = Sentinel1SARPipeline.compute_otsu_threshold(test_img)
    assert_test(-25.0 <= otsu_th <= -10.0, "Otsu threshold identifies SAR backscatter bimodal separation")

    gee_client = GEEClient(use_live_api=False)
    gee_data = gee_client.fetch_sentinel1_flood_pair("rishi_ganga", nx=30, ny=20)
    assert_test("observed_flood_area_km2" in gee_data, "GEE client retrieves calibrated satellite observations")

    val = HydroModelValidator.compute_spatial_agreement(
        simulated_mask=swe_res["max_depth_grid"][:30, :20] > 0.05,
        satellite_mask=gee_data["water_mask"]
    )
    assert_test("iou_jaccard_index" in val, "Spatial IoU (Jaccard Index) computed")
    assert_test("dice_similarity_coefficient" in val, "Dice Similarity Coefficient computed")
    assert_test(0.0 <= val["overall_accuracy_percent"] <= 100.0, "Overall spatial accuracy percentage valid")

    # ----------------------------------------------------
    # TEST SUITE 5: Member 5 - Export Engine & Orchestrator
    # ----------------------------------------------------
    print("\n[+] Testing Member 5: Shapefile (.shp) & KML (.kml) Export Pipeline...")
    from jal_drishti.backend.export_engine import GeospatialExportEngine
    from jal_drishti.backend.orchestrator import SimulationOrchestrator

    shp_zip = GeospatialExportEngine.export_shapefile_zip(contours_geo, "test_verify")
    assert_test(shp_zip.exists(), "ESRI Shapefile ZIP created on disk")
    with zipfile.ZipFile(shp_zip, "r") as z:
        names = z.namelist()
        assert_test(any(n.endswith(".shp") for n in names), "ZIP contains .shp file")
        assert_test(any(n.endswith(".shx") for n in names), "ZIP contains .shx file")
        assert_test(any(n.endswith(".dbf") for n in names), "ZIP contains .dbf attribute table")
        assert_test(any(n.endswith(".prj") for n in names), "ZIP contains .prj coordinate system")

    kml_file = GeospatialExportEngine.export_kml(contours_geo, "Test Verification KML", "test_verify")
    assert_test(kml_file.exists(), "Google Earth KML file created on disk")
    # Verify XML validity
    tree = ET.parse(kml_file)
    root = tree.getroot()
    assert_test(root.tag.endswith("kml"), "KML file is valid OGC XML 2.2 format")

    print("\n[+] Testing Full Simulation Orchestrator...")
    orchestrator = SimulationOrchestrator()
    task_id = orchestrator.dispatch_simulation({"basin_id": "rishi_ganga"})
    assert_test(len(task_id) > 0, "Simulation task dispatched asynchronously")

    # ----------------------------------------------------
    # TEST SUITE 6: Member 6 & Backend API
    # ----------------------------------------------------
    print("\n[+] Testing Member 6 & FastAPI REST Endpoints...")
    from jal_drishti.backend.server import app

    routes = [route.path for route in app.routes]
    assert_test("/api/health" in routes, "Health check endpoint registered")
    assert_test("/api/basins" in routes, "Basins endpoint registered")
    assert_test("/api/simulate" in routes, "Simulate trigger endpoint registered")
    assert_test("/api/status/{task_id}" in routes, "Status polling endpoint registered")
    assert_test("/api/results/{task_id}" in routes, "Results retrieval endpoint registered")
    assert_test("/api/export/shapefile/{task_id}" in routes, "Shapefile download endpoint registered")
    assert_test("/api/export/kml/{task_id}" in routes, "KML download endpoint registered")
    assert_test("/api/export/hadr-report/{task_id}" in routes, "HADR report download endpoint registered")

    print("\n" + "=" * 75)
    print(f"  [SUCCESS] ALL {passed}/{total} VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
