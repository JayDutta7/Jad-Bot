/**
 * J.A.D. AI MORNING ASSISTANT & WAKE-UP AGENT - CLIENT LOGIC
 * Features: 3D Holographic Orb Controller, Canvas Particle Field, Radial Visualizer,
 * Real-Time IST Clock & Countdown, Web Speech STT/TTS, and REST API Sync.
 */

// ==============================================================================
// 1. STATE & CONSTANTS
// ==============================================================================

// --------------- Theme Manager ---------------
const ThemeManager = {
  _current: 'night',
  _autoEnabled: true,

  init() {
    // Check saved preference first, else auto-detect from local time
    try {
      const saved = localStorage.getItem('jad_theme');
      if (saved === 'day' || saved === 'night') {
        this._current = saved;
        this._autoEnabled = false;
        this.apply(saved);
      } else {
        this.applyAutoTheme();
      }
    } catch (e) {
      this.applyAutoTheme();
    }

    // Re-check every 60 seconds if auto mode is enabled
    setInterval(() => {
      if (this._autoEnabled) this.applyAutoTheme();
    }, 60000);

    // Toggle button
    const btn = document.getElementById('themeToggleBtn');
    if (btn) {
      btn.addEventListener('click', () => this.toggle());
    }
  },

  getAutoTheme() {
    const hour = new Date().getHours();
    // Day: 5 AM to 7 PM (19:00), Night: 7 PM to 5 AM
    return (hour >= 5 && hour < 19) ? 'day' : 'night';
  },

  applyAutoTheme() {
    if (!this._autoEnabled) return;
    const theme = this.getAutoTheme();
    this.apply(theme);
  },

  toggle() {
    const next = this._current === 'night' ? 'day' : 'night';
    this._autoEnabled = false;
    this.apply(next);
    try {
      localStorage.setItem('jad_theme', next);
    } catch (e) {}
  },

  apply(theme) {
    this._current = theme;
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme === 'day' ? 'light' : 'dark';

    const icon = document.getElementById('themeToggleIcon');
    const label = document.getElementById('themeLabel');
    if (icon) icon.textContent = theme === 'day' ? '☀️' : '🌙';
    if (label) label.textContent = theme === 'day' ? '☀️ Day' : '🌙 Night';

    // Notify particle canvas to update colors
    if (window.__updateParticleTheme) window.__updateParticleTheme(theme);
  },

  get current() { return this._current; },
};

const STATE = {
  agentState: 'idle', // 'idle' | 'ringing' | 'listening' | 'thinking' | 'speaking'
  isRinging: false,
  sleepLockActive: true,
  platform: 'Desktop',
  userTitle: 'Boss',
  targetAlarmIso: null,
  browserAudioActive: false,
  isListeningMic: false,
  serverGreeting: null,
  serverTimeOfDay: null,
};

function getTimeOfDay() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return 'morning';
  if (hour === 12) return 'noon';
  if (hour >= 13 && hour < 17) return 'afternoon';
  if (hour >= 17 && hour < 19) return 'evening';
  return 'night';
}

function getTimeOfDayGreeting() {
  const tod = getTimeOfDay();
  if (tod === 'morning') return 'Good morning';
  if (tod === 'noon') return 'Good noon';
  if (tod === 'afternoon') return 'Good afternoon';
  if (tod === 'evening') return 'Good evening';
  return 'Good night';
}

function getActiveGreeting() {
  return STATE.serverGreeting || getTimeOfDayGreeting();
}

function getActiveTimeOfDay() {
  return STATE.serverTimeOfDay || getTimeOfDay();
}

// DOM Elements
const DOM = {
  liveClock: document.getElementById('liveClock'),
  platformText: document.getElementById('platformText'),
  wakeLockBtn: document.getElementById('wakeLockBtn'),
  wakeLockText: document.getElementById('wakeLockText'),
  wakeLockDot: document.getElementById('wakeLockDot'),
  hologramStage: document.getElementById('hologramStage'),
  orbCore: document.getElementById('orbCore'),
  agentStateBadge: document.getElementById('agentStateBadge'),
  agentStateLabel: document.getElementById('agentStateLabel'),
  cdHours: document.getElementById('cdHours'),
  cdMinutes: document.getElementById('cdMinutes'),
  cdSeconds: document.getElementById('cdSeconds'),
  targetAlarmTime: document.getElementById('targetAlarmTime'),
  btnSimulateRoutine: document.getElementById('btnSimulateRoutine'),
  btnTestAlarm: document.getElementById('btnTestAlarm'),
  btnStopAlarm: document.getElementById('btnStopAlarm'),
  btnFetchNews: document.getElementById('btnFetchNews'),
  btnVoiceMic: document.getElementById('btnVoiceMic'),
  micIcon: document.getElementById('micIcon'),
  micLabel: document.getElementById('micLabel'),
  chatMessages: document.getElementById('chatMessages'),
  chatForm: document.getElementById('chatForm'),
  chatInput: document.getElementById('chatInput'),
  chatMicBtn: document.getElementById('chatMicBtn'),
  newsList: document.getElementById('newsList'),
  btnRefreshNews: document.getElementById('btnRefreshNews'),
  footerSpokenStatus: document.getElementById('footerSpokenStatus'),
  browserAlarmAudio: document.getElementById('browserAlarmAudio'),
  visualizerCanvas: document.getElementById('visualizerCanvas'),
  ambientCanvas: document.getElementById('ambientCanvas'),
  weatherPill: document.getElementById('weatherPill'),
  weatherIcon: document.getElementById('weatherIcon'),
  weatherTemp: document.getElementById('weatherTemp'),
  btnWeather: document.getElementById('btnWeather'),
  locationBadge: document.getElementById('locationBadge'),
  locationText: document.getElementById('locationText'),
  locationBanner: document.getElementById('locationBanner'),
  locationForm: document.getElementById('locationForm'),
  locationInput: document.getElementById('locationInput'),
  btnCloseBanner: document.getElementById('btnCloseBanner'),
  countdownHeader: document.getElementById('countdownHeader'),
  btnChangeAlarm: document.getElementById('btnChangeAlarm'),
  wakeWordBtn: document.getElementById('wakeWordBtn'),
  wakeWordText: document.getElementById('wakeWordText'),
  themeToggleBtn: document.getElementById('themeToggleBtn'),
  themeToggleIcon: document.getElementById('themeToggleIcon'),
  themeLabel: document.getElementById('themeLabel'),
};

