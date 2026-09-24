"""
Member 1: SPH Hydrodynamic Metrics & Near-Field Envelope Extraction
Calculates peak surge velocity, dynamic impact pressure, wave arrival times,
and near-field GeoJSON polygon boundaries.
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from shapely.geometry import Point, MultiPoint, Polygon, mapping
from shapely.ops import unary_union
from .particle_generator import ParticleSystem

class SPHMetricsCalculator:
    """
    Computes diagnostic metrics and GIS polygons from SPH particle data.
    """

    @staticmethod
    def calculate_theoretical_ritter(h0: float, g: float = 9.81) -> Dict[str, float]:
        """
        Ritter's analytical solution for instantaneous dam break:
        v_front = 2 * sqrt(g * h0)
        c0 = sqrt(g * h0)
        q_max = (8/27) * h0 * sqrt(g * h0)
        """
        c0 = np.sqrt(g * h0)
        v_front = 2.0 * c0
        unit_q_max = (8.0 / 27.0) * h0 * c0
        return {
            "theoretical_front_speed_ms": round(float(v_front), 2),
            "critical_celerity_ms": round(float(c0), 2),
            "peak_unit_discharge_m2s": round(float(unit_q_max), 2)
        }

    @staticmethod
    def extract_near_field_metrics(
        system: ParticleSystem,
        dam_height_m: float,
        water_depth_m: float,
        run_duration_s: float
    ) -> Dict[str, Any]:
        """
        Calculates near-field hydrodynamic impact metrics.
        """
        fluid_idx = system.fluid_indices
        if len(fluid_idx) == 0:
            return {"status": "no_active_particles"}

        pos = system.positions[fluid_idx]
        vel = system.velocities[fluid_idx]
        press = system.pressures[fluid_idx]

        v_mag = np.linalg.norm(vel, axis=1)
        max_vel = float(np.max(v_mag))
        mean_vel = float(np.mean(v_mag))

        # Dynamic impact pressure: P_dyn = 0.5 * rho * v^2 + P_stat
        dyn_press_kpa = (0.5 * 1000.0 * (v_mag ** 2) + press) / 1000.0
        max_impact_kpa = float(np.max(dyn_press_kpa))

        # Downstream surge front position (maximum positive x)
        downstream_particles = pos[pos[:, 0] > 0]
        surge_extent_m = float(np.max(downstream_particles[:, 0])) if len(downstream_particles) > 0 else 0.0

        # Front velocity estimate
        front_speed_ms = surge_extent_m / max(0.1, run_duration_s)

        ritter = SPHMetricsCalculator.calculate_theoretical_ritter(water_depth_m)

        return {
            "model_type": "Smoothed Particle Hydrodynamics (WCSPH)",
            "peak_surge_velocity_ms": round(max_vel, 2),
            "mean_velocity_ms": round(mean_vel, 2),
            "max_dynamic_pressure_kpa": round(max_impact_kpa, 2),
            "surge_front_distance_m": round(surge_extent_m, 2),
            "measured_front_speed_ms": round(front_speed_ms, 2),
            "ritter_benchmark": ritter,
            "convergence_ratio": round(min(1.0, front_speed_ms / max(1e-3, ritter["theoretical_front_speed_ms"])), 3)
        }

    @staticmethod
    def generate_near_field_geojson(
        system: ParticleSystem,
        basin_center: List[float],
        basin_bbox: List[float],
        channel_length_m: float
    ) -> Dict[str, Any]:
        """
        Transforms local SPH fluid particle coordinates (meters) to geographic coordinates
        (WGS84 Lat/Lon) and generates a convex hull / buffered GeoJSON polygon.
        """
        fluid_idx = system.fluid_indices
        if len(fluid_idx) == 0:
            return {"type": "FeatureCollection", "features": []}

        pos = system.positions[fluid_idx]
        vel = system.velocities[fluid_idx]
        v_mag = np.linalg.norm(vel, axis=1)

        # Geographic scaling: 1 deg lat ~ 111,000 m; 1 deg lon ~ 111,000 * cos(lat)
        ref_lat, ref_lon = basin_center[0], basin_center[1]
        lat_scale = 1.0 / 111000.0
        lon_scale = 1.0 / (111000.0 * np.cos(np.radians(ref_lat)))

        # Convert downstream (x) and lateral (y) to lat/lon offsets
        # Flow runs primarily along the valley direction
        lats = ref_lat - (pos[:, 0] * lat_scale * 0.7)
        lons = ref_lon + (pos[:, 1] * lon_scale) + (pos[:, 0] * lon_scale * 0.3)

        # Clamp inside bbox
        min_lon, min_lat, max_lon, max_lat = basin_bbox
        lats = np.clip(lats, min_lat, max_lat)
        lons = np.clip(lons, min_lon, max_lon)

        # Create Shapely points and alpha shape / buffered polygon
        points = [Point(xy) for xy in zip(lons, lats)]
        mp = MultiPoint(points)
        hull = mp.convex_hull.buffer(0.001)

        feature = {
            "type": "Feature",
            "properties": {
                "model": "SPH",
                "layer": "Near-Field Wave Surge Envelope",
                "max_velocity_ms": round(float(np.max(v_mag)), 2),
                "particle_count": int(len(fluid_idx)),
                "color": "#ef4444",
                "fillOpacity": 0.45
            },
            "geometry": mapping(hull)
        }

        return {
            "type": "FeatureCollection",
            "features": [feature]
        }
