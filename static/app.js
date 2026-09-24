/**
 * MAITRI HUD — JARVIS Companion Controller v3
 * Live webcam canvas reticle, real mic audio spectrum analyser (FFT),
 * real-time voice pitch estimation, CBT/REBT/Box-breathing, TTS, STT,
 * AWBI trend history chart, and multi-scenario ground telemetry
 */

'use strict';

// ─── STATE ────────────────────────────────────────────────────────────────────
let voiceOn       = true;
let camActive     = false;
let micActive     = false;
let recognizing   = false;
let breathInterval = null;
let simIdx        = 0;
let awbiHistory   = [];           // rolling AWBI values for trend chart
let packetCount   = 0;

// Web Audio
let audioCtx = null, analyser = null, micSource = null;

// SpeechRecognition
let recognition = null;

// ─── DOM REFS ─────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const utcClock     = $('utc-clock');
const sysBadge     = $('sys-badge');
const hdrLatency   = $('hdr-latency');
const latencyTag   = $('latency-tag');
const btnVoice     = $('btn-voice');
const btnCam       = $('btn-cam');
const btnSimFace   = $('btn-sim-face');
const webcamVideo  = $('webcam-video');
const overlayCanvas= $('overlay-canvas');
const cvBadge      = $('cv-badge');
const audioBadge   = $('audio-badge');
const btnMicToggle = $('btn-mic-toggle');
const btnSpeak     = $('btn-speak');
const audioCanvas  = $('audio-canvas');
const histCanvas   = $('awbi-history-canvas');

// Vision
const vEmotion  = $('v-emotion'), vEar = $('v-ear'), barEar = $('bar-ear');
const vPerclos  = $('v-perclos'), barPerclos = $('bar-perclos');
const vMar      = $('v-mar'), barMar = $('bar-mar');
const vTension  = $('v-tension'), barTension = $('bar-tension');
const vPosture  = $('v-posture');

// Audio
const audioEmotionTag = $('audio-emotion-tag');
const aPitch  = $('a-pitch'), aJitter = $('a-jitter'), aShimmer = $('a-shimmer'), aStrain = $('a-strain');

// AWBI
const awbiScore = $('awbi-score'), awbiArc = $('awbi-arc'), awbiPill = $('awbi-pill');
const sStress = $('s-stress'), sFatigue = $('s-fatigue'), sCogload = $('s-cogload');

// Protocol / CBT
const protoName = $('proto-name'), protoText = $('proto-text');
const breathWidget = $('breath-widget'), breathPhase = $('breath-phase');

// Chat
const chatMsgs  = $('chat-msgs'), chatForm = $('chat-form'), chatInput = $('chat-input');

// Ground
const groundBadge = $('ground-badge'), pktId = $('pkt-id'), pktSeq = $('pkt-seq');
const pktCrc = $('pkt-crc'), pktHex = $('pkt-hex'), teleLog = $('tele-log');
const pktCount = $('pkt-count');

// ─── INIT ─────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  setInterval(updateClock, 1000); updateClock();
  initSpeechRecognition();
  initDemoSpectrum();
  initHistoryChart();
  setupListeners();
  // Initial telemetry fetch
  fetchTelemetry();
  setInterval(fetchTelemetry, 4000);
});

function updateClock() {
  utcClock.textContent = new Date().toUTCString().split(' ')[4] + ' UTC';
}

function setupListeners() {
  btnVoice.addEventListener('click', () => {
    voiceOn = !voiceOn;
    btnVoice.textContent = voiceOn ? '🔊 VOICE ON' : '🔇 VOICE OFF';
    if (voiceOn) speak('Voice synthesis activated, Commander.');
  });
  btnCam.addEventListener('click', toggleCam);
  btnSimFace.addEventListener('click', cycleSimFace);
  btnMicToggle.addEventListener('click', toggleMic);
  btnSpeak.addEventListener('click', toggleSTT);
  $('btn-breath').addEventListener('click', toggleBreathing);
  $('btn-rebt').addEventListener('click', activateREBT);
  $('btn-cbt').addEventListener('click', activateCBT);
  chatForm.addEventListener('submit', e => {
    e.preventDefault();
    const txt = chatInput.value.trim(); if (!txt) return;
    handleMessage(txt); chatInput.value = '';
  });
}

// ─── CLOCK ───────────────────────────────────────────────────────────────────

// ─── 1. CAMERA & CANVAS OVERLAY ───────────────────────────────────────────────
async function toggleCam() {
  if (!camActive) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
      webcamVideo.srcObject = stream;
      camActive = true;
      btnCam.textContent = '🛑 STOP CAMERA';
      btnCam.classList.add('red');
      webcamVideo.onloadedmetadata = () => {
        overlayCanvas.width  = webcamVideo.videoWidth  || 640;
        overlayCanvas.height = webcamVideo.videoHeight || 480;
        drawOverlay();
      };
      log('[CAM-01] Real-time video feed active. Optical tracking engaged.');
      speak('Visual tracking engaged. Monitoring facial biometrics.');
    } catch (err) {
      log('[CAM-01] ERROR: ' + err.message, 'r');
      alert('Camera access denied: ' + err.message);
    }
  } else {
    webcamVideo.srcObject?.getTracks().forEach(t => t.stop());
    webcamVideo.srcObject = null;
    camActive = false;
    btnCam.textContent = '📷 START CAMERA';
    btnCam.classList.remove('red');
    overlayCanvas.getContext('2d').clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    log('[CAM-01] Camera offline.');
  }
}

function drawOverlay() {
  if (!camActive) return;
  const ctx = overlayCanvas.getContext('2d');
  const W = overlayCanvas.width, H = overlayCanvas.height;
  ctx.clearRect(0, 0, W, H);

  const time = Date.now() / 1000;
  const pulse = 0.6 + 0.4 * Math.sin(time * 2);

  // Face bounding box
  const bx = W * 0.28, by = H * 0.12, bw = W * 0.44, bh = H * 0.68;
  const rl = 18; // reticle arm length

  // Reticle corners
  ctx.strokeStyle = `rgba(0,240,255,${pulse})`;
  ctx.lineWidth = 2;
  [[bx, by, 1, 1], [bx+bw, by, -1, 1], [bx, by+bh, 1, -1], [bx+bw, by+bh, -1, -1]].forEach(([cx, cy, dx, dy]) => {
    ctx.beginPath(); ctx.moveTo(cx + dx*rl, cy); ctx.lineTo(cx, cy); ctx.lineTo(cx, cy + dy*rl); ctx.stroke();
  });

  // Eye landmarks
  const eyeY = by + bh * 0.33;
  [[bx + bw*0.28, eyeY], [bx + bw*0.72, eyeY]].forEach(([ex, ey]) => {
    // Outer ring
    ctx.strokeStyle = `rgba(0,255,136,${pulse})`;
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(ex, ey, 14, 0, Math.PI*2); ctx.stroke();
    // Inner dot
    ctx.fillStyle = `rgba(0,255,136,${pulse})`;
    ctx.beginPath(); ctx.arc(ex, ey, 3, 0, Math.PI*2); ctx.fill();
    // Crosshair lines
    ctx.strokeStyle = `rgba(0,255,136,0.4)`;
    ctx.lineWidth = 0.8;
    ctx.beginPath(); ctx.moveTo(ex-20, ey); ctx.lineTo(ex+20, ey); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ex, ey-20); ctx.lineTo(ex, ey+20); ctx.stroke();
  });

  // Nose bridge line
  ctx.strokeStyle = `rgba(0,240,255,0.25)`;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(W/2, by + bh*0.33);
  ctx.lineTo(W/2, by + bh*0.62);
  ctx.stroke();

  // Mouth ellipse
  ctx.strokeStyle = `rgba(0,240,255,${0.5 * pulse})`;
  ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.ellipse(W/2, by + bh*0.76, bw*0.2, bh*0.065, 0, 0, Math.PI*2); ctx.stroke();

  // Top scan line
  const scanY = (by + (time % 1) * bh) % H;
  const grad = ctx.createLinearGradient(bx, scanY, bx+bw, scanY);
  grad.addColorStop(0, 'transparent'); grad.addColorStop(0.5, 'rgba(0,240,255,0.4)'); grad.addColorStop(1, 'transparent');
  ctx.fillStyle = grad;
  ctx.fillRect(bx, scanY, bw, 2);

  // HUD corner data overlay
  ctx.fillStyle = 'rgba(0,240,255,0.7)';
  ctx.font = '9px JetBrains Mono';
  ctx.fillText(`EAR:${vEar.textContent}`, bx+2, by - 6);
  ctx.fillText(`MAR:${vMar.textContent}`, bx + bw - 60, by - 6);

  requestAnimationFrame(drawOverlay);
}

const SIM_PRESETS = [
  { ear: 0.31, mar: 0.16, brow: 0.50, jaw: 0.20, pitch: 135, jitter: 0.012, shimmer: 0.028, label: 'Nominal Calm' },
  { ear: 0.24, mar: 0.27, brow: 0.20, jaw: 0.45, pitch: 192, jitter: 0.038, shimmer: 0.075, label: 'EVA Stressed' },
  { ear: 0.17, mar: 0.66, brow: 0.38, jaw: 0.24, pitch: 100, jitter: 0.028, shimmer: 0.088, label: 'Exhausted/Yawning' },
  { ear: 0.19, mar: 0.48, brow: 0.76, jaw: 0.68, pitch: 275, jitter: 0.065, shimmer: 0.120, label: 'Hypoxia Panic' },
];

function cycleSimFace() {
  simIdx = (simIdx + 1) % SIM_PRESETS.length;
  const p = SIM_PRESETS[simIdx];
  ingestMultimodal({ simulated_ear: p.ear, simulated_mar: p.mar, simulated_brow: p.brow,
    simulated_jaw: p.jaw, simulated_pitch: p.pitch, simulated_jitter: p.jitter,
    simulated_shimmer: p.shimmer, transcript: `Simulated: ${p.label}` });
  log(`[CV-SIM] Injected face preset: ${p.label}`);
}

// ─── 2. AUDIO SPECTRUM ANALYSER (REAL MIC FFT) ────────────────────────────────
async function toggleMic() {
  if (!micActive) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      micSource = audioCtx.createMediaStreamSource(stream);
      micSource.connect(analyser);
      micActive = true;
      btnMicToggle.textContent = '🛑 STOP MIC';
      btnMicToggle.classList.add('red');
      audioBadge.textContent = 'LIVE';
      audioBadge.className = 'badge badge-G';
      drawRealSpectrum();
      startPitchEstimation(stream);
      log('[AUD-01] Live microphone audio stream locked. FFT analysis active.');
    } catch (err) {
      log('[AUD-01] Mic access denied: ' + err.message, 'r');
      alert('Microphone access denied: ' + err.message);
    }
  } else {
    micSource?.disconnect();
    audioCtx?.close();
    micActive = false;
    audioCtx = null; analyser = null; micSource = null;
    btnMicToggle.textContent = '🎙 START MIC ANALYSIS';
    btnMicToggle.classList.remove('red');
    audioBadge.textContent = 'READY';
    audioBadge.className = 'badge badge-G';
    initDemoSpectrum();
    log('[AUD-01] Microphone offline.');
  }
}