// ==============================================================================
// 2. AMBIENT PARTICLE FIELD CANVAS
// ==============================================================================
(function initAmbientCanvas() {
  const canvas = DOM.ambientCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const count = Math.min(90, Math.floor(width / 18));

  // Theme-aware particle colors
  let pColor1 = '0, 242, 254';
  let pColor2 = '121, 40, 202';
  let lineAlpha = 0.12;

  window.__updateParticleTheme = function(theme) {
    if (theme === 'day') {
      pColor1 = '59, 130, 246';
      pColor2 = '245, 158, 11';
      lineAlpha = 0.06;
    } else {
      pColor1 = '0, 242, 254';
      pColor2 = '121, 40, 202';
      lineAlpha = 0.12;
    }
    // Update existing particle colors smoothly
    particles.forEach(p => {
      p.color = Math.random() > 0.5 ? pColor1 : pColor2;
    });
  };

  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      size: Math.random() * 2.2 + 0.8,
      alpha: Math.random() * 0.55 + 0.15,
      color: Math.random() > 0.5 ? pColor1 : pColor2,
      // Subtle twinkling
      twinkleSpeed: Math.random() * 0.02 + 0.005,
      twinklePhase: Math.random() * Math.PI * 2,
    });
  }

  let time = 0;
  function render() {
    time += 1;
    ctx.clearRect(0, 0, width, height);

    // Draw connecting faint lines
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(${pColor1}, ${(1 - dist / 120) * lineAlpha})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw particles with twinkling
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      const twinkle = 0.5 + 0.5 * Math.sin(time * p.twinkleSpeed + p.twinklePhase);
      const alpha = p.alpha * twinkle;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.color}, ${alpha})`;
      ctx.fill();

      // Soft glow around larger particles
      if (p.size > 1.5) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.color}, ${alpha * 0.12})`;
        ctx.fill();
      }
    }

    requestAnimationFrame(render);
  }
  render();

  // Apply initial theme to particles
  window.__updateParticleTheme(ThemeManager.getAutoTheme());
})();

// ==============================================================================
// 3. RADIAL AUDIO WAVEFORM VISUALIZER
// ==============================================================================
(function initRadialVisualizer() {
  const canvas = DOM.visualizerCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  let angleOffset = 0;

  function getThemeColor(alpha) {
    if (ThemeManager.current === 'day') {
      return {
        idle: `rgba(59, 130, 246, ${alpha})`,
        ringing: `rgba(239, 68, 68, ${alpha})`,
        speaking: `rgba(99, 102, 241, ${alpha})`,
        listening: `rgba(16, 185, 129, ${alpha})`,
        thinking: `rgba(168, 85, 247, ${alpha})`,
      };
    }
    return {
      idle: `rgba(0, 242, 254, ${alpha})`,
      ringing: `rgba(255, 42, 95, ${alpha})`,
      speaking: `rgba(79, 172, 254, ${alpha})`,
      listening: `rgba(0, 245, 160, ${alpha})`,
      thinking: `rgba(155, 81, 224, ${alpha})`,
    };
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    angleOffset += 0.02;

    const baseRadius = 115;
    const numPoints = 64;

    let amplitude = 4;
    const colors = getThemeColor(1);
    let waveColor;

    if (STATE.agentState === 'ringing') {
      amplitude = 24 + Math.sin(angleOffset * 5) * 8;
      waveColor = colors.ringing;
    } else if (STATE.agentState === 'speaking') {
      amplitude = 16 + Math.sin(angleOffset * 4) * 6;
      waveColor = colors.speaking;
    } else if (STATE.agentState === 'listening') {
      amplitude = 14 + Math.sin(angleOffset * 3) * 5;
      waveColor = colors.listening;
    } else if (STATE.agentState === 'thinking') {
      amplitude = 8;
      waveColor = colors.thinking;
    } else {
      waveColor = colors.idle;
    }

    // Outer Harmonic Ring
    ctx.beginPath();
    for (let i = 0; i <= numPoints; i++) {
      const angle = (i / numPoints) * Math.PI * 2;
      const wave = Math.sin(angle * 8 + angleOffset) * Math.cos(angle * 4 - angleOffset);
      const r = baseRadius + wave * amplitude;
      const x = cx + Math.cos(angle) * r;
      const y = cy + Math.sin(angle) * r;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = waveColor.replace(/[\d.]+\)$/, '0.6)');
    ctx.lineWidth = 1.8;
    ctx.shadowBlur = 18;
    ctx.shadowColor = waveColor.replace(/[\d.]+\)$/, '0.7)');
    ctx.stroke();

    // Inner Counter Ring
    ctx.beginPath();
    for (let i = 0; i <= numPoints; i++) {
      const angle = (i / numPoints) * Math.PI * 2;
      const wave = Math.cos(angle * 6 - angleOffset * 1.5);
      const r = baseRadius - 15 + wave * (amplitude * 0.6);
      const x = cx + Math.cos(angle) * r;
      const y = cy + Math.sin(angle) * r;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = waveColor.replace(/[\d.]+\)$/, '0.3)');
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.shadowBlur = 0;

    requestAnimationFrame(draw);
  }
  draw();
})();

