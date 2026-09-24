"""
Member 3: HADR Decision Support & Evacuation Routing Engine
Classifies road network passability, evaluates critical infrastructure risk,
and identifies safe evacuation corridors to designated relief shelters.
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from shapely.geometry import Point, LineString, mapping
from jal_drishti.config import INDIAN_BASINS

class HADRDecisionEngine:
    """
    HADR scenario planning, evacuation routing, and critical infrastructure risk analysis.
    """

    @staticmethod
    def evaluate_critical_infrastructure(
        basin_id: str,
        depth_grid: np.ndarray,
        basin_bbox: List[float]
    ) -> List[Dict[str, Any]]:
        """
        Assesses operational vulnerability of hospitals, power plants, bridges, and shelters.
        """
        basin_info = INDIAN_BASINS.get(basin_id, {})
        infra_list = basin_info.get("critical_infrastructure", [])
        min_lon, min_lat, max_lon, max_lat = basin_bbox
        nx, ny = depth_grid.shape

        results = []
        for item in infra_list:
            lat, lon = item["coords"]

            # Map lat/lon to grid indices
            norm_x = (lon - min_lon) / max(1e-5, (max_lon - min_lon))
            norm_y = (max_lat - lat) / max(1e-5, (max_lat - min_lat))

            i = int(np.clip(norm_x * (nx - 1), 0, nx - 1))
            j = int(np.clip(norm_y * (ny - 1), 0, ny - 1))

            local_depth = float(depth_grid[i, j])

            if local_depth >= 1.2:
                status = "CRITICAL_DANGER"
                urgency = "IMMEDIATE_AIR_EVACUATION"
                color = "#ef4444"
            elif local_depth >= 0.35:
                status = "SUBMERGED"
                urgency = "BOATS_AND_PUMPS_REQUIRED"
                color = "#f97316"
            elif local_depth >= 0.05:
                status = "ACCESS_THREATENED"
                urgency = "DEPLOY_SANDBAG_DEFENSE"
                color = "#eab308"
            else:
                status = "OPERATIONAL_SAFE"
                urgency = "STAGING_AREA_ACTIVE"
                color = "#22c55e"

            results.append({
                "id": item["id"],
                "name": item["name"],
                "type": item["type"],
                "coords": [lat, lon],
                "elevation_m": item["elevation"],
                "inundation_depth_m": round(local_depth, 2),
                "status": status,
                "urgency_action": urgency,
                "badge_color": color
            })

        return results

    @staticmethod
    def generate_evacuation_routes_geojson(
        basin_id: str,
        depth_grid: np.ndarray,
        basin_bbox: List[float]
    ) -> Dict[str, Any]:
        """
        Generates road network polylines classified by flood inundation:
        - Safe evacuation corridors (Green)
        - Cautionary flooded roads (Yellow)
        - Submerged/Impassable roads (Red)
        """
        min_lon, min_lat, max_lon, max_lat = basin_bbox
        basin_info = INDIAN_BASINS.get(basin_id, {})
        shelters = basin_info.get("relief_shelters", [])

        # Generate realistic primary transport routes through the river valley
        routes = []
        lons = np.linspace(min_lon + 0.02, max_lon - 0.02, 12)
        center_lat = (min_lat + max_lat) / 2.0

        # Primary highway along riverbank
        road_1_pts = []
        for lon in lons:
            lat = center_lat + 0.015 * np.sin((lon - min_lon) * 20.0)
            road_1_pts.append((lon, lat))
        routes.append(("Main River Arterial Highway", road_1_pts))

        # Secondary high-ground bypass
        road_2_pts = []
        for lon in lons:
            lat = center_lat + 0.035 + 0.008 * np.cos((lon - min_lon) * 15.0)
            road_2_pts.append((lon, lat))
        routes.append(("High-Ground Ridge Relief Bypass", road_2_pts))

        # Evacuation spur roads leading to shelters
        for idx, sh in enumerate(shelters):
            sh_lat, sh_lon = sh["coords"]
            spur_pts = [
                (sh_lon - 0.03, sh_lat - 0.02),
                (sh_lon - 0.015, sh_lat - 0.005),
                (sh_lon, sh_lat)
            ]
            routes.append((f"Evacuation Corridor to {sh['name']}", spur_pts))

        features = []
        nx, ny = depth_grid.shape

        for road_name, pts in routes:
            # Sample flood depth along road
            max_road_depth = 0.0
            for lon, lat in pts:
                norm_x = (lon - min_lon) / max(1e-5, (max_lon - min_lon))
                norm_y = (max_lat - lat) / max(1e-5, (max_lat - min_lat))
                i = int(np.clip(norm_x * (nx - 1), 0, nx - 1))
                j = int(np.clip(norm_y * (ny - 1), 0, ny - 1))
                max_road_depth = max(max_road_depth, float(depth_grid[i, j]))

            if max_road_depth >= 0.35:
                condition = "SUBMERGED_CLOSED"
                color = "#dc2626"
                desc = "Impassable for vehicular transit. Severe risk."
            elif max_road_depth >= 0.05:
                condition = "CAUTION_HEAVY_VEHICLES_ONLY"
                color = "#f59e0b"
                desc = "Water on road (5-35 cm). Proceed with extreme caution."
            else:
                condition = "SAFE_EVACUATION_CORRIDOR"
                color = "#10b981"
                desc = "Clear high-ground route recommended for population evacuation."

            line = LineString(pts)
            features.append({
                "type": "Feature",
                "properties": {
                    "road_name": road_name,
                    "condition": condition,
                    "max_depth_m": round(max_road_depth, 2),
                    "stroke_color": color,
                    "stroke_width": 4 if condition == "SAFE_EVACUATION_CORRIDOR" else 3,
                    "description": desc
                },
                "geometry": mapping(line)
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }
