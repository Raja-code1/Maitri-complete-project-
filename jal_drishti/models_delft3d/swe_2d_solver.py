"""
Member 2: 2D Shallow Water Equations (SWE / Saint-Venant) Solver
Solves 2D non-linear hydrodynamic flood wave propagation on digital elevation models (DEM)
with wetting/drying fronts and Manning bottom shear stress.
"""

from dataclasses import dataclass
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from .manning_friction import ManningRoughnessCalculator

@dataclass
class SWEGridConfig:
    nx: int = 60                       # Grid cells along X (downstream)
    ny: int = 40                       # Grid cells along Y (lateral)
    dx: float = 250.0                  # Cell spacing in meters
    dy: float = 250.0                  # Cell spacing in meters
    cfl: float = 0.45                  # Courant number
    h_dry: float = 0.005               # Wetting / drying threshold (m)
    manning_n: float = 0.038           # Manning roughness coefficient


class SWE2DSolver:
    """
    Well-balanced Finite-Volume 2D Shallow Water Equations solver.
    """

    def __init__(self, config: Optional[SWEGridConfig] = None):
        self.config = config or SWEGridConfig()
        self.g = 9.81

    def generate_dam_breach_hydrograph(
        self,
        reservoir_vol_mcm: float,
        dam_height_m: float,
        breach_width_m: float,
        breach_time_hrs: float,
        total_sim_hrs: float,
        num_points: int = 100
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates breach outflow hydrograph using Froehlich (2008) and NWS breach hydraulics.
        """
        vol_m3 = reservoir_vol_mcm * 1e6
        # Peak discharge: Froehlich formula Qp = 0.607 * V^0.295 * Hw^1.24
        q_peak = 0.607 * (vol_m3 ** 0.295) * (dam_height_m ** 1.24)
        # Broad-crested weir limit check: Q_weir = (8/27) * sqrt(g) * B * H^(3/2)
        q_weir_limit = 0.385 * np.sqrt(self.g) * breach_width_m * (dam_height_m ** 1.5)
        q_peak = min(q_peak, q_weir_limit)

        time_s = np.linspace(0, total_sim_hrs * 3600.0, num_points)
        t_peak_s = max(60.0, breach_time_hrs * 3600.0 * 0.4)

        # Dimensionless hydrograph: gamma distribution
        scaled_t = np.maximum(1e-4, time_s / t_peak_s)
        hydrograph = q_peak * scaled_t * np.exp(1.0 - scaled_t)
        return time_s, hydrograph

    def simulate(
        self,
        dem_zb: np.ndarray,
        breach_x_idx: int,
        breach_y_idx: int,
        hydrograph_time_s: np.ndarray,
        hydrograph_q_m3s: np.ndarray,
        sim_duration_s: float,
        dam_height_m: float = 30.0,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Executes 2D SWE simulation over DEM terrain.
        """
        nx, ny = dem_zb.shape
        dx, dy = self.config.dx, self.config.dy
        h_dry = self.config.h_dry
        cell_area = dx * dy

        # State fields: depth h, x-velocity u, y-velocity v
        h = np.zeros((nx, ny), dtype=np.float64)
        u = np.zeros((nx, ny), dtype=np.float64)
        v = np.zeros((nx, ny), dtype=np.float64)

        # Historical peak tracking
        max_h = np.zeros((nx, ny), dtype=np.float64)
        max_v = np.zeros((nx, ny), dtype=np.float64)
        arrival_time = np.full((nx, ny), np.nan, dtype=np.float64)

        current_time = 0.0
        step_count = 0
        max_steps = 3000

        while current_time < sim_duration_s and step_count < max_steps:
            # 1. Determine CFL-stable timestep dt
            wet = h > h_dry
            if np.any(wet):
                celerity = np.sqrt(self.g * h[wet])
                max_speed_x = np.max(np.abs(u[wet]) + celerity)
                max_speed_y = np.max(np.abs(v[wet]) + celerity)
                max_speed = max(0.5, max_speed_x, max_speed_y)
                dt = self.config.cfl * min(dx, dy) / max_speed
            else:
                dt = 2.0

            dt = min(dt, 5.0, sim_duration_s - current_time)
            if dt <= 0:
                break

            # 2. Inject breach inflow at breach location
            current_q = np.interp(current_time, hydrograph_time_s, hydrograph_q_m3s)
            inflow_depth = (current_q * dt) / cell_area
            # Spread across breach cell and clamp to physical reservoir dam head
            y_start = max(0, breach_y_idx - 1)
            y_end = min(ny, breach_y_idx + 2)
            max_head = max(2.5, dam_height_m * 1.15)
            h[breach_x_idx, y_start:y_end] = np.minimum(
                max_head,
                h[breach_x_idx, y_start:y_end] + inflow_depth / 3.0
            )

            # 3. Hydrostatic Pressure & Bed Slope Source Terms (Central Differences)
            eta = h + dem_zb  # Water surface elevation
            d_eta_dx = np.zeros_like(h)
            d_eta_dy = np.zeros_like(h)

            d_eta_dx[1:-1, :] = (eta[2:, :] - eta[:-2, :]) / (2.0 * dx)
            d_eta_dy[:, 1:-1] = (eta[:, 2:] - eta[:, :-2]) / (2.0 * dy)

            # Limit slope acceleration to realistic channel gradient and apply on wet cells
            accel_x = np.where(wet, -self.g * np.clip(d_eta_dx, -0.06, 0.06), 0.0)
            accel_y = np.where(wet, -self.g * np.clip(d_eta_dy, -0.06, 0.06), 0.0)

            # 4. Manning Bottom Friction
            tau_x, tau_y = ManningRoughnessCalculator.compute_bed_shear_stress(
                h=h,
                u=u,
                v=v,
                n_manning=self.config.manning_n,
                g=self.g,
                h_dry=h_dry
            )

            u_new = u + (accel_x - tau_x) * dt
            v_new = v + (accel_y - tau_y) * dt

            # Physical velocity limiter (max 28 m/s for extreme mountain torrents)
            v_mag_calc = np.sqrt(u_new**2 + v_new**2)
            v_max_phys = 28.0
            excess = v_mag_calc > v_max_phys
            if np.any(excess):
                ratio = v_max_phys / v_mag_calc[excess]
                u_new[excess] *= ratio
                v_new[excess] *= ratio

            # 5. Mass Conservation Fluxes (First-Order Upwind Fluxes for Robust Positivity)
            qx = np.where(u_new > 0, h * u_new, np.roll(h, -1, axis=0) * u_new)
            qy = np.where(v_new > 0, h * v_new, np.roll(h, -1, axis=1) * v_new)

            div_flux = np.zeros_like(h)
            div_flux[1:-1, :] += (qx[1:-1, :] - qx[:-2, :]) / dx
            div_flux[:, 1:-1] += (qy[:, 1:-1] - qy[:, :-2]) / dy

            h_new = np.maximum(0.0, h - div_flux * dt)

            # Update dry boundaries
            dry_mask = h_new < h_dry
            h_new[dry_mask] = 0.0
            u_new[dry_mask] = 0.0
            v_new[dry_mask] = 0.0

            # State update
            h, u, v = h_new, u_new, v_new
            current_time += dt
            step_count += 1

            # Update peak statistics
            v_mag = np.sqrt(u**2 + v**2)
            max_h = np.maximum(max_h, h)
            max_v = np.maximum(max_v, v_mag)

            # Record arrival time (first time flood depth exceeds 5 cm)
            arrived = (h > 0.05) & np.isnan(arrival_time)
            arrival_time[arrived] = current_time / 60.0  # in minutes

            if progress_callback and step_count % 30 == 0:
                progress_callback(min(1.0, current_time / sim_duration_s))

        # Replace remaining NaNs in arrival time with -1
        arrival_time[np.isnan(arrival_time)] = -1.0

        return {
            "max_depth_grid": max_h,
            "max_velocity_grid": max_v,
            "arrival_time_min": arrival_time,
            "final_depth_grid": h,
            "steps_computed": step_count,
            "sim_duration_s": current_time
        }