// ==============================================================================
// 3.5 MOUSE PARALLAX FOR HOLOGRAPHIC ORB
// ==============================================================================
(function initOrbParallax() {
  const orbCore = DOM.orbCore;
  if (!orbCore) return;

  let targetX = 0, targetY = 0;
  let currentX = 0, currentY = 0;

  document.addEventListener('mousemove', (e) => {
    const cx = window.innerWidth / 2;
    const cy = window.innerHeight / 2;
    targetX = ((e.clientX - cx) / cx) * 12;
    targetY = ((e.clientY - cy) / cy) * 12;
  });

  function animate() {
    currentX += (targetX - currentX) * 0.06;
    currentY += (targetY - currentY) * 0.06;
    orbCore.style.transform = `rotateY(${currentX}deg) rotateX(${-currentY}deg)`;
    requestAnimationFrame(animate);
  }
  animate();
})();

// ==============================================================================
// 4. AGENT STATE MANAGER
// ==============================================================================
function setAgentState(newState) {
  STATE.agentState = newState;

  // Clear previous state classes from stage & badge
  DOM.hologramStage.className = 'hologram-stage state-' + newState;
  DOM.agentStateBadge.className = 'agent-state-badge state-' + newState;

  if (newState === 'ringing') {
    const greeting = getActiveGreeting();
    DOM.agentStateLabel.textContent = `🚨 ALARM ACTIVE • WAKE UP BOSS! (Say "${greeting}")`;
    DOM.btnStopAlarm.classList.remove('hidden');
    DOM.footerSpokenStatus.textContent = '*** ALARM RINGING! WAKE UP! ***';
    playBrowserAlarmTone();
  } else {
    DOM.btnStopAlarm.classList.add('hidden');
    stopBrowserAlarmTone();

    if (newState === 'listening') {
      DOM.agentStateLabel.textContent = '🎙️ LISTENING TO BOSS...';
      DOM.footerSpokenStatus.textContent = 'Listening to voice command...';
    } else if (newState === 'speaking') {
      const tod = getActiveTimeOfDay();
      DOM.agentStateLabel.textContent = `🗣️ DELIVERING ${tod.toUpperCase()} BRIEFING`;
      DOM.footerSpokenStatus.textContent = `Speaking ${tod} update`;
    } else if (newState === 'thinking') {
      DOM.agentStateLabel.textContent = '🧠 PROCESSING NEURAL BRIEFING...';
      DOM.footerSpokenStatus.textContent = 'Fetching and compiling news...';
    } else {
      DOM.agentStateLabel.textContent = 'STANDBY • MONITORING ROUTINES';
      DOM.footerSpokenStatus.textContent = 'AI Standby • Ready to assist Boss';
    }
  }
}

// Browser Audio Synthesizer for instant web alarm feedback
let webAudioCtx = null;
let alarmOscillator = null;

function playBrowserAlarmTone() {
  try {
    if (!webAudioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) webAudioCtx = new AudioContext();
    }
    if (webAudioCtx && webAudioCtx.state === 'suspended') {
      webAudioCtx.resume();
    }
    if (DOM.browserAlarmAudio) {
      DOM.browserAlarmAudio.currentTime = 0;
      DOM.browserAlarmAudio.play().catch(() => {});
    }
  } catch (e) {}
}

function stopBrowserAlarmTone() {
  try {
    if (DOM.browserAlarmAudio) {
      DOM.browserAlarmAudio.pause();
      DOM.browserAlarmAudio.currentTime = 0;
    }
  } catch (e) {}
}

