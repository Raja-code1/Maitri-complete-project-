"""
Member 2: Manning Roughness & Bed Shear Stress Engine
Computes spatial bed friction according to land cover / channel morphology.
"""

import numpy as np
from typing import Dict, Any

class ManningRoughnessCalculator:
    """
    Computes bottom shear stress for 2D shallow water flow using Manning's equation.
    """

    # Standard USGS / Chow (1959) Manning's n table
    LAND_COVER_N = {
        "clean_natural_channel": 0.030,
        "winding_natural_stream_with_pools": 0.040,
        "mountain_stream_with_cobbles_boulders": 0.055,
        "pasture_agricultural_plain": 0.035,
        "light_brush_and_weeds": 0.050,
        "dense_forest_floodplain": 0.100,
        "urban_residential_paved": 0.020,
        "urban_dense_structures": 0.080
    }

    @staticmethod
    def compute_bed_shear_stress(
        h: np.ndarray,
        u: np.ndarray,
        v: np.ndarray,
        n_manning: np.ndarray | float,
        g: float = 9.81,
        h_dry: float = 0.005
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Computes friction slope terms:
        Sfx = (g * n^2 * u * sqrt(u^2 + v^2)) / (h^(4/3))
        Sfy = (g * n^2 * v * sqrt(u^2 + v^2)) / (h^(4/3))
        
        Returns:
            (tau_x_rho, tau_y_rho): acceleration terms (m/s^2) due to bottom friction
        """
        wet = h > h_dry
        vel_mag = np.zeros_like(h)
        vel_mag[wet] = np.sqrt(u[wet]**2 + v[wet]**2)

        h_safe = np.maximum(h_dry, h)
        denom = np.power(h_safe, 4.0 / 3.0)

        n2 = np.power(n_manning, 2)
        coef = (g * n2 * vel_mag) / denom

        # Semi-implicit friction limiter to maintain numerical stability in very shallow water
        friction_limiter = 1.0 / (1.0 + coef * 0.1)

        tau_x = np.zeros_like(h)
        tau_y = np.zeros_like(h)

        tau_x[wet] = (coef[wet] * u[wet]) * friction_limiter[wet]
        tau_y[wet] = (coef[wet] * v[wet]) * friction_limiter[wet]

        return tau_x, tau_y
