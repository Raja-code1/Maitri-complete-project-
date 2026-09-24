/**
 * Member 6: WebGIS Map Viewer Module (Leaflet Engine)
 * Manages map canvas, base tiles, vector layers, and spatial rendering.
 */

class MapViewer {
  constructor(containerId) {
    this.containerId = containerId;
    this.map = null;
    this.layers = {
      delft3d: null,
      sph: null,
      gee: null,
      evac: null,
      infra: null
    };
    this.initMap();
  }

  initMap() {
    // Default center at Rishi Ganga / Chamoli
    this.map = L.map(this.containerId, {
      zoomControl: true,
      attributionControl: false
    }).setView([30.485, 79.712], 12);

    // Base Layers (Free, No API Key required)
    const darkCanvas = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 16,
      attribution: 'Esri, HERE, DeLorme, MapmyIndia'
    });

    const satellite = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Esri, Maxar, Earthstar Geographics'
    });

    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    });

    // Default to dark canvas
    darkCanvas.addTo(this.map);

    const baseMaps = {
      "Dark Canvas": darkCanvas,
      "Satellite View": satellite,
      "OpenStreetMap": osm
    };

    L.control.layers(baseMaps, null, { position: 'topright' }).addTo(this.map);
  }

  flyToBbox(bbox) {
    if (!bbox || bbox.length < 4) return;
    const bounds = [
      [bbox[1], bbox[0]], // [min_lat, min_lon]
      [bbox[3], bbox[2]]  // [max_lat, max_lon]
    ];
    this.map.fitBounds(bounds, { padding: [25, 25], animate: true });
  }

  clearLayers() {
    Object.keys(this.layers).forEach(k => {
      if (this.layers[k]) {
        this.map.removeLayer(this.layers[k]);
        this.layers[k] = null;
      }
    });
  }

  renderRunLayers(results) {
    this.clearLayers();
    const l = results.layers || {};

    // 1. Delft3D Contours
    if (l.delft3d_contours) {
      this.layers.delft3d = L.geoJSON(l.delft3d_contours, {
        style: (feature) => ({
          color: feature.properties.color || '#dc2626',
          weight: 1,
          fillColor: feature.properties.color || '#dc2626',
          fillOpacity: feature.properties.fillOpacity || 0.55
        }),
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          layer.bindPopup(`
            <div style="font-size:12px; color:#111;">
              <b>Delft3D Flood Hazard:</b> ${p.depth_band}<br>
              <b>Estimated Depth:</b> ${p.min_depth_m}m - ${p.max_depth_m}m
            </div>
          `);
        }
      }).addTo(this.map);
    }

    // 2. SPH Surge Envelope
    if (l.sph_envelope) {
      this.layers.sph = L.geoJSON(l.sph_envelope, {
        style: {
          color: '#ffffff',
          dashArray: '4, 4',
          weight: 2,
          fillColor: '#ef4444',
          fillOpacity: 0.45
        },
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          layer.bindPopup(`
            <div style="font-size:12px; color:#111;">
              <b>SPH Near-Field Surge Envelope</b><br>
              <b>Peak Breach Velocity:</b> ${p.max_velocity_ms} m/s<br>
              <b>Simulated SPH Particles:</b> ${p.particle_count}
            </div>
          `);
        }
      }).addTo(this.map);
    }

    // 3. GEE Sentinel-1 SAR Ground Truth
    if (l.gee_satellite_mask) {
      this.layers.gee = L.geoJSON(l.gee_satellite_mask, {
        style: {
          color: '#0891b2',
          weight: 2,
          fillColor: '#06b6d4',
          fillOpacity: 0.50
        },
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          layer.bindPopup(`
            <div style="font-size:12px; color:#111;">
              <b>GEE Sentinel-1 SAR Observation</b><br>
              <b>Sensor:</b> ${p.sensor}<br>
              <b>Type:</b> ${p.observation_type}
            </div>
          `);
        }
      }).addTo(this.map);
    }

    // 4. Evacuation Routes
    if (l.evacuation_routes) {
      this.layers.evac = L.geoJSON(l.evacuation_routes, {
        style: (feature) => ({
          color: feature.properties.stroke_color || '#10b981',
          weight: feature.properties.stroke_width || 3,
          opacity: 0.95
        }),
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          layer.bindPopup(`
            <div style="font-size:12px; color:#111;">
              <b>Road Corridor:</b> ${p.road_name}<br>
              <b>HADR Status:</b> ${p.condition}<br>
              <b>Max Water Depth:</b> ${p.max_depth_m}m<br>
              <i>${p.description}</i>
            </div>
          `);
        }
      }).addTo(this.map);
    }

    // 5. Critical Infrastructure Markers
    const infraItems = results.infrastructure_status || [];
    if (infraItems.length > 0) {
      const markers = [];
      infraItems.forEach(item => {
        const [lat, lon] = item.coords;
        const color = item.badge_color || '#eab308';
        const marker = L.circleMarker([lat, lon], {
          radius: 7,
          fillColor: color,
          color: '#ffffff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9
        }).bindPopup(`
          <div style="font-size:12px; color:#111;">
            <b>${item.name}</b> (${item.type.toUpperCase()})<br>
            <b>Elevation:</b> ${item.elevation_m}m<br>
            <b>Inundation Depth:</b> ${item.inundation_depth_m}m<br>
            <b>Status:</b> <span style="color:${color};font-weight:bold;">${item.status}</span><br>
            <b>Action:</b> ${item.urgency_action}
          </div>
        `);
        markers.push(marker);
      });
      this.layers.infra = L.featureGroup(markers).addTo(this.map);
    }

    // Fit to basin bounds
    this.flyToBbox(results.bbox);
  }

  setLayerVisibility(layerKey, isVisible) {
    if (!this.layers[layerKey]) return;
    if (isVisible) {
      if (!this.map.hasLayer(this.layers[layerKey])) {
        this.map.addLayer(this.layers[layerKey]);
      }
    } else {
      if (this.map.hasLayer(this.layers[layerKey])) {
        this.map.removeLayer(this.layers[layerKey]);
      }
    }
  }
}

window.MapViewer = MapViewer;