// ==============================================================================
// 5. CLOCK & COUNTDOWN ENGINE (GMT+5:30)
// ==============================================================================
function updateLiveClockAndCountdown() {
  // Compute current time in Asia/Kolkata (GMT+5:30) with dd/mm/yyyy date format
  const now = new Date();
  const options = {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  };
  const parts = new Intl.DateTimeFormat('en-GB', options).formatToParts(now);
  const partMap = {};
  parts.forEach(p => partMap[p.type] = p.value);
  const day = partMap.day;
  const month = partMap.month;
  const year = partMap.year;
  const hour = partMap.hour;
  const minute = partMap.minute;
  const second = partMap.second;
  const dayPeriod = (partMap.dayPeriod || '').toUpperCase();
  DOM.liveClock.textContent = `${day}/${month}/${year} ${hour}:${minute}:${second} ${dayPeriod}`.trim();

  // If backend target alarm is known, compute precise diff
  if (STATE.targetAlarmIso) {
    const targetDate = new Date(STATE.targetAlarmIso);
    const diffSec = Math.max(0, Math.floor((targetDate.getTime() - now.getTime()) / 1000));
    const h = Math.floor(diffSec / 3600);
    const m = Math.floor((diffSec % 3600) / 60);
    const s = diffSec % 60;
    DOM.cdHours.textContent = String(h).padStart(2, '0');
    DOM.cdMinutes.textContent = String(m).padStart(2, '0');
    DOM.cdSeconds.textContent = String(s).padStart(2, '0');
    return;
  }

  // Fallback: Compute adaptive 6:30 AM (Mon-Sat) / 7:00 AM (Sun)
  const nowUtc = now.getTime() + now.getTimezoneOffset() * 60000;
  const istNow = new Date(nowUtc + 5.5 * 3600000);

  let targetIst = new Date(istNow);
  const targetHour = targetIst.getDay() === 0 ? 7 : 6;
  const targetMinute = targetIst.getDay() === 0 ? 0 : 30;
  targetIst.setHours(targetHour, targetMinute, 0, 0);

  if (targetIst <= istNow) {
    targetIst.setDate(targetIst.getDate() + 1);
    const nextDayHour = targetIst.getDay() === 0 ? 7 : 6;
    const nextDayMin = targetIst.getDay() === 0 ? 0 : 30;
    targetIst.setHours(nextDayHour, nextDayMin, 0, 0);
  }

  const diffSec = Math.max(0, Math.floor((targetIst - istNow) / 1000));
  const h = Math.floor(diffSec / 3600);
  const m = Math.floor((diffSec % 3600) / 60);
  const s = diffSec % 60;

  DOM.cdHours.textContent = String(h).padStart(2, '0');
  DOM.cdMinutes.textContent = String(m).padStart(2, '0');
  DOM.cdSeconds.textContent = String(s).padStart(2, '0');

  const dayName = targetIst.getDate() === istNow.getDate() ? 'Today' : 'Tomorrow';
  const timeLabel = targetIst.getDay() === 0 ? '07:00:00 AM' : '06:30:00 AM';
  DOM.targetAlarmTime.textContent = `Target: ${dayName} at ${timeLabel} IST (Sun: 7:00 AM)`;
}

setInterval(updateLiveClockAndCountdown, 1000);
updateLiveClockAndCountdown();

// ==============================================================================
// 6. BACKEND REST API SYNCHRONIZATION
// ==============================================================================
async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) return;
    const data = await res.json();

    if (data.platform && DOM.platformText) DOM.platformText.textContent = data.platform;
    if (data.user_title) STATE.userTitle = data.user_title;
    if (data.next_alarm_iso) STATE.targetAlarmIso = data.next_alarm_iso;
    if (data.greeting) STATE.serverGreeting = data.greeting;
    if (data.time_of_day) STATE.serverTimeOfDay = data.time_of_day;

    // Display target time & schedule description
    if (data.next_alarm_str && DOM.targetAlarmTime) {
      const scheduleTag = data.schedule_type || (data.is_custom_alarm ? 'Custom Alarm' : 'Default Schedule');
      DOM.targetAlarmTime.textContent = `Target: ${data.next_alarm_str} (${scheduleTag})`;
    }

    // Location badge sync
    if (data.location && DOM.locationText) {
      const loc = data.location;
      const place = loc.place || 'Local Area';
      const lat = loc.latitude != null ? Number(loc.latitude).toFixed(2) : null;
      const lon = loc.longitude != null ? Number(loc.longitude).toFixed(2) : null;
      const coordsText = (lat && lon) ? ` (${lat}, ${lon})` : '';
      DOM.locationText.textContent = `${place}${coordsText}`;
    }

    // Sleep Lock sync
    STATE.sleepLockActive = !!data.sleep_prevention_active;
    updateSleepLockUI();

    // Alarm & State sync
    STATE.isRinging = !!data.is_ringing;
    if (STATE.isRinging && STATE.agentState !== 'ringing') {
      setAgentState('ringing');
    } else if (!STATE.isRinging && STATE.agentState === 'ringing') {
      setAgentState('idle');
    } else if (data.agent_state && STATE.agentState !== 'ringing') {
      setAgentState(data.agent_state);
    }
  } catch (err) {
    // Backend offline or standalone mode
  }
}

function updateSleepLockUI() {
  if (STATE.sleepLockActive) {
    DOM.wakeLockBtn.classList.remove('inactive');
    DOM.wakeLockText.textContent = 'Sleep Lock: Active';
  } else {
    DOM.wakeLockBtn.classList.add('inactive');
    DOM.wakeLockText.textContent = 'Sleep Lock: Off';
  }
}

// Poll status every 1.5 seconds
setInterval(fetchStatus, 1500);
fetchStatus();

// ==============================================================================
// 7. ACTION BUTTON HANDLERS
// ==============================================================================
DOM.btnSimulateRoutine.addEventListener('click', async () => {
  setAgentState('ringing');
  const greeting = getActiveGreeting();
  appendChatMessage('bot', `⏰ Routine Triggered! Wake up ${STATE.userTitle}! Say '${greeting}' to dismiss.`);
  try {
    await fetch('/api/trigger-routine', { method: 'POST' });
  } catch (e) {}
});

DOM.btnTestAlarm.addEventListener('click', async () => {
  setAgentState('ringing');
  appendChatMessage('bot', '🔔 Testing alarm sound for 5 seconds...');
  try {
    await fetch('/api/test-alarm', { method: 'POST' });
    setTimeout(() => {
      if (STATE.agentState === 'ringing') setAgentState('idle');
    }, 5500);
  } catch (e) {}
});

DOM.btnStopAlarm.addEventListener('click', async () => {
  setAgentState('idle');
  const greeting = getActiveGreeting();
  appendChatMessage('user', 'Dismiss Alarm');
  appendChatMessage('bot', `${greeting} ${STATE.userTitle}, alarm turned off. How can I assist you?`);
  try {
    await fetch('/api/stop-alarm', { method: 'POST' });
  } catch (e) {}
});

