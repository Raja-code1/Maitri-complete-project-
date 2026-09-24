"""
Jal-Drishti System Configuration & Basin Presets
SIH 2026 Problem Statement SIH26161 (NTRO)
"""

from pathlib import Path
from typing import Dict, Any, List

# Base directories
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
EXPORT_DIR = BASE_DIR / "exports"
DATA_STORE_DIR = BASE_DIR / "data_store"

# Ensure directories exist
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
DATA_STORE_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Hydrodynamic Constants
GRAVITY = 9.81                   # m/s^2
WATER_DENSITY = 1000.0           # kg/m^3
KINEMATIC_VISCOSITY = 1e-6       # m^2/s
TAIT_GAMMA = 7.0                 # Tait's EOS exponent for water
SPH_C0_MULTIPLIER = 10.0         # Speed of sound c0 ~ 10 * vmax (WCSPH compressibility < 1%)
DEFAULT_MANNING_N = 0.038        # Natural winding stream with gravel/bed stones
WET_DRY_THRESHOLD = 0.01         # Minimum depth for wetting front (m)

# HADR Impact Categories (Flood Depth)
HADR_DEPTH_THRESHOLDS = {
    "NOMINAL": 0.05,       # Under 5 cm: safe/puddle
    "MILD_INUNDATION": 0.30, # 5 - 30 cm: pedestrian caution, light vehicles passable
    "MODERATE_HAZARD": 0.80, # 30 - 80 cm: vehicles submerged, ground floor flooded
    "HIGH_DANGER": 1.50,     # 80 cm - 1.5m: structural danger, evacuation mandatory
    "CATASTROPHIC": 3.00     # > 1.5m: structural collapse risk, aerial/boat rescue only
}

# Unit Economic Loss Estimates (in Crores INR per sq km at max depth)
ECONOMIC_LOSS_FACTORS = {
    "residential": 45.0,    # 45 Cr INR / km^2
    "commercial": 80.0,     # 80 Cr INR / km^2
    "agricultural": 4.5,    # 4.5 Cr INR / km^2
    "infrastructure": 25.0  # 25 Cr INR / km^2
}

