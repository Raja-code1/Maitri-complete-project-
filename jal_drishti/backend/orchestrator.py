"""
Member 5: Master Simulation Orchestrator
Coordinates SPH near-field modeling, Delft3D far-field SWE routing, GEE SAR validation,
geospatial loss estimation, and HADR evacuation routing into an end-to-end pipeline.
"""

import uuid
import threading
import numpy as np
from typing import Dict, Any, Optional
from jal_drishti.config import INDIAN_BASINS
from jal_drishti.models_sph import SPHParticleGenerator, WCSPHSolver, SPHSimulationConfig, SPHMetricsCalculator
from jal_drishti.models_delft3d import SWE2DSolver, SWEGridConfig, FarFieldFloodRouter
from jal_drishti.gis_damage import DEMProcessor, LossDamageEngine, HADRDecisionEngine
from jal_drishti.gee_satellite import GEEClient, HydroModelValidator
from jal_drishti.backend.export_engine import GeospatialExportEngine
from jal_drishti.backend.tile_cache import TileCacheManager

class SimulationOrchestrator:
    """
    Asynchronous runner and coordinator for hydrodynamic simulation tasks.
    """

    def __init__(self):
        self.cache = TileCacheManager()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.gee_client = GEEClient(use_live_api=False)

    def dispatch_simulation(self, params: Dict[str, Any]) -> str:
        """
        Dispatches simulation in a background thread and returns task_id immediately.
        """
        task_id = str(uuid.uuid4())[:8]
        self.active_tasks[task_id] = {
            "task_id": task_id,
            "status": "RUNNING",
            "progress": 0.05,
            "message": "Initializing terrain topography and particle discretization...",
            "results": None
        }

        thread = threading.Thread(
            target=self._run_pipeline,
            args=(task_id, params),
            daemon=True
        )
        thread.start()
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Queries status of running or completed simulation.
        """
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        cached = self.cache.get_run(task_id)
        if cached:
            return {"task_id": task_id, "status": "COMPLETED", "progress": 1.0, "message": "Simulation Complete", "results": cached}
        return {"task_id": task_id, "status": "NOT_FOUND", "progress": 0.0, "message": "Unknown task ID"}

    def _run_pipeline(self, task_id: str, params: Dict[str, Any]) -> None:
        """
        Executes end-to-end multi-model hydrodynamic workflow.
        """
        try:
            basin_id = params.get("basin_id", "rishi_ganga")
            basin = INDIAN_BASINS.get(basin_id, INDIAN_BASINS["rishi_ganga"])
            dam_h = float(params.get("dam_height_m", basin["default_params"]["dam_height_m"]))
            res_vol = float(params.get("reservoir_volume_mcm", basin["default_params"]["reservoir_volume_mcm"]))
            breach_w = float(params.get("breach_width_m", basin["default_params"]["breach_width_m"]))
            breach_d = float(params.get("breach_depth_m", basin["default_params"]["breach_depth_m"]))
            manning_n = float(params.get("manning_n", basin["default_params"]["manning_n"]))
            sim_hrs = float(params.get("sim_duration_hrs", basin["default_params"]["sim_duration_hrs"]))

            bbox = basin["bbox"]

            # Step 1: Pre-process DEM Terrain (Member 3)
            self._update_task(task_id, 0.15, "Generating digital elevation model & filling sinks...")
            nx, ny = 60, 40
            dx, dy = 250.0, 250.0
            dem_zb = DEMProcessor.generate_basin_dem(basin_id=basin_id, nx=nx, ny=ny, dx=dx, dy=dy)
            slope_deg, flow_dir = DEMProcessor.compute_slope_and_flow_direction(dem_zb, dx, dy)

            # Step 2: Member 1 SPH Near-Field Simulation
            self._update_task(task_id, 0.35, "Executing SPH particle hydrodynamics (WCSPH solver)...")
            sph_gen = SPHParticleGenerator(dx=2.5)
            sph_system = sph_gen.generate_dam_break_scenario(
                reservoir_length=180.0,
                reservoir_width=120.0,
                water_depth=dam_h * 0.8,
                breach_width=breach_w * 0.4,
                channel_length=450.0,
                valley_slope=0.04,
                num_particles_target=1200
            )
            sph_cfg = SPHSimulationConfig(total_time=8.0, dt=0.015, snapshot_interval=0.8)
            sph_solver = WCSPHSolver(sph_cfg)
            sph_run = sph_solver.run_simulation(sph_system)

            sph_metrics = SPHMetricsCalculator.extract_near_field_metrics(
                system=sph_system,
                dam_height_m=dam_h,
                water_depth_m=dam_h * 0.8,
                run_duration_s=8.0
            )
            sph_geojson = SPHMetricsCalculator.generate_near_field_geojson(
                system=sph_system,
                basin_center=basin["center_coords"],
                basin_bbox=bbox,
                channel_length_m=450.0
            )

            # Step 3: Member 2 Delft3D Far-Field SWE Simulation
            self._update_task(task_id, 0.60, "Routing 2D Shallow Water Equations across catchment (Delft3D)...")
            swe_cfg = SWEGridConfig(nx=nx, ny=ny, dx=dx, dy=dy, manning_n=manning_n)
            swe_solver = SWE2DSolver(swe_cfg)
            t_s, q_s = swe_solver.generate_dam_breach_hydrograph(
                reservoir_vol_mcm=res_vol,
                dam_height_m=dam_h,
                breach_width_m=breach_w,
                breach_time_hrs=params.get("breach_time_hrs", basin["default_params"]["breach_time_hrs"]),
                total_sim_hrs=sim_hrs
            )
            swe_res = swe_solver.simulate(
                dem_zb=dem_zb,
                breach_x_idx=4,
                breach_y_idx=ny // 2,
                hydrograph_time_s=t_s,
                hydrograph_q_m3s=q_s,
                sim_duration_s=sim_hrs * 3600.0,
                dam_height_m=dam_h
            )

            depth_grid = swe_res["max_depth_grid"]
            vel_grid = swe_res["max_velocity_grid"]
            arrival_grid = swe_res["arrival_time_min"]

            delft3d_metrics = FarFieldFloodRouter.extract_routing_metrics(
                depth_grid=depth_grid,
                vel_grid=vel_grid,
                arrival_grid=arrival_grid,
                cell_dx=dx,
                cell_dy=dy
            )
            delft3d_geojson = FarFieldFloodRouter.generate_depth_contours_geojson(
                depth_grid=depth_grid,
                basin_bbox=bbox
            )
            velocity_vectors_geojson = FarFieldFloodRouter.generate_velocity_vectors_geojson(
                depth_grid=depth_grid,
                vel_grid=vel_grid,
                basin_bbox=bbox
            )

            # Step 4: Member 4 GEE Sentinel-1 SAR Validation
            self._update_task(task_id, 0.78, "Retrieving GEE Sentinel-1 SAR imagery & validating...")
            gee_res = self.gee_client.fetch_sentinel1_flood_pair(basin_id=basin_id, nx=nx, ny=ny)
            sim_water_mask = depth_grid > 0.08
            validation_metrics = HydroModelValidator.compute_spatial_agreement(
                simulated_mask=sim_water_mask,
                satellite_mask=gee_res["water_mask"],
                cell_dx=dx,
                cell_dy=dy
            )
            model_comparison = HydroModelValidator.compare_sph_vs_delft3d(
                sph_metrics=sph_metrics,
                delft_metrics=delft3d_metrics
            )

            # Step 5: Member 3 Geospatial Loss Assessment & HADR Routing
            self._update_task(task_id, 0.90, "Computing loss estimation & HADR evacuation routes...")
            loss_data = LossDamageEngine.calculate_losses(
                depth_grid=depth_grid,
                basin_id=basin_id,
                cell_dx=dx,
                cell_dy=dy
            )
            infra_status = HADRDecisionEngine.evaluate_critical_infrastructure(
                basin_id=basin_id,
                depth_grid=depth_grid,
                basin_bbox=bbox
            )
            evacuation_routes_geojson = HADRDecisionEngine.generate_evacuation_routes_geojson(
                basin_id=basin_id,
                depth_grid=depth_grid,
                basin_bbox=bbox
            )

            # Step 6: Member 5 Export Generation
            self._update_task(task_id, 0.96, "Generating standard .shp Shapefile ZIP & .kml files...")
            # Combine features for comprehensive export
            combined_export_geojson = {
                "type": "FeatureCollection",
                "features": delft3d_geojson.get("features", []) + sph_geojson.get("features", [])
            }
            shapefile_path = GeospatialExportEngine.export_shapefile_zip(
                geojson_data=combined_export_geojson,
                base_filename=f"{basin_id}_{task_id}"
            )
            kml_path = GeospatialExportEngine.export_kml(
                geojson_data=combined_export_geojson,
                scenario_title=f"{basin['name']} - Dam Break Simulation",
                base_filename=f"{basin_id}_{task_id}"
            )

            # Full result bundle
            final_payload = {
                "task_id": task_id,
                "basin_id": basin_id,
                "basin_name": basin["name"],
                "basin_state": basin["state"],
                "center_coords": basin["center_coords"],
                "bbox": bbox,
                "inputs": {
                    "dam_height_m": dam_h,
                    "reservoir_volume_mcm": res_vol,
                    "breach_width_m": breach_w,
                    "breach_depth_m": breach_d,
                    "manning_n": manning_n,
                    "sim_duration_hrs": sim_hrs
                },
                "sph_metrics": sph_metrics,
                "sph_snapshots": sph_run["snapshots"][:10], # First 10 key frames for UI animation
                "delft3d_metrics": delft3d_metrics,
                "gee_validation": {
                    "satellite_metadata": {
                        "satellite": gee_res["satellite"],
                        "polarization": gee_res["polarization"],
                        "acquisition_date": gee_res["acquisition_date"],
                        "otsu_threshold_db": gee_res["otsu_threshold_db"],
                        "observed_flood_area_km2": gee_res["observed_flood_area_km2"]
                    },
                    "spatial_metrics": validation_metrics
                },
                "model_comparison": model_comparison,
                "loss_damage": loss_data,
                "infrastructure_status": infra_status,
                "layers": {
                    "delft3d_contours": delft3d_geojson,
                    "sph_envelope": sph_geojson,
                    "velocity_vectors": velocity_vectors_geojson,
                    "gee_satellite_mask": gee_res["geojson"],
                    "evacuation_routes": evacuation_routes_geojson
                },
                "downloads": {
                    "shapefile_zip": f"/api/export/shapefile/{task_id}",
                    "kml_file": f"/api/export/kml/{task_id}",
                    "hadr_report": f"/api/export/hadr-report/{task_id}"
                }
            }

            # Generate HADR situation report
            GeospatialExportEngine.generate_hadr_executive_report(
                scenario_data=final_payload,
                base_filename=f"hadr_report_{task_id}"
            )

            # Save in tile cache
            self.cache.store_run(task_id, final_payload)
            self._update_task(task_id, 1.0, "Simulation successfully completed!", results=final_payload)
            self.active_tasks[task_id]["status"] = "COMPLETED"

        except Exception as e:
            import traceback
            err_msg = f"Simulation failed: {str(e)}\n{traceback.format_exc()}"
            self.active_tasks[task_id]["status"] = "ERROR"
            self.active_tasks[task_id]["message"] = err_msg

    def _update_task(self, task_id: str, progress: float, msg: str, results: Optional[Dict[str, Any]] = None):
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["progress"] = round(progress, 2)
            self.active_tasks[task_id]["message"] = msg
            if results:
                self.active_tasks[task_id]["results"] = results