DOM.btnFetchNews.addEventListener('click', async () => {
  setAgentState('thinking');
  const tod = getActiveTimeOfDay();
  appendChatMessage('user', `Read the latest ${tod} news`);
  appendChatMessage('bot', `Fetching the latest verified English news for you, ${STATE.userTitle}...`);
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'latest news' }),
    });
    const data = await res.json();
    setAgentState('speaking');
    appendChatMessage('bot', data.reply);
    setTimeout(() => setAgentState('idle'), 6000);
  } catch (e) {
    setAgentState('idle');
  }
});

if (DOM.btnWeather) {
  DOM.btnWeather.addEventListener('click', async () => {
    setAgentState('thinking');
    appendChatMessage('user', "What's today's weather?");
    appendChatMessage('bot', `Checking real-time meteorological reports for you, ${STATE.userTitle}...`);
    try {
      const res = await fetch('/api/weather');
      const data = await res.json();
      setAgentState('speaking');
      const speech = data.speech || "Today's forecast is clear Boss.";
      appendChatMessage('bot', `⛅ ${speech}`);
      // Request backend to speak aloud
      fetch('/api/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: speech }),
      }).catch(() => {});
      setTimeout(() => {
        if (STATE.agentState === 'speaking') setAgentState('idle');
      }, 6500);
    } catch (e) {
      setAgentState('idle');
      appendChatMessage('bot', "Could not retrieve live weather at the moment, Boss.");
    }
  });
}

if (DOM.btnChangeAlarm) {
  DOM.btnChangeAlarm.addEventListener('click', async () => {
    const userInput = prompt(
      `Set Wake-Up Alarm Time for ${STATE.userTitle}:\n\nEnter time (e.g. '7:30 AM', '8:00 AM', '6:15 AM') or type 'reset' for default schedule (6:30 AM weekdays / 7:00 AM Sundays):`,
      "7:00 AM"
    );
    if (!userInput) return;

    if (userInput.trim().toLowerCase() === 'reset') {
      try {
        const res = await fetch('/api/set-alarm-time', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reset: true }),
        });
        const data = await res.json();
        appendChatMessage('user', 'Reset alarm schedule to default');
        appendChatMessage('bot', data.message);
        fetchStatus();
      } catch (e) {}
      return;
    }

    const match = userInput.match(/(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?/i);
    if (match) {
      let h = parseInt(match[1]);
      const m = match[2] ? parseInt(match[2]) : 0;
      const ampm = match[3] ? match[3].toLowerCase() : null;
      if (ampm === 'pm' && h < 12) h += 12;
      if (ampm === 'am' && h === 12) h = 0;

      try {
        const res = await fetch('/api/set-alarm-time', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ hour: h, minute: m }),
        });
        const data = await res.json();
        appendChatMessage('user', `Set alarm to ${userInput}`);
        appendChatMessage('bot', data.message);
        fetchStatus();
      } catch (e) {}
    } else {
      alert("Invalid time format. Please enter e.g. '7:30 AM' or '08:00'.");
    }
  });
}

DOM.wakeLockBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/toggle-sleep', { method: 'POST' });
    const data = await res.json();
    STATE.sleepLockActive = !!data.sleep_prevention_active;
    updateSleepLockUI();
  } catch (e) {}
});

// Spacebar / Enter shortcut to silence alarm
window.addEventListener('keydown', (e) => {
  if ((e.code === 'Space' || e.code === 'Enter') && STATE.agentState === 'ringing') {
    if (document.activeElement !== DOM.chatInput) {
      e.preventDefault();
      DOM.btnStopAlarm.click();
    }
  }
});