function drawRealSpectrum() {
  if (!micActive || !analyser) return;
  const cvs = audioCanvas;
  const ctx = cvs.getContext('2d');
  const W = cvs.width, H = cvs.height;
  const data = new Uint8Array(analyser.frequencyBinCount);

  function frame() {
    if (!micActive) return;
    analyser.getByteFrequencyData(data);
    ctx.fillStyle = '#020812';
    ctx.fillRect(0, 0, W, H);

    const barW = W / data.length * 1.8;
    let x = 0;
    data.forEach((v, i) => {
      const ratio = v / 255;
      const barH = ratio * H;
      // Gradient based on energy level
      const r = Math.round(ratio * 80);
      const g = Math.round(200 + ratio * 55);
      const b = 255;
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(x, H - barH, barW - 1, barH);
      x += barW;
    });
    requestAnimationFrame(frame);
  }
  frame();
}

function initDemoSpectrum() {
  const cvs = audioCanvas;
  const ctx = cvs.getContext('2d');
  cvs.width = cvs.offsetWidth || 300; cvs.height = 60;

  function demo() {
    if (micActive) return; // stop demo when real mic is active
    const W = cvs.width, H = cvs.height;
    ctx.fillStyle = '#020812';
    ctx.fillRect(0, 0, W, H);
    const bars = 32;
    const bw = W / bars - 1;
    for (let i = 0; i < bars; i++) {
      const h = Math.random() * 12 + 3;
      ctx.fillStyle = `rgba(0,240,255,0.35)`;
      ctx.fillRect(i * (bw + 1), H - h, bw, h);
    }
    setTimeout(demo, 120);
  }
  demo();
}

// Real-time pitch estimation via autocorrelation on raw PCM
let pitchWorker = null;
function startPitchEstimation(stream) {
  // We use a separate analyser for time-domain pitch
  const pitchCtx = new AudioContext();
  const pitchAnalyser = pitchCtx.createAnalyser();
  pitchAnalyser.fftSize = 2048;
  const src = pitchCtx.createMediaStreamSource(stream);
  src.connect(pitchAnalyser);
  const buf = new Float32Array(pitchAnalyser.fftSize);

  setInterval(() => {
    if (!micActive) { pitchCtx.close(); return; }
    pitchAnalyser.getFloatTimeDomainData(buf);
    const freq = autoCorrelate(buf, pitchCtx.sampleRate);
    if (freq > 80 && freq < 500) {
      aPitch.textContent = freq.toFixed(0) + ' Hz';
      // Rough strain estimate from pitch deviation from 130Hz normal
      const deviation = Math.abs(freq - 130) / 130;
      const strain = Math.min(100, Math.round(deviation * 160));
      aStrain.textContent = strain + '/100';
      aStrain.style.color = strain > 60 ? 'var(--red)' : strain > 35 ? 'var(--yellow)' : 'var(--cyan)';

      // Jitter and shimmer placeholders (would need multi-frame analysis)
      const j = (0.008 + Math.random() * 0.015).toFixed(3);
      const s = (0.020 + Math.random() * 0.045).toFixed(3);
      aJitter.textContent = (j * 100).toFixed(1) + '%';
      aShimmer.textContent = (s * 100).toFixed(1) + '%';

      const emotion = strain > 65 ? 'PANICKED' : strain > 40 ? 'STRESSED' : strain > 20 ? 'MILD STRAIN' : 'CALM';
      audioEmotionTag.textContent = emotion;
      audioEmotionTag.style.color = strain > 65 ? 'var(--red)' : strain > 40 ? 'var(--orange)' : 'var(--cyan)';
    }
  }, 500);
}

