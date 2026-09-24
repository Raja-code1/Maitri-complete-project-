"""
Member 3: Loss & Damage Assessment Engine
Evaluates structural, agricultural, and socio-economic damages
using depth-damage vulnerability curves and spatial overlays.
"""

import numpy as np
from typing import Dict, Any, List
from jal_drishti.config import ECONOMIC_LOSS_FACTORS

class LossDamageEngine:
    """
    Computes direct structural losses, population exposure, and economic damages in ₹ Crores.
    """

    @staticmethod
    def depth_damage_curve_residential(depth_m: float) -> float:
        """
        Stage-damage percentage for residential structures:
        0 - 0.3m: 15% (flooring, carpets, ground furnishings)
        0.3 - 0.8m: 35% (electrical circuits, appliances)
        0.8 - 1.5m: 65% (masonry saturation, structural walls)
        > 1.5m: 95% (severe structural compromise / collapse)
        """
        if depth_m <= 0.05:
            return 0.0
        elif depth_m <= 0.30:
            return 0.15 * (depth_m / 0.30)
        elif depth_m <= 0.80:
            return 0.15 + 0.20 * ((depth_m - 0.30) / 0.50)
        elif depth_m <= 1.50:
            return 0.35 + 0.30 * ((depth_m - 0.80) / 0.70)
        else:
            return min(1.0, 0.65 + 0.30 * min(1.0, (depth_m - 1.50) / 1.50))

    @staticmethod
    def calculate_losses(
        depth_grid: np.ndarray,
        basin_id: str,
        cell_dx: float,
        cell_dy: float
    ) -> Dict[str, Any]:
        """
        Calculates sectoral loss estimates and population exposure.
        """
        cell_area_km2 = (cell_dx * cell_dy) / 1e6
        wet_mask = depth_grid > 0.05
        total_wet_km2 = float(np.sum(wet_mask) * cell_area_km2)

        if total_wet_km2 == 0:
            return {
                "total_economic_loss_inr_crores": 0.0,
                "population_exposed": 0,
                "buildings_damaged": 0,
                "agricultural_area_submerged_ha": 0.0
            }

        # Sectoral distribution depends on basin geomorphology
        if basin_id == "rishi_ganga":
            # Mountain valley: high infrastructure/hydropower risk, lower farmland
            res_ratio, comm_ratio, agri_ratio, infra_ratio = 0.15, 0.10, 0.20, 0.55
            pop_density_per_km2 = 280
            bld_density_per_km2 = 45
        elif basin_id == "kosi_river":
            # Dense agricultural plain: high population and crops
            res_ratio, comm_ratio, agri_ratio, infra_ratio = 0.30, 0.10, 0.50, 0.10
            pop_density_per_km2 = 950
            bld_density_per_km2 = 180
        elif basin_id == "phuktal_river":
            # Remote canyon
            res_ratio, comm_ratio, agri_ratio, infra_ratio = 0.10, 0.05, 0.15, 0.70
            pop_density_per_km2 = 45
            bld_density_per_km2 = 12
        else: # machhu_dam
            # Semi-urban town + farmland
            res_ratio, comm_ratio, agri_ratio, infra_ratio = 0.40, 0.25, 0.25, 0.10
            pop_density_per_km2 = 820
            bld_density_per_km2 = 160

        mean_depth = float(np.mean(depth_grid[wet_mask]))
        damage_ratio = LossDamageEngine.depth_damage_curve_residential(mean_depth)

        # Economic loss computation
        loss_res = total_wet_km2 * res_ratio * ECONOMIC_LOSS_FACTORS["residential"] * damage_ratio
        loss_comm = total_wet_km2 * comm_ratio * ECONOMIC_LOSS_FACTORS["commercial"] * damage_ratio
        loss_agri = total_wet_km2 * agri_ratio * ECONOMIC_LOSS_FACTORS["agricultural"] * min(1.0, damage_ratio * 1.5)
        loss_infra = total_wet_km2 * infra_ratio * ECONOMIC_LOSS_FACTORS["infrastructure"] * damage_ratio

        total_loss_cr = loss_res + loss_comm + loss_agri + loss_infra
        exposed_pop = int(total_wet_km2 * pop_density_per_km2)
        damaged_bld = int(total_wet_km2 * bld_density_per_km2 * damage_ratio)
        agri_ha = round(total_wet_km2 * agri_ratio * 100.0, 1)

        return {
            "total_economic_loss_inr_crores": round(total_loss_cr, 2),
            "sectoral_losses_inr_crores": {
                "residential": round(loss_res, 2),
                "commercial_industrial": round(loss_comm, 2),
                "agricultural": round(loss_agri, 2),
                "public_infrastructure": round(loss_infra, 2)
            },
            "population_exposed": exposed_pop,
            "population_at_high_risk": int(exposed_pop * (0.6 if mean_depth > 1.0 else 0.25)),
            "buildings_damaged_count": damaged_bld,
            "agricultural_area_submerged_ha": agri_ha,
            "mean_flood_depth_m": round(mean_depth, 2),
            "vulnerability_damage_index": round(damage_ratio, 3)
        }
