/**
 * 3D Hydrodynamic Simulation Visualizer (Three.js Engine)
 * Renders 3D mountain canyon, concrete dam structure, breach opening,
 * and 3D SPH particles with velocity colormapping and OrbitControls.
 */

class Hydro3DViewer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.particlesMesh = null;
    this.snapshots = [];
    this.currentFrame = 0;
    this.isPlaying = false;
    this.animInterval = null;
    this.isInitialized = false;

    // Cache elements
    this.timeEl = document.getElementById("hud3dTime");
    this.velEl = document.getElementById("hud3dVel");
    this.frontEl = document.getElementById("hud3dFront");
    this.partEl = document.getElementById("hud3dParticles");
    this.sliderEl = document.getElementById("slider3D");
    this.playBtn = document.getElementById("btnPlay3D");
    this.resetBtn = document.getElementById("btnReset3D");

    this.wireControls();
  }

  init() {
    if (this.isInitialized || !this.container) return;
    if (typeof THREE === "undefined") {
      console.warn("Three.js not yet loaded.");
      return;
    }

    const width = this.container.clientWidth || 800;
    const height = this.container.clientHeight || 600;

    // 1. Scene & Camera
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0a0f1d);
    this.scene.fog = new THREE.FogExp2(0x0a0f1d, 0.005);

    this.camera = new THREE.PerspectiveCamera(50, width / height, 0.5, 2000);
    this.camera.position.set(65, 45, 95);

    // 2. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.container.appendChild(this.renderer.domElement);

    // 3. Orbit Controls
    if (THREE.OrbitControls) {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.08;
      this.controls.target.set(30, 10, 0);
      this.controls.maxPolarAngle = Math.PI / 2 - 0.02;
      this.controls.minDistance = 15;
      this.controls.maxDistance = 350;
    }

    // 4. Lighting
    const ambient = new THREE.AmbientLight(0x94a3b8, 0.6);
    this.scene.add(ambient);

    const sun = new THREE.DirectionalLight(0xffffff, 1.1);
    sun.position.set(80, 120, 60);
    sun.castShadow = true;
    this.scene.add(sun);

    const blueRim = new THREE.DirectionalLight(0x06b6d4, 0.4);
    blueRim.position.set(-60, 40, -50);
    this.scene.add(blueRim);

    // 5. Environment: Valley Terrain & Dam
    this.buildTerrain();
    this.buildDamStructure();

    // 6. Particle System Setup
    this.buildParticleSystem();

    this.isInitialized = true;
    this.animate();

    window.addEventListener("resize", () => this.onResize());
  }

  buildTerrain() {
    const planeGeo = new THREE.PlaneGeometry(240, 160, 64, 48);
    planeGeo.rotateX(-Math.PI / 2);

    const pos = planeGeo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      const valleySlope = 0.003 * Math.pow(z, 2);
      const riverbedIncline = -0.06 * (x - 20);
      pos.setY(i, valleySlope + riverbedIncline + Math.sin(x * 0.08) * 1.5);
    }
    planeGeo.computeVertexNormals();

    const terrainMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.85,
      metalness: 0.15,
      wireframe: false
    });

    const terrain = new THREE.Mesh(planeGeo, terrainMat);
    terrain.position.set(40, -2, 0);
    terrain.receiveShadow = true;
    this.scene.add(terrain);

    const grid = new THREE.GridHelper(260, 52, 0x334155, 0x1e293b);
    grid.position.set(40, -2.1, 0);
    this.scene.add(grid);
  }

  buildDamStructure() {
    this.damGroup = new THREE.Group();

    const concreteMat = new THREE.MeshStandardMaterial({
      color: 0x475569,
      roughness: 0.6,
      metalness: 0.2
    });

    const leftWingGeo = new THREE.BoxGeometry(10, 24, 45);
    const leftWing = new THREE.Mesh(leftWingGeo, concreteMat);
    leftWing.position.set(0, 10, 32);
    leftWing.castShadow = true;
    this.damGroup.add(leftWing);

    const rightWingGeo = new THREE.BoxGeometry(10, 24, 45);
    const rightWing = new THREE.Mesh(rightWingGeo, concreteMat);
    rightWing.position.set(0, 10, -32);
    rightWing.castShadow = true;
    this.damGroup.add(rightWing);

    const breachNotchGeo = new THREE.BoxGeometry(9.8, 2, 20);
    const breachMat = new THREE.MeshBasicMaterial({ color: 0xef4444, wireframe: true });
    const breachNotch = new THREE.Mesh(breachNotchGeo, breachMat);
    breachNotch.position.set(0, 1, 0);
    this.damGroup.add(breachNotch);

    const resGeo = new THREE.BoxGeometry(45, 14, 70);
    const resMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      transparent: true,
      opacity: 0.65,
      roughness: 0.1
    });
    const resMesh = new THREE.Mesh(resGeo, resMat);
    resMesh.position.set(-23, 6, 0);
    this.damGroup.add(resMesh);

    this.scene.add(this.damGroup);
  }

  buildParticleSystem() {
    this.maxParticles = 180;
    this.particleGeo = new THREE.SphereGeometry(0.8, 8, 8);
    this.particleMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      roughness: 0.2,
      metalness: 0.3,
      emissive: 0x0284c7,
      emissiveIntensity: 0.5
    });

    this.particlesMesh = new THREE.InstancedMesh(this.particleGeo, this.particleMat, this.maxParticles);
    this.particlesMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    const dummy = new THREE.Object3D();
    for (let i = 0; i < this.maxParticles; i++) {
      dummy.position.set(0, -999, 0);
      dummy.updateMatrix();
      this.particlesMesh.setMatrixAt(i, dummy.matrix);
    }
    this.particlesMesh.instanceMatrix.needsUpdate = true;
    this.scene.add(this.particlesMesh);
  }

  loadSnapshots(snapshots) {
    if (!snapshots || snapshots.length === 0) return;
    this.snapshots = snapshots;
    this.currentFrame = 0;
    if (this.sliderEl) {
      this.sliderEl.max = snapshots.length - 1;
      this.sliderEl.value = 0;
    }
    this.renderFrame(0);
  }

  renderFrame(frameIdx) {
    if (!this.snapshots || !this.snapshots[frameIdx] || !this.particlesMesh) return;
    const snap = this.snapshots[frameIdx];

    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    const particles = snap.particles || [];

    for (let i = 0; i < this.maxParticles; i++) {
      if (i < particles.length) {
        const p = particles[i];
        dummy.position.set(p.x, Math.max(0.5, p.z * 0.8), (p.y - 15.0) * 1.2);
        const scale = 0.7 + Math.min(1.0, (p.vel || 0) / 25.0);
        dummy.scale.set(scale, scale, scale);
        dummy.updateMatrix();
        this.particlesMesh.setMatrixAt(i, dummy.matrix);

        const normalizedV = Math.min(1.0, (p.vel || 0) / 28.0);
        if (normalizedV < 0.35) {
          color.setRGB(0.1, 0.6 + normalizedV * 0.8, 1.0);
        } else if (normalizedV < 0.7) {
          color.setRGB(0.9, 0.85, 0.1);
        } else {
          color.setRGB(1.0, 0.2 + (1.0 - normalizedV) * 0.4, 0.1);
        }
        this.particlesMesh.setColorAt(i, color);
      } else {
        dummy.position.set(0, -999, 0);
        dummy.updateMatrix();
        this.particlesMesh.setMatrixAt(i, dummy.matrix);
      }
    }

    this.particlesMesh.instanceMatrix.needsUpdate = true;
    if (this.particlesMesh.instanceColor) {
      this.particlesMesh.instanceColor.needsUpdate = true;
    }

    if (this.timeEl) this.timeEl.textContent = ` ${snap.time_s.toFixed(2)} s `;
    if (this.velEl) this.velEl.textContent = ` ${(snap.max_velocity_ms || 0).toFixed(1)} m/s `;
    if (this.frontEl) this.frontEl.textContent = ` ${(snap.surge_front_x || 0).toFixed(1)} m `;
    if (this.partEl) this.partEl.textContent = ` ${particles.length} `;
    if (this.sliderEl) this.sliderEl.value = frameIdx;
  }

  wireControls() {
    if (this.playBtn) {
      this.playBtn.addEventListener("click", () => this.togglePlay());
    }
    if (this.resetBtn) {
      this.resetBtn.addEventListener("click", () => {
        this.pause();
        this.currentFrame = 0;
        this.renderFrame(0);
      });
    }
    if (this.sliderEl) {
      this.sliderEl.addEventListener("input", (ev) => {
        this.pause();
        this.currentFrame = parseInt(ev.target.value, 10);
        this.renderFrame(this.currentFrame);
      });
    }
  }

  togglePlay() {
    if (this.isPlaying) {
      this.pause();
    } else {
      this.play();
    }
  }

  play() {
    if (!this.snapshots || this.snapshots.length === 0) return;
    this.isPlaying = true;
    if (this.playBtn) this.playBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
    this.animInterval = setInterval(() => {
      this.currentFrame = (this.currentFrame + 1) % this.snapshots.length;
      this.renderFrame(this.currentFrame);
    }, 450);
  }

  pause() {
    this.isPlaying = false;
    if (this.animInterval) {
      clearInterval(this.animInterval);
      this.animInterval = null;
    }
    if (this.playBtn) this.playBtn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
  }

  onResize() {
    if (!this.container || !this.renderer || !this.camera) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    if (width === 0 || height === 0) return;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    if (this.controls) this.controls.update();
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  }
}

window.Hydro3DViewer = Hydro3DViewer;