# Pre-packaged Indian River Basins & Historical Dam Breaches
INDIAN_BASINS: Dict[str, Dict[str, Any]] = {
    "rishi_ganga": {
        "id": "rishi_ganga",
        "name": "Rishi Ganga / Dhauliganga (Chamoli Disaster 2021)",
        "state": "Uttarakhand",
        "basin_type": "High-Altitude Steep Himalayan Gorge",
        "historical_event": "7 Feb 2021 Glacial Rock/Ice Avalanche & Flash Flood",
        "center_coords": [30.485, 79.712],
        "bbox": [79.62, 30.42, 79.78, 30.56], # [min_lon, min_lat, max_lon, max_lat]
        "elevation_range": [1650.0, 3950.0],
        "default_params": {
            "dam_height_m": 45.0,
            "reservoir_volume_mcm": 18.5,       # Million Cubic Meters
            "breach_width_m": 60.0,
            "breach_depth_m": 35.0,
            "breach_time_hrs": 0.25,
            "manning_n": 0.052,
            "sim_duration_hrs": 2.5,
            "river_length_km": 14.8
        },
        "critical_infrastructure": [
            {"id": "inf_1", "name": "Tapovan Vishnugad Hydroelectric Plant", "type": "power_plant", "coords": [30.495, 79.680], "elevation": 1780.0},
            {"id": "inf_2", "name": "Raini Village Suspension Bridge", "type": "bridge", "coords": [30.487, 79.702], "elevation": 1920.0},
            {"id": "inf_3", "name": "Rishi Ganga Hydro Project Intake", "type": "dam_intake", "coords": [30.482, 79.715], "elevation": 2040.0},
            {"id": "inf_4", "name": "Malari Highway Border Road (BRO)", "type": "transport_corridor", "coords": [30.491, 79.695], "elevation": 1890.0},
            {"id": "inf_5", "name": "Joshimath Community Emergency Hospital", "type": "hospital", "coords": [30.556, 79.565], "elevation": 1875.0}
        ],
        "relief_shelters": [
            {"id": "sh_1", "name": "Joshimath Cantonment Safe Camp", "coords": [30.559, 79.560], "capacity": 3500, "elevation": 1920.0},
            {"id": "sh_2", "name": "Suraithota High Ground ITBP Camp", "coords": [30.505, 79.735], "capacity": 1200, "elevation": 2250.0}
        ]
    },
    "kosi_river": {
        "id": "kosi_river",
        "name": "Kosi River (Kushaha Mega-Breach 2008)",
        "state": "Bihar / Eastern Plains",
        "basin_type": "Alluvial Megafan Flat Lowland",
        "historical_event": "18 Aug 2008 Kushaha Eastern Embankment Collapse",
        "center_coords": [26.540, 86.950],
        "bbox": [86.75, 26.30, 87.15, 26.75],
        "elevation_range": [48.0, 85.0],
        "default_params": {
            "dam_height_m": 12.0,
            "reservoir_volume_mcm": 145.0,
            "breach_width_m": 1800.0,
            "breach_depth_m": 8.5,
            "breach_time_hrs": 3.0,
            "manning_n": 0.032,
            "sim_duration_hrs": 12.0,
            "river_length_km": 42.0
        },
        "critical_infrastructure": [
            {"id": "inf_10", "name": "Supaul District Civil Hospital", "type": "hospital", "coords": [26.115, 86.602], "elevation": 54.0},
            {"id": "inf_11", "name": "National Highway NH-57 Bridge", "type": "bridge", "coords": [26.350, 86.820], "elevation": 58.0},
            {"id": "inf_12", "name": "Birpur Barrage Power Substation", "type": "power_plant", "coords": [26.525, 86.925], "elevation": 72.0},
            {"id": "inf_13", "name": "Madhepura Railway Junction", "type": "railway_hub", "coords": [25.920, 86.790], "elevation": 50.0}
        ],
        "relief_shelters": [
            {"id": "sh_10", "name": "Supaul High School Elevated Relief Shelter", "coords": [26.130, 86.590], "capacity": 8000, "elevation": 62.0},
            {"id": "sh_11", "name": "Nirmali Central Relief Center", "coords": [26.320, 86.580], "capacity": 6500, "elevation": 64.0}
        ]
    },
    "phuktal_river": {
        "id": "phuktal_river",
        "name": "Phuktal River (Zanskar Landslide Dam 2015)",
        "state": "Ladakh / J&K",
        "basin_type": "Trans-Himalayan Cold Desert Canyon",
        "historical_event": "7 May 2015 Artificial Landslide Lake Outburst Flood",
        "center_coords": [33.250, 77.170],
        "bbox": [77.05, 33.15, 77.30, 33.35],
        "elevation_range": [3650.0, 4800.0],
        "default_params": {
            "dam_height_m": 60.0,
            "reservoir_volume_mcm": 30.0,
            "breach_width_m": 85.0,
            "breach_depth_m": 42.0,
            "breach_time_hrs": 0.75,
            "manning_n": 0.048,
            "sim_duration_hrs": 4.0,
            "river_length_km": 22.5
        },
        "critical_infrastructure": [
            {"id": "inf_20", "name": "Phuktal Monastery Ancient Footbridge", "type": "bridge", "coords": [33.265, 77.185], "elevation": 3850.0},
            {"id": "inf_21", "name": "Padum Central Health Post", "type": "hospital", "coords": [33.465, 76.880], "elevation": 3660.0},
            {"id": "inf_22", "name": "Tsarap Chu Solar Microgrid", "type": "power_plant", "coords": [33.240, 77.160], "elevation": 3780.0}
        ],
        "relief_shelters": [
            {"id": "sh_20", "name": "Padum Monastic High Ground Shelter", "coords": [33.470, 76.875], "capacity": 2000, "elevation": 3720.0}
        ]
    },
    "machhu_dam": {
        "id": "machhu_dam",
        "name": "Machhu Dam-II (Morbi Catastrophe 1979)",
        "state": "Gujarat",
        "basin_type": "Semi-Arid Peninsular River Catchment",
        "historical_event": "11 Aug 1979 Extreme Inflow & Earthen Flank Collapse",
        "center_coords": [22.820, 70.830],
        "bbox": [70.75, 22.75, 70.92, 22.90],
        "elevation_range": [35.0, 110.0],
        "default_params": {
            "dam_height_m": 26.0,
            "reservoir_volume_mcm": 110.0,
            "breach_width_m": 420.0,
            "breach_depth_m": 22.0,
            "breach_time_hrs": 0.5,
            "manning_n": 0.036,
            "sim_duration_hrs": 5.0,
            "river_length_km": 18.0
        },
        "critical_infrastructure": [
            {"id": "inf_30", "name": "Morbi Civil Hospital", "type": "hospital", "coords": [22.815, 70.835], "elevation": 48.0},
            {"id": "inf_31", "name": "Machhu Railway Viaduct", "type": "bridge", "coords": [22.828, 70.838], "elevation": 51.0},
            {"id": "inf_32", "name": "Morbi Substation GIDC Power Hub", "type": "power_plant", "coords": [22.805, 70.845], "elevation": 46.0}
        ],
        "relief_shelters": [
            {"id": "sh_30", "name": "Green Chowk Elevated Town Hall", "coords": [22.812, 70.830], "capacity": 5000, "elevation": 58.0}
        ]
    }
}