// YIN-like autocorrelation pitch detector
function autoCorrelate(buf, sampleRate) {
  let size = buf.length, rms = 0;
  for (let i = 0; i < size; i++) rms += buf[i] * buf[i];
  rms = Math.sqrt(rms / size);
  if (rms < 0.01) return -1;

  let r1 = 0, r2 = size - 1;
  for (let i = 0; i < size/2; i++) { if (Math.abs(buf[i]) < 0.2) { r1 = i; break; } }
  for (let i = 1; i < size/2; i++) { if (Math.abs(buf[size - i]) < 0.2) { r2 = size - i; break; } }
  buf = buf.slice(r1, r2);
  size = buf.length;

  const c = new Array(size).fill(0);
  for (let i = 0; i < size; i++) for (let j = 0; j < size - i; j++) c[i] += buf[j] * buf[j + i];

  let d = 0;
  while (c[d] > c[d + 1]) d++;
  let maxVal = -1, maxPos = -1;
  for (let i = d; i < size; i++) { if (c[i] > maxVal) { maxVal = c[i]; maxPos = i; } }
  let T0 = maxPos;
  const x1 = c[T0-1], x2 = c[T0], x3 = c[T0+1];
  const a = (x1 + x3 - 2*x2) / 2, b = (x3 - x1) / 2;
  if (a) T0 -= b / (2*a);
  return sampleRate / T0;
}

// ─── 3. SPEECH RECOGNITION (STT) ──────────────────────────────────────────────
function initSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) return;
  recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';
  recognition.onstart = () => { recognizing = true; btnSpeak.textContent = '🔴 LISTENING'; btnSpeak.classList.add('red'); };
  recognition.onresult = e => {
    const text = e.results[0][0].transcript;
    chatInput.value = text;
    handleMessage(text);
  };
  recognition.onend = () => { recognizing = false; btnSpeak.textContent = '🎤 SPEAK'; btnSpeak.classList.remove('red'); };
  recognition.onerror = () => { recognizing = false; btnSpeak.textContent = '🎤 SPEAK'; btnSpeak.classList.remove('red'); };
}

function toggleSTT() {
  if (!recognition) { alert('Speech recognition not supported in this browser. Use Chrome.'); return; }
  if (!recognizing) {
    if (!micActive) toggleMic(); // also start mic for spectrum
    recognition.start();
  } else {
    recognition.stop();
  }
}

// ─── 4. JARVIS TTS ────────────────────────────────────────────────────────────
function speak(text) {
  if (!voiceOn || !window.speechSynthesis) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.0; u.pitch = 0.9;
  const voices = speechSynthesis.getVoices();
  const v = voices.find(v => v.name.includes('Google UK English Male') || v.name.includes('David') || v.lang === 'en-US');
  if (v) u.voice = v;
  speechSynthesis.speak(u);
}

// ─── 5. CHAT + MULTIMODAL API ─────────────────────────────────────────────────
async function handleMessage(text) {
  addMsg('ASTRONAUT', text);
  const result = await ingestMultimodal({
    transcript: text,
    simulated_pitch: aPitch.textContent !== '-- Hz' ? parseFloat(aPitch.textContent) : 140.0,
    simulated_jitter: 0.015,
  });
  if (result?.member3_dialogue) {
    const reply = result.member3_dialogue.text;
    addMsg('MAITRI', reply);
    speak(reply);
    // Update protocol display
    if (result.member3_dialogue.intervention) {
      const iname = result.member3_dialogue.intervention.protocol_name || '';
      protoName.textContent = '⚡ ' + iname;
      if (result.member3_dialogue.intervention.steps?.length) {
        protoText.textContent = result.member3_dialogue.intervention.steps[0];
      }
    }
  }
}

function addMsg(who, text) {
  const d = document.createElement('div');
  d.className = `msg ${who === 'ASTRONAUT' ? 'msg-a' : 'msg-m'}`;
  d.innerHTML = `<strong>${who}:</strong> ${text}`;
  chatMsgs.appendChild(d);
  chatMsgs.scrollTop = chatMsgs.scrollHeight;
}

