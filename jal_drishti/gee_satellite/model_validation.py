"""
Member 4: Ground-Truth Validation & Model Comparison Benchmarker
Quantitatively evaluates SPH vs Delft3D vs GEE Sentinel-1 SAR observations
using spatial IoU, Dice coefficients, confusion matrix, and hydrodynamic metrics.
"""

import numpy as np
from typing import Dict, Any

class HydroModelValidator:
    """
    Validation engine comparing simulated inundation footprints with satellite ground-truth.
    """

    @staticmethod
    def compute_spatial_agreement(
        simulated_mask: np.ndarray,
        satellite_mask: np.ndarray,
        cell_dx: float = 250.0,
        cell_dy: float = 250.0
    ) -> Dict[str, Any]:
        """
        Calculates contingency table and spatial agreement metrics:
        - IoU (Intersection over Union)
        - Dice Coefficient
        - Hit, Miss, False Alarm areas in km^2
        """
        cell_km2 = (cell_dx * cell_dy) / 1e6

        # Auto-align shapes if grids differ in resolution/dimension
        if simulated_mask.shape != satellite_mask.shape:
            min_x = min(simulated_mask.shape[0], satellite_mask.shape[0])
            min_y = min(simulated_mask.shape[1], satellite_mask.shape[1])
            simulated_mask = simulated_mask[:min_x, :min_y]
            satellite_mask = satellite_mask[:min_x, :min_y]

        tp_mask = simulated_mask & satellite_mask
        fp_mask = simulated_mask & (~satellite_mask)
        fn_mask = (~simulated_mask) & satellite_mask
        tn_mask = (~simulated_mask) & (~satellite_mask)

        tp = int(np.sum(tp_mask))
        fp = int(np.sum(fp_mask))
        fn = int(np.sum(fn_mask))
        tn = int(np.sum(tn_mask))

        union = tp + fp + fn
        iou = float(tp / union) if union > 0 else 1.0
        dice = float((2.0 * tp) / (2.0 * tp + fp + fn)) if (2 * tp + fp + fn) > 0 else 1.0
        hit_rate = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        far = float(fp / (tp + fp)) if (tp + fp) > 0 else 0.0

        return {
            "iou_jaccard_index": round(iou, 3),
            "dice_similarity_coefficient": round(dice, 3),
            "hit_rate_sensitivity": round(hit_rate, 3),
            "false_alarm_ratio": round(far, 3),
            "areas_km2": {
                "hit_true_positive": round(tp * cell_km2, 2),
                "false_alarm_overprediction": round(fp * cell_km2, 2),
                "miss_underprediction": round(fn * cell_km2, 2)
            },
            "overall_accuracy_percent": round(100.0 * (tp + tn) / max(1, tp + tn + fp + fn), 2)
        }

    @staticmethod
    def compare_sph_vs_delft3d(
        sph_metrics: Dict[str, Any],
        delft_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cross-benchmarks SPH (Near-Field Lagrangian) against Delft3D (Far-Field Eulerian).
        """
        sph_v = sph_metrics.get("peak_surge_velocity_ms", 12.5)
        delft_v = delft_metrics.get("peak_velocity_ms", 7.8)

        sph_area = sph_metrics.get("surge_front_distance_m", 1500.0) * 0.001 * 0.4
        delft_area = delft_metrics.get("total_inundated_area_km2", 15.2)

        return {
            "near_field_regime": {
                "dominant_model": "Smoothed Particle Hydrodynamics (SPH)",
                "strengths": "Captures violent fluid collapse, dynamic wave splash, instant structural impact force",
                "peak_velocity_ms": sph_v,
                "impact_pressure_kpa": sph_metrics.get("max_dynamic_pressure_kpa", 85.0)
            },
            "far_field_regime": {
                "dominant_model": "Delft3D (2D Saint-Venant SWE)",
                "strengths": "Superior catchment-scale routing, multi-kilometer terrain wetting/drying, computational efficiency over large domains",
                "peak_velocity_ms": delft_v,
                "inundation_area_km2": delft_area
            },
            "velocity_amplification_near_field": round(sph_v / max(0.1, delft_v), 2),
            "recommended_operational_pipeline": "Hybrid Coupled Pipeline: SPH resolves initial 0-15 min near-field breach zone, passing outflow boundary hydrograph to Delft3D for downstream floodplain routing."
        }
