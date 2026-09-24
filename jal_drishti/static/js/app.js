/**
 * Member 6: Application Master Controller
 * Wires GUI inputs, API requests, progress tracking, and layer synchronization.
 */

document.addEventListener("DOMContentLoaded", () => {
  const mapViewer = new MapViewer("map");
  let viewer3d = null;      // 3D viewer — lazy-initialized on first tab open
  let currentTaskId = null;
  let basinsData = {};

  // DOM Elements
  const basinSelect = document.getElementById("basinSelect");
  const basinDetailText = document.getElementById("basinDetailText");
  const inputDamHeight = document.getElementById("inputDamHeight");
  const inputResVol = document.getElementById("inputResVol");
  const inputBreachWidth = document.getElementById("inputBreachWidth");
  const inputBreachDepth = document.getElementById("inputBreachDepth");
  const inputManningN = document.getElementById("inputManningN");
  const inputDuration = document.getElementById("inputDuration");

  const btnRunSim = document.getElementById("btnRunSim");
  const progressContainer = document.getElementById("simProgressBarContainer");
  const progressFill = document.getElementById("progressBarFill");
  const progressMsg = document.getElementById("progressMessage");
  const progressPct = document.getElementById("progressPercent");

  const btnExportShp = document.getElementById("btnExportShp");
  const btnExportKml = document.getElementById("btnExportKml");
  const btnExportReport = document.getElementById("btnExportReport");

  // Load Basins Metadata
  fetch("/api/basins")
    .then(r => r.json())
    .then(data => {
      basinsData = data.basins || {};
      updateBasinForm();
    })
    .catch(err => console.error("Error loading basins:", err));

  function updateBasinForm() {
    const basinId = basinSelect.value;
    const b = basinsData[basinId];
    if (!b) return;

    basinDetailText.textContent = `${b.basin_type} (${b.historical_event})`;
    const p = b.default_params;
    inputDamHeight.value = p.dam_height_m;
    inputResVol.value = p.reservoir_volume_mcm;
    inputBreachWidth.value = p.breach_width_m;
    inputBreachDepth.value = p.breach_depth_m;
    inputManningN.value = p.manning_n;
    inputDuration.value = p.sim_duration_hrs;

    mapViewer.flyToBbox(b.bbox);
  }

  basinSelect.addEventListener("change", updateBasinForm);

  // Tab Navigation
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");

      if (targetId === "tab-map" && mapViewer.map) {
        setTimeout(() => mapViewer.map.invalidateSize(), 100);
      }

      // Lazy-initialize 3D WebGL viewer the first time the tab is opened
      if (targetId === "tab-3d") {
        if (!viewer3d) {
          viewer3d = new Hydro3DViewer("canvas3dContainer");
          viewer3d.init();
        } else {
          setTimeout(() => viewer3d.onResize(), 100);
        }
      }
    });
  });

  // Layer Visibility Checkboxes
  document.getElementById("layerDelft3D").addEventListener("change", (e) => mapViewer.setLayerVisibility("delft3d", e.target.checked));
  document.getElementById("layerSPH").addEventListener("change", (e) => mapViewer.setLayerVisibility("sph", e.target.checked));
  document.getElementById("layerGEE").addEventListener("change", (e) => mapViewer.setLayerVisibility("gee", e.target.checked));
  document.getElementById("layerEvac").addEventListener("change", (e) => mapViewer.setLayerVisibility("evac", e.target.checked));
  document.getElementById("layerInfra").addEventListener("change", (e) => mapViewer.setLayerVisibility("infra", e.target.checked));

  // Run Simulation Handler
  btnRunSim.addEventListener("click", async () => {
    const payload = {
      basin_id: basinSelect.value,
      dam_height_m: parseFloat(inputDamHeight.value),
      reservoir_volume_mcm: parseFloat(inputResVol.value),
      breach_width_m: parseFloat(inputBreachWidth.value),
      breach_depth_m: parseFloat(inputBreachDepth.value),
      manning_n: parseFloat(inputManningN.value),
      sim_duration_hrs: parseFloat(inputDuration.value)
    };

    btnRunSim.disabled = true;
    progressContainer.classList.remove("hidden");
    progressFill.style.width = "5%";
    progressMsg.textContent = "Dispatching hydrodynamic simulation...";
    progressPct.textContent = "5%";

    try {
      const resp = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      currentTaskId = data.task_id;
      pollSimulation(currentTaskId);
    } catch (err) {
      alert("Failed to start simulation: " + err.message);
      btnRunSim.disabled = false;
      progressContainer.classList.add("hidden");
    }
  });

  // Polling Function
  function pollSimulation(taskId) {
    const interval = setInterval(async () => {
      try {
        const resp = await fetch(`/api/status/${taskId}`);
        const statusData = await resp.json();

        const pct = Math.round((statusData.progress || 0) * 100);
        progressFill.style.width = `${pct}%`;
        progressPct.textContent = `${pct}%`;
        progressMsg.textContent = statusData.message || "Simulating hydrodynamics...";

        if (statusData.status === "COMPLETED") {
          clearInterval(interval);
          btnRunSim.disabled = false;
          progressMsg.textContent = "Simulation completed successfully!";

          const results = statusData.results;
          if (results) {
            handleSimulationSuccess(results);
          }
        } else if (statusData.status === "ERROR") {
          clearInterval(interval);
          btnRunSim.disabled = false;
          alert("Simulation Error: " + (statusData.message || "Unknown error"));
        }
      } catch (err) {
        clearInterval(interval);
        btnRunSim.disabled = false;
        console.error("Polling error:", err);
      }
    }, 600);
  }

  function handleSimulationSuccess(results) {
    // 1. Render Map Layers
    mapViewer.renderRunLayers(results);

    // 2. Populate Comparison View
    ComparisonView.update(results);

    // 3. Populate HADR Panel
    HADRPanel.update(results);

    // 4. Feed SPH snapshots into 3D viewer (init if not yet open)
    if (results.sph_snapshots && results.sph_snapshots.length > 0) {
      if (!viewer3d) {
        viewer3d = new Hydro3DViewer("canvas3dContainer");
        viewer3d.init();
      }
      viewer3d.loadSnapshots(results.sph_snapshots);
      // Notify user that 3D data is ready
      const tab3dBtn = document.querySelector("[data-tab='tab-3d']");
      if (tab3dBtn) tab3dBtn.style.color = "#10b981";
    }

    // 5. Enable Export Buttons
    if (results.downloads) {
      btnExportShp.disabled = false;
      btnExportShp.onclick = () => window.open(results.downloads.shapefile_zip, "_blank");

      btnExportKml.disabled = false;
      btnExportKml.onclick = () => window.open(results.downloads.kml_file, "_blank");

      btnExportReport.disabled = false;
      btnExportReport.onclick = () => window.open(results.downloads.hadr_report, "_blank");
    }
  }

  // Trigger initial run automatically so user sees live simulation instantly!
  setTimeout(() => {
    btnRunSim.click();
  }, 500);
});
