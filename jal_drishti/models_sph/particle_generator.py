"""
Member 1: SPH Particle Discretization & Generator
Discretizes reservoir fluid volume, dam barrier, and downstream terrain DEM into SPH particles.
"""

from dataclasses import dataclass, field
import numpy as np
from typing import Dict, Any, Tuple, List

@dataclass
class ParticleSystem:
    """Holds active particles for the SPH simulation."""
    positions: np.ndarray          # Shape (N, 3) [x, y, z] in meters
    velocities: np.ndarray         # Shape (N, 3) [vx, vy, vz] in m/s
    densities: np.ndarray          # Shape (N,) in kg/m^3
    pressures: np.ndarray          # Shape (N,) in Pa
    masses: np.ndarray             # Shape (N,) in kg
    particle_types: np.ndarray     # Shape (N,) int: 0=fluid, 1=terrain/boundary, 2=dam structure
    smoothing_length: float = 2.5  # h in meters
    rest_density: float = 1000.0   # rho0 in kg/m^3

    @property
    def num_particles(self) -> int:
        return len(self.positions)

    @property
    def fluid_indices(self) -> np.ndarray:
        return np.where(self.particle_types == 0)[0]

    @property
    def boundary_indices(self) -> np.ndarray:
        return np.where(self.particle_types != 0)[0]

    def to_summary(self) -> Dict[str, Any]:
        fluid_idx = self.fluid_indices
        v_mag = np.linalg.norm(self.velocities[fluid_idx], axis=1) if len(fluid_idx) > 0 else np.array([0.0])
        return {
            "total_particles": int(self.num_particles),
            "fluid_particles": int(len(fluid_idx)),
            "boundary_particles": int(len(self.boundary_indices)),
            "max_velocity_ms": float(np.max(v_mag)),
            "mean_velocity_ms": float(np.mean(v_mag)),
            "max_pressure_kpa": float(np.max(self.pressures) / 1000.0) if len(self.pressures) > 0 else 0.0,
            "bounds": {
                "min_x": float(np.min(self.positions[:, 0])),
                "max_x": float(np.max(self.positions[:, 0])),
                "min_y": float(np.min(self.positions[:, 1])),
                "max_y": float(np.max(self.positions[:, 1])),
                "min_z": float(np.min(self.positions[:, 2])),
                "max_z": float(np.max(self.positions[:, 2]))
            }
        }


class SPHParticleGenerator:
    """
    Generates SPH particles from reservoir parameters, dam structure geometry,
    and downstream DEM topography.
    """

    def __init__(self, dx: float = 2.0, rest_density: float = 1000.0):
        """
        Args:
            dx: Initial particle spacing in meters
            rest_density: Fluid rest density in kg/m^3
        """
        self.dx = dx
        self.rest_density = rest_density
        self.h = 1.3 * dx  # Optimal smoothing length ratio

    def generate_dam_break_scenario(
        self,
        reservoir_length: float,
        reservoir_width: float,
        water_depth: float,
        breach_width: float,
        channel_length: float,
        valley_slope: float = 0.03,
        num_particles_target: int = 4000
    ) -> ParticleSystem:
        """
        Generates fluid particles behind a dam wall, boundary particles for the valley
        and dam flanks, with an open breach orifice.
        """
        # Adapt spacing to target particle budget for real-time responsiveness
        estimated_vol = reservoir_length * reservoir_width * water_depth
        dx = max(1.2, (estimated_vol / num_particles_target) ** (1/3))
        self.dx = dx
        self.h = 1.35 * dx

        particle_vol = dx ** 3
        particle_mass = self.rest_density * particle_vol

        # 1. Generate Fluid Column in Reservoir (-reservoir_length <= x <= 0)
        xs_f = np.arange(-reservoir_length, -dx/2, dx)
        ys_f = np.arange(-reservoir_width/2 + dx/2, reservoir_width/2, dx)
        zs_f = np.arange(dx/2, water_depth, dx)

        fx, fy, fz = np.meshgrid(xs_f, ys_f, zs_f, indexing='ij')
        fluid_pos = np.vstack([fx.ravel(), fy.ravel(), fz.ravel()]).T

        n_fluid = len(fluid_pos)
        fluid_vel = np.zeros((n_fluid, 3), dtype=np.float64)
        fluid_dens = np.full(n_fluid, self.rest_density, dtype=np.float64)
        
        # Hydrostatic initial pressure: p = rho * g * (H - z)
        fluid_press = np.maximum(0.0, self.rest_density * 9.81 * (water_depth - fluid_pos[:, 2]))
        fluid_masses = np.full(n_fluid, particle_mass, dtype=np.float64)
        fluid_types = np.zeros(n_fluid, dtype=np.int32)

        # 2. Generate Valley Bed and Side Walls (Boundary particles)
        xs_b = np.arange(-reservoir_length - 2*dx, channel_length + 2*dx, dx * 1.5)
        ys_b = np.arange(-reservoir_width/2 - 3*dx, reservoir_width/2 + 3*dx, dx * 1.5)
        bx, by = np.meshgrid(xs_b, ys_b, indexing='ij')
        bx_flat = bx.ravel()
        by_flat = by.ravel()

        # Valley bed elevation: slope downwards for x > 0, flat or concave in reservoir
        bed_z = np.where(
            bx_flat >= 0,
            -valley_slope * bx_flat + 0.08 * (by_flat ** 2) / (reservoir_width / 2),
            0.08 * (by_flat ** 2) / (reservoir_width / 2)
        )
        bed_pos = np.vstack([bx_flat, by_flat, bed_z]).T

        # 3. Generate Dam Wall with Breach Gap at x = 0
        dam_ys = np.arange(-reservoir_width/2, reservoir_width/2, dx * 1.2)
        dam_zs = np.arange(0.0, water_depth * 1.25, dx * 1.2)
        dy_grid, dz_grid = np.meshgrid(dam_ys, dam_zs, indexing='ij')
        dy_flat = dy_grid.ravel()
        dz_flat = dz_grid.ravel()

        # Breach condition: particles removed in the breach zone [-breach_width/2, breach_width/2]
        is_breached = (np.abs(dy_flat) <= breach_width / 2.0) & (dz_flat <= water_depth * 0.95)
        dam_mask = ~is_breached

        dam_pos = np.vstack([
            np.zeros(np.sum(dam_mask)),
            dy_flat[dam_mask],
            dz_flat[dam_mask]
        ]).T

        # Combine boundary particles (Bed + Dam)
        boundary_pos = np.vstack([bed_pos, dam_pos])
        n_bound = len(boundary_pos)
        bound_vel = np.zeros((n_bound, 3), dtype=np.float64)
        bound_dens = np.full(n_bound, self.rest_density, dtype=np.float64)
        bound_press = np.zeros(n_bound, dtype=np.float64)
        bound_masses = np.full(n_bound, particle_mass * 1.5, dtype=np.float64)
        bound_types = np.ones(n_bound, dtype=np.int32)

        # Merge all particles into unified system
        all_pos = np.vstack([fluid_pos, boundary_pos])
        all_vel = np.vstack([fluid_vel, bound_vel])
        all_dens = np.concatenate([fluid_dens, bound_dens])
        all_press = np.concatenate([fluid_press, bound_press])
        all_masses = np.concatenate([fluid_masses, bound_masses])
        all_types = np.concatenate([fluid_types, bound_types])

        return ParticleSystem(
            positions=all_pos,
            velocities=all_vel,
            densities=all_dens,
            pressures=all_press,
            masses=all_masses,
            particle_types=all_types,
            smoothing_length=self.h,
            rest_density=self.rest_density
        )
