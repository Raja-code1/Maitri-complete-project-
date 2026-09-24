/**
 * Member 6: HADR Decision Support & Incident Commander Panel
 */

class HADRPanel {
  static update(results) {
    const loss = results.loss_damage || {};
    const infra = results.infrastructure_status || [];
    const layers = results.layers || {};

    // 1. KPIs
    const popRiskEl = document.getElementById("hadrPopRisk");
    const lossCrEl = document.getElementById("hadrLossCr");
    const roadClosuresEl = document.getElementById("hadrRoadClosures");

    if (popRiskEl) popRiskEl.textContent = (loss.population_at_high_risk || 0).toLocaleString();
    if (lossCrEl) lossCrEl.textContent = `₹ ${loss.total_economic_loss_inr_crores || 0} Cr`;

    // Count closed roads
    let closedRoads = 0;
    if (layers.evacuation_routes && layers.evacuation_routes.features) {
      closedRoads = layers.evacuation_routes.features.filter(
        f => f.properties.condition === "SUBMERGED_CLOSED"
      ).length;
    }
    if (roadClosuresEl) roadClosuresEl.textContent = closedRoads;

    // 2. Critical Infrastructure Matrix Table
    const tbody = document.getElementById("infraTableBody");
    if (tbody) {
      if (infra.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No infrastructure data.</td></tr>';
      } else {
        tbody.innerHTML = infra.map(item => {
          let badgeClass = "badge-status";
          let bg = item.badge_color || "#22c55e";
          return `
            <tr>
              <td><b>${item.name}</b></td>
              <td><span style="font-size:0.75rem; color:#9ca3af;">${item.type.toUpperCase()}</span></td>
              <td>${item.inundation_depth_m} m</td>
              <td><span class="${badgeClass}" style="background-color:${bg}20; color:${bg}; border:1px solid ${bg};">${item.status}</span></td>
              <td><i style="color:#d1d5db;">${item.urgency_action}</i></td>
            </tr>
          `;
        }).join("");
      }
    }

    // 3. Sectoral Losses
    const sec = loss.sectoral_losses_inr_crores || {};
    const lossResEl = document.getElementById("lossRes");
    const lossCommEl = document.getElementById("lossComm");
    const lossAgriEl = document.getElementById("lossAgri");
    const lossInfraEl = document.getElementById("lossInfra");

    if (lossResEl) lossResEl.textContent = `₹ ${sec.residential || 0} Cr`;
    if (lossCommEl) lossCommEl.textContent = `₹ ${sec.commercial_industrial || 0} Cr`;
    if (lossAgriEl) lossAgriEl.textContent = `₹ ${sec.agricultural || 0} Cr (${loss.agricultural_area_submerged_ha || 0} ha)`;
    if (lossInfraEl) lossInfraEl.textContent = `₹ ${sec.public_infrastructure || 0} Cr`;
  }
}

window.HADRPanel = HADRPanel;
