/**
 * Member 6: Multi-Model Comparison & Satellite Validation View
 */

class ComparisonView {
  static update(results) {
    const sph = results.sph_metrics || {};
    const delft = results.delft3d_metrics || {};
    const gee = results.gee_validation || {};
    const spatial = gee.spatial_metrics || {};
    const areas = spatial.areas_km2 || {};

    // SPH
    const sphVelEl = document.getElementById("compSphVel");
    const sphPressEl = document.getElementById("compSphPress");
    const sphSpeedEl = document.getElementById("compSphFrontSpeed");

    if (sphVelEl) sphVelEl.textContent = `${sph.peak_surge_velocity_ms || '--'} m/s`;
    if (sphPressEl) sphPressEl.textContent = `${sph.max_dynamic_pressure_kpa || '--'} kPa`;
    if (sphSpeedEl) sphSpeedEl.textContent = `${sph.measured_front_speed_ms || '--'} m/s`;

    // Delft3D
    const delftAreaEl = document.getElementById("compDelftArea");
    const delftDepthEl = document.getElementById("compDelftDepth");
    const delftArrivalEl = document.getElementById("compDelftArrival");

    if (delftAreaEl) delftAreaEl.textContent = `${delft.total_inundated_area_km2 || '--'} sq km`;
    if (delftDepthEl) delftDepthEl.textContent = `${delft.peak_depth_m || '--'} m`;
    if (delftArrivalEl) {
      const win = delft.wave_arrival_window_min || [0, 0];
      delftArrivalEl.textContent = `${win[0]} - ${win[1]} min`;
    }

    // GEE Validation
    const iouEl = document.getElementById("compIoU");
    const diceEl = document.getElementById("compDice");
    const accEl = document.getElementById("compAccuracy");

    if (iouEl) iouEl.textContent = spatial.iou_jaccard_index != null ? `${spatial.iou_jaccard_index}` : '--';
    if (diceEl) diceEl.textContent = spatial.dice_similarity_coefficient != null ? `${spatial.dice_similarity_coefficient}` : '--';
    if (accEl) accEl.textContent = spatial.overall_accuracy_percent != null ? `${spatial.overall_accuracy_percent}%` : '--%';

    // Contingency Box
    const hitEl = document.getElementById("contHit");
    const faEl = document.getElementById("contFalseAlarm");
    const missEl = document.getElementById("contMiss");

    if (hitEl) hitEl.textContent = `${areas.hit_true_positive || 0} sq km`;
    if (faEl) faEl.textContent = `${areas.false_alarm_overprediction || 0} sq km`;
    if (missEl) missEl.textContent = `${areas.miss_underprediction || 0} sq km`;
  }
}

window.ComparisonView = ComparisonView;