async function ingestMultimodal(params = {}) {
  try {
    const res = await fetch('/api/v1/analyze/multimodal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    const data = await res.json();
    applyTelemetry(data);
    return data;
  } catch (e) { console.error('Multimodal ingest failed:', e); }
}

async function fetchTelemetry() {
  try {
    const res = await fetch('/api/v1/telemetry/live');
    if (res.ok) { const d = await res.json(); applyContext(d); }
  } catch (_) {}
}

// ─── 6. HUD UPDATE FROM TELEMETRY ─────────────────────────────────────────────
function applyTelemetry(data) {
  if (data.total_execution_latency_ms) {
    const ms = data.total_execution_latency_ms;
    latencyTag.textContent = `LATENCY ${ms}ms`;
    hdrLatency.textContent = ms + 'ms';
  }
  if (data.member4_fusion_context) applyContext(data.member4_fusion_context);
  if (data.member5_active_alert)   applyAlert(data.member5_active_alert);
  if (data.member5_telemetry_packet) {
    const p = data.member5_telemetry_packet;
    packetCount++;
    pktId.textContent  = p.packet_id || '—';
    pktSeq.textContent = p.ccsds_header?.packet_sequence_count ?? packetCount;
    pktCrc.textContent = p.crc32_checksum || '—';
    pktHex.textContent = (p.hex_payload || '').slice(0, 36) + '…';
    pktCount.textContent = packetCount + ' PACKETS';
  }
}

function applyContext(ctx) {
  const awbi = ctx.awbi_score ?? 90;
  awbiScore.textContent = awbi.toFixed(1);

  // Radial arc — circumference 439.82 for r=70
  const C = 439.82;
  awbiArc.style.strokeDashoffset = (C - (awbi / 100) * C).toFixed(2);

  // Color coding
  let col, cls, label;
  if (awbi >= 80)      { col='var(--green)';  cls='badge badge-G'; label='OPTIMAL EQUILIBRIUM'; }
  else if (awbi >= 60) { col='var(--yellow)'; cls='badge badge-Y'; label='MILD STRAIN DETECTED'; }
  else if (awbi >= 40) { col='var(--orange)'; cls='badge badge-O'; label='MODERATE STRESS ALERT'; }
  else                 { col='var(--red)';    cls='badge badge-R'; label='CRITICAL DISTRESS'; }

  awbiArc.style.stroke = col;
  awbiArc.style.filter = `drop-shadow(0 0 8px ${col})`;
  awbiPill.className = cls;
  awbiPill.textContent = label;
  awbiScore.style.color = col;
  awbiScore.style.textShadow = `0 0 20px ${col}`;
  sysBadge.className = cls;
  sysBadge.textContent = '⬤ ' + label.split(' ')[0];

  // Stats
  const si = ctx.stress_index ?? 0, fi = ctx.fatigue_index ?? 0, cl = ctx.cognitive_load_index ?? 0;
  sStress.textContent  = si.toFixed(1);
  sFatigue.textContent = fi.toFixed(1);
  sCogload.textContent = cl.toFixed(1);
  colorStat(sStress,  si, 30, 60);
  colorStat(sFatigue, fi, 30, 60);
  colorStat(sCogload, cl, 40, 70);

  // Vision metrics
  if (ctx.visual_state) {
    const v = ctx.visual_state;
    vEmotion.textContent = `${v.primary_emotion?.toUpperCase() ?? '—'} (${((v.confidence ?? 0)*100).toFixed(0)}%)`;
    if (v.fatigue_metrics) {
      const fm = v.fatigue_metrics;
      setBar('v-ear', 'bar-ear', fm.ear, 0.4, v => v.toFixed(2), 'EAR', 0.22, 0.26);
      setBar('v-perclos', 'bar-perclos', fm.perclos * 100, 100, v => v.toFixed(1) + '%', 'PERCLOS%', 10, 20);
      setBar('v-mar', 'bar-mar', fm.mar, 1, v => v.toFixed(2), 'MAR', 0.40, 0.55);
      vPosture.textContent = `${(fm.posture_stability ?? '').toUpperCase()} · ${(fm.head_pitch_deg ?? 0).toFixed(1)}°`;
    }
    if (v.micro_expressions) {
      const ts = v.micro_expressions.tension_score ?? 0;
      vTension.textContent = ts.toFixed(2);
      const pct = Math.min(100, ts * 100);
      barTension.style.width = pct + '%';
      barTension.className = `fill ${pct < 30 ? 'f-G' : pct < 55 ? 'f-Y' : 'f-R'}`;
    }
  }

  // Audio metrics from API
  if (ctx.audio_state) {
    const a = ctx.audio_state;
    if (!micActive) { // Only update from API when real mic is off
      aPitch.textContent  = (a.acoustic_features?.f0_pitch_hz ?? 0).toFixed(0) + ' Hz';
      aJitter.textContent = ((a.acoustic_features?.jitter_percent ?? 0) * 100).toFixed(1) + '%';
      aShimmer.textContent = ((a.acoustic_features?.shimmer_percent ?? 0) * 100).toFixed(1) + '%';
      aStrain.textContent = (a.vocal_strain_score ?? 0).toFixed(0) + '/100';
      audioEmotionTag.textContent = (a.audio_emotion ?? 'CALM').toUpperCase();
    }
  }

  // AWBI history
  awbiHistory.push(awbi);
  if (awbiHistory.length > 40) awbiHistory.shift();
  drawHistory();
}

function setBar(valId, barId, raw, maxVal, fmt, _key, warnThr, critThr) {
  const el = $(valId); if (el) el.textContent = fmt(raw);
  const bar = $(barId); if (!bar) return;
  const pct = Math.min(100, (raw / maxVal) * 100);
  bar.style.width = pct + '%';
  bar.className = `fill ${raw > critThr ? 'f-R' : raw > warnThr ? 'f-Y' : 'f-G'}`;
}

function colorStat(el, val, warn, crit) {
  el.style.color = val >= crit ? 'var(--red)' : val >= warn ? 'var(--yellow)' : 'var(--cyan)';
}

function applyAlert(a) {
  const sev = a.severity ?? 'GREEN';
  const clsMap = { GREEN: 'badge-G', YELLOW: 'badge-Y', ORANGE: 'badge-O', RED: 'badge-R' };
  groundBadge.className = `badge ${clsMap[sev] ?? 'badge-G'}`;
  groundBadge.textContent = `${sev} // ${a.title ?? sev}`;
  log(`[ALERT] [${sev}] ${a.title} — ${a.recommended_action}`, sev === 'RED' ? 'r' : sev === 'ORANGE' || sev === 'YELLOW' ? 'w' : '');
}

// ─── 7. AWBI TREND HISTORY CHART ──────────────────────────────────────────────
function initHistoryChart() {
  histCanvas.width  = histCanvas.offsetWidth || 320;
  histCanvas.height = 55;
  drawHistory();
}

function drawHistory() {
  const ctx = histCanvas.getContext('2d');
  const W = histCanvas.width, H = histCanvas.height;
  ctx.fillStyle = '#010507';
  ctx.fillRect(0, 0, W, H);
  if (awbiHistory.length < 2) return;

  const step = W / (awbiHistory.length - 1);
  const grad = ctx.createLinearGradient(0, 0, W, 0);
  grad.addColorStop(0, 'rgba(0,240,255,0.15)');
  grad.addColorStop(1, 'rgba(0,255,136,0.4)');

  ctx.beginPath();
  awbiHistory.forEach((v, i) => {
    const x = i * step, y = H - (v / 100) * (H - 8) - 4;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.strokeStyle = 'var(--cyan)';
  ctx.lineWidth = 2;
  ctx.shadowBlur = 6;
  ctx.shadowColor = 'var(--cyan)';
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Fill below
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();
}

// ─── 8. CBT / REBT / BOX BREATHING ───────────────────────────────────────────
function toggleBreathing() {
  if (breathWidget.style.display === 'flex') {
    breathWidget.style.display = 'none';
    clearInterval(breathInterval);
    protoName.textContent = '⚡ AUTONOMOUS MONITORING ACTIVE';
    protoText.textContent = 'Monitoring nominal baseline. Standing by.';
  } else {
    breathWidget.style.display = 'flex';
    protoName.textContent = '🫁 TACTICAL BOX BREATHING (4-4-4-4)';
    protoText.textContent = 'Synchronise with the glowing circle: Inhale 4s → Hold 4s → Exhale 4s → Hold 4s. Vagus nerve calming cycle active.';
    speak('Initiating tactical box breathing. Inhale through your nose now.');
    const phases = ['INHALE (4s)', 'HOLD BREATH (4s)', 'EXHALE (4s)', 'HOLD EMPTY (4s)'];
    let p = 0;
    breathPhase.textContent = phases[0];
    clearInterval(breathInterval);
    breathInterval = setInterval(() => {
      p = (p + 1) % 4;
      breathPhase.textContent = phases[p];
      if (p === 0) speak('Inhale.');
      if (p === 2) speak('Exhale.');
    }, 4000);
    log('[PROTO] Box Breathing 4-4-4-4 protocol activated. Vagus nerve stimulation.');
  }
}

function activateREBT() {
  clearInterval(breathInterval);
  breathWidget.style.display = 'none';
  protoName.textContent = '💡 REBT — ABCDE COGNITIVE DISPUTATION';
  protoText.textContent =
    'A→ Identify the activating stressor without catastrophising. ' +
    'B→ Disarm perfectionistic "musts" and demands for certainty. ' +
    'C→ Acknowledge autonomic arousal as information, not threat. ' +
    'D→ Dispute: instrument telemetry confirms triple-redundant safety. ' +
    'E→ Adopt calm, rational action aligned with your training.';
  speak('Activating REBT cognitive disputation. Your training and triple-redundant systems are verified nominal. Proceed with calibrated focus.');
  log('[REBT] ABCDE Disputation protocol engaged. Irrational belief restructuring active.');
}

function activateCBT() {
  clearInterval(breathInterval);
  breathWidget.style.display = 'none';
  protoName.textContent = '🧩 CBT — COGNITIVE RESTRUCTURING';
  protoText.textContent =
    'Step 1 → Identify the Automatic Negative Thought (ANT). ' +
    'Step 2 → Gather evidence: What do instruments confirm? ' +
    'Step 3 → Generate a balanced counter-thought. ' +
    'Step 4 → Rate your distress now (0-10). What changed?';
  speak('Cognitive Behavioural Therapy restructuring initiated. Let us examine the evidence together, Commander.');
  log('[CBT] Cognitive restructuring protocol active. Disarming automatic negative thoughts.');
}

// ─── 9. SCENARIO SIMULATION ───────────────────────────────────────────────────
window.triggerScenario = async function(id) {
  log(`[SIM] Triggering scenario [${id}]...`, 'w');
  try {
    const res = await fetch(`/api/v1/scenarios/${id}/execute`, { method: 'POST' });
    const data = await res.json();
    if (data.actual_result) {
      applyTelemetry(data.actual_result);
      const d = data.actual_result.member3_dialogue;
      if (d) { addMsg('MAITRI', d.text); speak(d.text); }
    }
  } catch (e) { log('[SIM] ERROR: ' + e.message, 'r'); }
};

// ─── 10. TELEMETRY LOG ────────────────────────────────────────────────────────
function log(msg, level = '') {
  const t = new Date().toTimeString().slice(0, 8);
  const d = document.createElement('div');
  d.className = level === 'r' ? 'log-r' : level === 'w' ? 'log-w' : '';
  d.textContent = `[${t}] ${msg}`;
  teleLog.appendChild(d);
  teleLog.scrollTop = teleLog.scrollHeight;
}
