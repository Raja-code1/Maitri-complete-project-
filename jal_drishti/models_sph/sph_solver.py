"""
Member 1: Weakly-Compressible SPH (WCSPH) Navier-Stokes Solver
Implements Wendland C2 smoothing kernel, Tait's EOS, Monaghan artificial viscosity,
and symplectic time integration for sudden dam break wave surge.
"""

from dataclasses import dataclass
import numpy as np
from scipy.spatial import cKDTree
from typing import Dict, Any, List, Optional, Tuple
from .particle_generator import ParticleSystem, SPHParticleGenerator

@dataclass
class SPHSimulationConfig:
    total_time: float = 12.0          # Total physical seconds simulated
    dt: float = 0.01                 # Integration time step (s)
    alpha_visc: float = 0.08         # Monaghan artificial viscosity coefficient
    beta_visc: float = 0.0           # Second viscosity parameter
    gamma_eos: float = 7.0           # Tait's EOS exponent
    c0_speed: float = 35.0           # Artificial speed of sound (m/s)
    snapshot_interval: float = 0.5   # Snapshot record interval (s)
    max_particles: int = 2500        # Particle budget for fast responsiveness


class WCSPHSolver:
    """
    Hydrodynamic solver implementing Weakly-Compressible SPH (WCSPH) equations.
    """

    def __init__(self, config: Optional[SPHSimulationConfig] = None):
        self.config = config or SPHSimulationConfig()
        self.rho0 = 1000.0  # kg/m^3
        self.g = np.array([0.0, 0.0, -9.81], dtype=np.float64) # Gravity vector
        self.B = (self.rho0 * (self.config.c0_speed ** 2)) / self.config.gamma_eos

    def _wendland_c2_kernel(self, r: np.ndarray, h: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates 3D Wendland C2 smoothing kernel and its derivative.
        W(q) = alpha_d * (1 - q/2)^4 * (2q + 1), for 0 <= q <= 2
        """
        q = r / h
        alpha_3d = 21.0 / (16.0 * np.pi * (h ** 3))
        w = np.zeros_like(q)
        dw_dr = np.zeros_like(q)

        mask = (q >= 0) & (q <= 2.0)
        q_m = q[mask]

        term1 = (1.0 - 0.5 * q_m) ** 4
        term2 = 2.0 * q_m + 1.0
        w[mask] = alpha_3d * term1 * term2

        # Derivative dW/dr = (dW/dq) / h
        # d/dq [(1 - q/2)^4 * (2q + 1)] = -5 * q * (1 - q/2)^3
        dw_dq = -5.0 * q_m * ((1.0 - 0.5 * q_m) ** 3)
        dw_dr[mask] = (alpha_3d / h) * dw_dq

        return w, dw_dr

    def compute_tait_pressure(self, densities: np.ndarray) -> np.ndarray:
        """
        Tait's Equation of State:
        P = B * ((rho / rho0)^gamma - 1), clamped at P >= 0
        """
        density_ratio = np.maximum(0.85, densities / self.rho0)
        p = self.B * (np.power(density_ratio, self.config.gamma_eos) - 1.0)
        return np.maximum(0.0, p)

    def step(self, system: ParticleSystem, dt: float) -> None:
        """
        Advances the SPH particle system by one physical timestep dt.
        """
        N = system.num_particles
        fluid_idx = system.fluid_indices
        if len(fluid_idx) == 0:
            return

        h = system.smoothing_length
        pos = system.positions
        vel = system.velocities
        rho = system.densities
        mass = system.masses
        p = system.pressures

        # Build KD-Tree for fast neighbor queries
        tree = cKDTree(pos)
        pairs = tree.query_pairs(r=2.0 * h, output_type='ndarray')

        # Accumulators
        drho_dt = np.zeros(N, dtype=np.float64)
        accel = np.zeros((N, 3), dtype=np.float64)

        if len(pairs) > 0:
            i_idx = pairs[:, 0]
            j_idx = pairs[:, 1]

            rij = pos[i_idx] - pos[j_idx]
            dist = np.linalg.norm(rij, axis=1)

            # Avoid singularity
            valid = dist > 1e-6
            i_idx = i_idx[valid]
            j_idx = j_idx[valid]
            rij = rij[valid]
            dist = dist[valid]

            _, dw_dr = self._wendland_c2_kernel(dist, h)
            # Normalized grad W
            grad_w = (rij / dist[:, np.newaxis]) * dw_dr[:, np.newaxis]

            # 1. Continuity: drho/dt = sum_j m_j (v_i - v_j) . grad_W
            vij = vel[i_idx] - vel[j_idx]
            v_dot_grad = np.sum(vij * grad_w, axis=1)

            np.add.at(drho_dt, i_idx, mass[j_idx] * v_dot_grad)
            np.add.at(drho_dt, j_idx, mass[i_idx] * v_dot_grad)

            # 2. Monaghan Artificial Viscosity
            v_dot_r = np.sum(vij * rij, axis=1)
            approaching = v_dot_r < 0.0

            pi_ij = np.zeros(len(dist), dtype=np.float64)
            if np.any(approaching):
                mu_ij = (h * v_dot_r[approaching]) / (dist[approaching]**2 + 0.01 * (h**2))
                rho_bar = 0.5 * (rho[i_idx[approaching]] + rho[j_idx[approaching]])
                pi_ij[approaching] = (
                    -self.config.alpha_visc * self.config.c0_speed * mu_ij
                    + self.config.beta_visc * (mu_ij ** 2)
                ) / rho_bar

            # 3. Momentum Equation: pressure gradient + artificial viscosity
            p_rho2_sum = (p[i_idx] / (rho[i_idx]**2)) + (p[j_idx] / (rho[j_idx]**2)) + pi_ij
            force_ij = -grad_w * p_rho2_sum[:, np.newaxis]

            np.add.at(accel, i_idx, mass[j_idx, np.newaxis] * force_ij)
            np.add.at(accel, j_idx, -mass[i_idx, np.newaxis] * force_ij)

        # Apply gravity to fluid particles
        accel[fluid_idx] += self.g

        # Solid Boundary Penalty Force (Lennard-Jones style repulsion)
        # Prevents fluid penetration into riverbed boundary particles
        bound_idx = system.boundary_indices
        if len(bound_idx) > 0 and len(fluid_idx) > 0:
            bound_pos = pos[bound_idx]
            b_tree = cKDTree(bound_pos)
            fluid_pos = pos[fluid_idx]
            b_dists, b_neighbors = b_tree.query(fluid_pos, k=1, distance_upper_bound=1.2 * h)

            close_mask = b_dists < (0.9 * h)
            if np.any(close_mask):
                f_active = fluid_idx[close_mask]
                b_active = bound_idx[b_neighbors[close_mask]]
                delta = pos[f_active] - pos[b_active]
                d_mag = np.maximum(1e-4, np.linalg.norm(delta, axis=1, keepdims=True))
                repulse_dir = delta / d_mag
                r_ratio = (0.9 * h) / d_mag
                repulse_force = 120.0 * (np.power(r_ratio, 4) - np.power(r_ratio, 2))
                accel[f_active] += np.clip(repulse_force * repulse_dir, -500.0, 500.0)

        # Time Integration (Symplectic Euler / Leapfrog for fluid particles)
        rho[fluid_idx] = np.maximum(
            0.8 * self.rho0,
            rho[fluid_idx] + drho_dt[fluid_idx] * dt
        )
        p[fluid_idx] = self.compute_tait_pressure(rho[fluid_idx])

        # Velocity update
        vel[fluid_idx] += accel[fluid_idx] * dt

        # Physical velocity limiter (max 35 m/s for catastrophic dam break waves)
        v_mag_sph = np.linalg.norm(vel[fluid_idx], axis=1, keepdims=True)
        v_max_phys = 35.0
        excess_sph = v_mag_sph > v_max_phys
        if np.any(excess_sph):
            vel[fluid_idx] = np.where(excess_sph, vel[fluid_idx] * (v_max_phys / np.maximum(1e-4, v_mag_sph)), vel[fluid_idx])

        # Pos update
        pos[fluid_idx] += vel[fluid_idx] * dt

        # Dam-break physical constraints: ground clamp
        # Fluid cannot fall infinitely below local bed
        pos[fluid_idx, 2] = np.maximum(-150.0, pos[fluid_idx, 2])

    def run_simulation(
        self,
        system: ParticleSystem,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Runs full SPH simulation, saving time snapshots and computing key metrics.
        """
        total_time = self.config.total_time
        dt = self.config.dt
        steps = int(total_time / dt)
        snap_step = max(1, int(self.config.snapshot_interval / dt))

        snapshots: List[Dict[str, Any]] = []
        time_elapsed = 0.0

        for step_idx in range(steps):
            self.step(system, dt)
            time_elapsed += dt

            if step_idx % snap_step == 0 or step_idx == steps - 1:
                fluid_idx = system.fluid_indices
                v_mag = np.linalg.norm(system.velocities[fluid_idx], axis=1) if len(fluid_idx) > 0 else np.array([0.0])
                
                # Sample max 150 particles for lightweight JSON payload
                sample_step = max(1, len(fluid_idx) // 120)
                sub_idx = fluid_idx[::sample_step]

                snapshots.append({
                    "time_s": round(time_elapsed, 2),
                    "particles": [
                        {
                            "x": round(float(system.positions[i, 0]), 2),
                            "y": round(float(system.positions[i, 1]), 2),
                            "z": round(float(system.positions[i, 2]), 2),
                            "vel": round(float(np.linalg.norm(system.velocities[i])), 2),
                            "press": round(float(system.pressures[i] / 1000.0), 2) # kPa
                        }
                        for i in sub_idx
                    ],
                    "max_velocity_ms": round(float(np.max(v_mag)), 2),
                    "surge_front_x": round(float(np.max(system.positions[fluid_idx, 0])), 2) if len(fluid_idx) > 0 else 0.0
                })

            if progress_callback and step_idx % 25 == 0:
                progress_callback(min(1.0, (step_idx + 1) / steps))

        return {
            "snapshots": snapshots,
            "final_summary": system.to_summary()
        }