// ==============================================================================
// 8. CHAT TRANSCRIPT & SPEECH INPUT
// ==============================================================================
function appendChatMessage(sender, text) {
  const isBot = sender === 'bot';
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${isBot ? 'bot-bubble' : 'user-bubble'}`;

  const avatar = document.createElement('div');
  avatar.className = 'bubble-avatar';
  avatar.textContent = isBot ? '🤖' : '👤';

  const content = document.createElement('div');
  content.className = 'bubble-content';

  const author = document.createElement('div');
  author.className = 'bubble-author';
  author.textContent = isBot ? 'J.A.D. AI Assistant' : STATE.userTitle;

  const textDiv = document.createElement('div');
  textDiv.className = 'bubble-text';
  textDiv.textContent = text;

  content.appendChild(author);
  content.appendChild(textDiv);
  bubble.appendChild(avatar);
  bubble.appendChild(content);

  DOM.chatMessages.appendChild(bubble);
  DOM.chatMessages.scrollTop = DOM.chatMessages.scrollHeight;
}

DOM.chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = DOM.chatInput.value.trim();
  if (!text) return;

  DOM.chatInput.value = '';
  appendChatMessage('user', text);
  setAgentState('thinking');
  showTypingIndicator();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    removeTypingIndicator();
    setAgentState('speaking');
    appendChatMessage('bot', data.reply);
    setTimeout(() => {
      if (STATE.agentState === 'speaking') setAgentState('idle');
    }, 4000);
  } catch (err) {
    removeTypingIndicator();
    setAgentState('idle');
    appendChatMessage('bot', "I received your message Boss. I am standing by.");
  }
});

// Browser Microphone Speech Recognition (Web Speech API)
let speechRecognizer = null;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
  speechRecognizer = new SpeechRecognition();
  speechRecognizer.continuous = false;
  speechRecognizer.interimResults = false;
  speechRecognizer.lang = 'en-US';

  speechRecognizer.onstart = () => {
    STATE.isListeningMic = true;
    DOM.chatMicBtn.classList.add('listening');
    DOM.btnVoiceMic.classList.add('btn-primary');
    DOM.micLabel.textContent = 'Listening...';
    setAgentState('listening');
  };

  speechRecognizer.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    DOM.chatInput.value = transcript;
    DOM.chatForm.dispatchEvent(new Event('submit'));
  };

  speechRecognizer.onerror = () => {
    stopListening();
  };

  speechRecognizer.onend = () => {
    stopListening();
  };
}

function startListening() {
  stopWakeWordListening();
  if (speechRecognizer && !STATE.isListeningMic) {
    try {
      speechRecognizer.start();
    } catch (e) {}
  } else {
    DOM.chatInput.focus();
  }
}

function stopListening() {
  STATE.isListeningMic = false;
  DOM.chatMicBtn.classList.remove('listening');
  DOM.btnVoiceMic.classList.remove('btn-primary');
  DOM.micLabel.textContent = 'Talk to Bot';
  if (STATE.agentState === 'listening') setAgentState('idle');
  // Resume background wake word listening
  setTimeout(startWakeWordListening, 500);
}

DOM.chatMicBtn.addEventListener('click', () => {
  if (STATE.isListeningMic) {
    if (speechRecognizer) speechRecognizer.stop();
  } else {
    startListening();
  }
});

DOM.btnVoiceMic.addEventListener('click', () => {
  if (STATE.isListeningMic) {
    if (speechRecognizer) speechRecognizer.stop();
  } else {
    startListening();
  }
});

// ==============================================================================
// 8.5 WAKE WORD VOICE ACTIVATION ("HELLO JAD" / "HEY JAD")
// ==============================================================================
let wakeWordRecognizer = null;
let isWakeWordActive = true;
let isActivatingFromWake = false;

function playWakeActivationChime() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    // Two-tone cheerful cyber chime (587 Hz D5 -> 880 Hz A5)
    osc.frequency.setValueAtTime(587.33, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12);
    gain.gain.setValueAtTime(0.18, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.35);
  } catch (e) {}
}

function activateAgentByWakeWord(heardText = '', commandAfterWake = '') {
  if (isActivatingFromWake) return;
  isActivatingFromWake = true;

  console.log('[Wake Word Activated]:', heardText, 'Command:', commandAfterWake);
  playWakeActivationChime();

  // Visual indication of activation
  setAgentState('listening');
  if (DOM.agentStateLabel) {
    DOM.agentStateLabel.textContent = "⚡ AGENT ACTIVATED • 'HELLO JAD' HEARD";
  }

  // Display user wake utterance in chat
  appendChatMessage('user', heardText || 'Hello Jad');

  if (commandAfterWake && commandAfterWake.length > 2) {
    // If user said wake word + immediate command (e.g. "Hello Jad what is the weather today"):
    DOM.chatInput.value = commandAfterWake;
    DOM.chatForm.dispatchEvent(new Event('submit'));
    setTimeout(() => { isActivatingFromWake = false; }, 2000);
  } else {
    // User said "Hello Jad", bot replies "How may I help you Boss?", then listens for prompt!
    const wakeReply = `How may I help you ${STATE.userTitle}?`;
    appendChatMessage('bot', wakeReply);
    setAgentState('speaking');

    // Speak acknowledgment
    fetch('/api/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: wakeReply }),
    }).catch(() => {});

    // After acknowledgment, automatically start listening for user's prompt!
    setTimeout(() => {
      isActivatingFromWake = false;
      startListening();
    }, 1800);
  }
}

function initWakeWordListener() {
  if (!SpeechRecognition) return;

  wakeWordRecognizer = new SpeechRecognition();
  wakeWordRecognizer.continuous = true;
  wakeWordRecognizer.interimResults = true;
  wakeWordRecognizer.lang = 'en-US';

  wakeWordRecognizer.onresult = (event) => {
    if (!isWakeWordActive || STATE.isListeningMic || isActivatingFromWake) return;

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript.trim().toLowerCase();
      console.log('[Wake Word stream]:', transcript);

      const isWake = (
        transcript.includes('hello jad') ||
        transcript.includes('hey jad') ||
        transcript.includes('hi jad') ||
        transcript.includes('hello chad') ||
        transcript.includes('hey chad') ||
        transcript.includes('hello chat') ||
        /\bjad\b/i.test(transcript)
      );

      if (isWake) {
        const match = transcript.match(/(?:hello|hey|hi)?\s*(?:jad|chad|chat)\s*(.*)/i);
        const followUp = match && match[1] ? match[1].trim() : '';

        try { wakeWordRecognizer.stop(); } catch (e) {}

        activateAgentByWakeWord(transcript, followUp);
        break;
      }
    }
  };

  wakeWordRecognizer.onerror = (e) => {
    if (isWakeWordActive && e.error !== 'not-allowed' && !STATE.isListeningMic) {
      setTimeout(startWakeWordListening, 1200);
    }
  };

  wakeWordRecognizer.onend = () => {
    if (isWakeWordActive && !STATE.isListeningMic && !isActivatingFromWake) {
      setTimeout(startWakeWordListening, 600);
    }
  };

  startWakeWordListening();
}

function startWakeWordListening() {
  if (!wakeWordRecognizer || !isWakeWordActive || STATE.isListeningMic || isActivatingFromWake) return;
  try {
    wakeWordRecognizer.start();
  } catch (e) {}
}

function stopWakeWordListening() {
  if (wakeWordRecognizer) {
    try { wakeWordRecognizer.stop(); } catch (e) {}
  }
}

if (DOM.wakeWordBtn) {
  DOM.wakeWordBtn.addEventListener('click', () => {
    isWakeWordActive = !isWakeWordActive;
    if (isWakeWordActive) {
      DOM.wakeWordBtn.classList.add('active');
      DOM.wakeWordBtn.classList.remove('inactive');
      DOM.wakeWordText.textContent = 'Wake Word: "Hello Jad"';
      startWakeWordListening();
    } else {
      DOM.wakeWordBtn.classList.remove('active');
      DOM.wakeWordBtn.classList.add('inactive');
      DOM.wakeWordText.textContent = 'Wake Word: Off';
      stopWakeWordListening();
    }
  });
}

// ==============================================================================
// 9. MORNING INTELLIGENCE NEWS FEED
// ==============================================================================
async function loadNewsHeadlines() {
  DOM.newsList.innerHTML = `
    <div class="news-loading">
      <div class="loading-spinner"></div>
      <span>Fetching live Google / BBC news feeds...</span>
    </div>
  `;

  try {
    const res = await fetch('/api/news');
    if (!res.ok) throw new Error();
    const data = await res.json();
    const headlines = data.headlines || [];

    if (headlines.length === 0) {
      DOM.newsList.innerHTML = `<div class="news-loading">No headlines available right now.</div>`;
      return;
    }

    DOM.newsList.innerHTML = '';
    headlines.forEach((title, idx) => {
      const item = document.createElement('div');
      item.className = 'news-item';

      const meta = document.createElement('div');
      meta.className = 'news-meta';

      const tag = document.createElement('span');
      tag.className = 'news-source-tag';
      tag.textContent = `HEADLINE ${idx + 1} • VERIFIED BRIEFING`;

      const speakBtn = document.createElement('button');
      speakBtn.className = 'news-speak-btn';
      speakBtn.title = 'Read this headline aloud';
      speakBtn.textContent = '🔊 Read';

      meta.appendChild(tag);
      meta.appendChild(speakBtn);

      const titleEl = document.createElement('div');
      titleEl.className = 'news-title';
      titleEl.textContent = title;

      item.appendChild(meta);
      item.appendChild(titleEl);

      speakBtn.addEventListener('click', () => {
        setAgentState('speaking');
        fetch('/api/speak', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: `Headline ${idx + 1}: ${title}` }),
        });
        setTimeout(() => {
          if (STATE.agentState === 'speaking') setAgentState('idle');
        }, 3500);
      });

      DOM.newsList.appendChild(item);
    });
  } catch (err) {
    DOM.newsList.innerHTML = '';
    const fallbackTitles = [
      "Global autonomous and intelligence systems release next-generation morning automation tools.",
      "Favorable atmospheric conditions reported across primary metropolitan hubs."
    ];
    fallbackTitles.forEach((ft, i) => {
      const item = document.createElement('div');
      item.className = 'news-item';
      const meta = document.createElement('div');
      meta.className = 'news-meta';
      const tag = document.createElement('span');
      tag.className = 'news-source-tag';
      tag.textContent = i === 0 ? "GLOBAL INTELLIGENCE" : "WEATHER & TECH";
      meta.appendChild(tag);
      const titleEl = document.createElement('div');
      titleEl.className = 'news-title';
      titleEl.textContent = ft;
      item.appendChild(meta);
      item.appendChild(titleEl);
      DOM.newsList.appendChild(item);
    });
  }
}

DOM.btnRefreshNews.addEventListener('click', loadNewsHeadlines);
loadNewsHeadlines();

// ==============================================================================
// 10. WEATHER REFRESH & WELCOME GREETING
// ==============================================================================
function getWeatherEmoji(condition = '') {
  const c = condition.toLowerCase();
  if (c.includes('rain') || c.includes('drizzle')) return '🌧️';
  if (c.includes('thunder') || c.includes('storm')) return '⛈️';
  if (c.includes('snow') || c.includes('ice') || c.includes('sleet')) return '❄️';
  if (c.includes('cloud') || c.includes('overcast')) return '☁️';
  if (c.includes('fog') || c.includes('mist') || c.includes('haze')) return '🌫️';
  if (c.includes('sun') || c.includes('clear')) return '☀️';
  return '⛅';
}

async function loadWeather() {
  if (!DOM.weatherPill) return;
  try {
    const res = await fetch('/api/weather');
    if (!res.ok) return;
    const data = await res.json();
    if (data.status === 'ok') {
      const temp = data.temp_c != null ? `${data.temp_c}°C` : '--';
      const cond = data.condition || 'Clear';
      const city = data.city || 'Kolkata';
      if (DOM.weatherTemp) {
        DOM.weatherTemp.textContent = `${temp} • ${cond} (${city})`;
      }
      if (DOM.weatherIcon) {
        DOM.weatherIcon.textContent = getWeatherEmoji(cond);
      }
      DOM.weatherPill.title = data.speech || `Current weather: ${temp}, ${cond} in ${city}. Click to hear forecast.`;
    }
  } catch (err) {
    if (DOM.weatherTemp) DOM.weatherTemp.textContent = 'Weather Online';
  }
}

if (DOM.weatherPill) {
  DOM.weatherPill.addEventListener('click', () => {
    if (DOM.btnWeather) DOM.btnWeather.click();
  });
}

async function initWelcomeGreeting() {
  const greeting = getActiveGreeting();
  const initialBubble = document.getElementById('initialBotGreeting');
  if (initialBubble) {
    initialBubble.textContent = `${greeting} Boss, how may I help you?`;
  }
  try {
    const res = await fetch('/api/welcome', { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      console.log('Welcome response:', data);
    }
  } catch (err) {
    if ('speechSynthesis' in window && !window.__jadWelcomeSpoken) {
      window.__jadWelcomeSpoken = true;
      const u = new SpeechSynthesisUtterance(`${greeting} Boss, how may I help you?`);
      window.speechSynthesis.speak(u);
    }
  }
}

// Initialize Weather & Welcome Greeting
loadWeather();
setInterval(loadWeather, 10 * 60 * 1000);
initWelcomeGreeting();

// ==============================================================================
// 11. GPS GEOLOCATION & PLACE GEOCODING (FALLBACK)
// ==============================================================================
function initGeolocation() {
  if (!navigator.geolocation) {
    onGeolocationDenied('Geolocation is not supported by your browser.');
    return;
  }

  if (DOM.locationText) DOM.locationText.textContent = 'Acquiring GPS...';

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;
      if (DOM.locationText) DOM.locationText.textContent = `GPS: ${lat.toFixed(2)}, ${lon.toFixed(2)}`;
      if (DOM.locationBanner) DOM.locationBanner.classList.add('hidden');

      try {
        const res = await fetch('/api/location', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ latitude: lat, longitude: lon }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          const loc = data.location;
          if (DOM.locationText) {
            DOM.locationText.textContent = `${loc.place} (${lat.toFixed(2)}, ${lon.toFixed(2)})`;
          }
          loadWeather();
        }
      } catch (e) {}
    },
    (error) => {
      console.warn('Geolocation not permitted or unavailable:', error.message);
      onGeolocationDenied();
    },
    { timeout: 8000, enableHighAccuracy: true }
  );
}

function onGeolocationDenied() {
  if (DOM.locationBanner) {
    DOM.locationBanner.classList.remove('hidden');
  }
  if (DOM.locationText) DOM.locationText.textContent = 'Set Location 📍';

  if (!window.__jadLocationPrompted) {
    window.__jadLocationPrompted = true;
    const promptMsg = "📍 Location permission was not granted. Where are you currently located at?";
    appendChatMessage('bot', promptMsg);
    fetch('/api/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: "Where are you currently located at?" }),
    }).catch(() => {});
  }
}

async function submitPlaceLocation(placeName) {
  if (!placeName) return;
  setAgentState('thinking');
  appendChatMessage('user', `My location is ${placeName}`);
  appendChatMessage('bot', `Searching coordinates and meteorological forecast for ${placeName}...`);

  try {
    const res = await fetch('/api/location', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ place: placeName }),
    });
    const data = await res.json();

    if (data.status === 'ok') {
      const loc = data.location;
      if (DOM.locationText) {
        DOM.locationText.textContent = `${loc.place} (${loc.latitude.toFixed(2)}, ${loc.longitude.toFixed(2)})`;
      }
      if (DOM.locationBanner) DOM.locationBanner.classList.add('hidden');
      setAgentState('speaking');
      const w = data.weather || {};
      const speech = `Location synchronized to ${loc.display_name}. Current weather is ${w.temp_c || '--'} degrees Celsius with ${(w.condition || 'clear skies').toLowerCase()}.`;
      appendChatMessage('bot', speech);
      fetch('/api/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: speech }),
      }).catch(() => {});
      loadWeather();
      setTimeout(() => setAgentState('idle'), 6000);
    } else {
      setAgentState('idle');
      appendChatMessage('bot', data.error || `Could not find coordinates for ${placeName}. Please try another city name.`);
    }
  } catch (e) {
    setAgentState('idle');
    appendChatMessage('bot', 'Network error while geocoding place. Please check internet connection.');
  }
}

if (DOM.locationForm) {
  DOM.locationForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const val = DOM.locationInput ? DOM.locationInput.value.trim() : '';
    if (val) {
      if (DOM.locationInput) DOM.locationInput.value = '';
      submitPlaceLocation(val);
    }
  });
}

if (DOM.btnCloseBanner) {
  DOM.btnCloseBanner.addEventListener('click', () => {
    if (DOM.locationBanner) DOM.locationBanner.classList.add('hidden');
  });
}

if (DOM.locationBadge) {
  DOM.locationBadge.addEventListener('click', () => {
    const place = prompt(`Enter your city or place name for ${STATE.userTitle}:`, 'Kolkata');
    if (place) submitPlaceLocation(place);
  });
}

// Start GPS geolocation detection & Wake Word Voice Activation
initGeolocation();
initWakeWordListener();

// ==============================================================================
// 12. THEME MANAGER INITIALIZATION
// ==============================================================================
ThemeManager.init();

// ==============================================================================
// 13. CHAT TYPING INDICATOR
// ==============================================================================
function showTypingIndicator() {
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble bot-bubble';
  bubble.id = 'typingBubble';

  const avatar = document.createElement('div');
  avatar.className = 'bubble-avatar';
  avatar.textContent = '🤖';

  const content = document.createElement('div');
  content.className = 'bubble-content';

  const author = document.createElement('div');
  author.className = 'bubble-author';
  author.textContent = 'J.A.D. AI Assistant';

  const indicator = document.createElement('div');
  indicator.className = 'bubble-text typing-indicator';
  indicator.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

  content.appendChild(author);
  content.appendChild(indicator);
  bubble.appendChild(avatar);
  bubble.appendChild(content);

  DOM.chatMessages.appendChild(bubble);
  DOM.chatMessages.scrollTop = DOM.chatMessages.scrollHeight;
  return bubble;
}

function removeTypingIndicator() {
  const el = document.getElementById('typingBubble');
  if (el) el.remove();
}

