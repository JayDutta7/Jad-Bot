/**
 * J.A.D. AI MORNING ASSISTANT & WAKE-UP AGENT - CLIENT LOGIC
 * Features: 3D Holographic Orb Controller, Canvas Particle Field, Radial Visualizer,
 * Real-Time IST Clock & Countdown, Web Speech STT/TTS, and REST API Sync.
 */

// ==============================================================================
// 1. STATE & CONSTANTS
// ==============================================================================
const STATE = {
  agentState: 'idle', // 'idle' | 'ringing' | 'listening' | 'thinking' | 'speaking'
  isRinging: false,
  sleepLockActive: true,
  platform: 'Desktop',
  userTitle: 'Boss',
  targetAlarmIso: null,
  browserAudioActive: false,
  isListeningMic: false,
};

// DOM Elements
const DOM = {
  liveClock: document.getElementById('liveClock'),
  platformText: document.getElementById('platformText'),
  wakeLockBtn: document.getElementById('wakeLockBtn'),
  wakeLockText: document.getElementById('wakeLockText'),
  wakeLockDot: document.getElementById('wakeLockDot'),
  hologramStage: document.getElementById('hologramStage'),
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
  const count = Math.min(80, Math.floor(width / 20));

  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      size: Math.random() * 2 + 1,
      alpha: Math.random() * 0.6 + 0.2,
      color: Math.random() > 0.5 ? '0, 242, 254' : '121, 40, 202',
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    // Draw connecting faint lines
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 110) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(0, 242, 254, ${(1 - dist / 110) * 0.12})`;
          ctx.lineWidth = 0.6;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw particles
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.color}, ${p.alpha})`;
      ctx.fill();
    }

    requestAnimationFrame(render);
  }
  render();
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

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    angleOffset += 0.02;

    const baseRadius = 115;
    const numPoints = 64;

    // Amplitude based on current agent state
    let amplitude = 4;
    let waveColor = 'rgba(0, 242, 254, ';

    if (STATE.agentState === 'ringing') {
      amplitude = 24 + Math.sin(angleOffset * 5) * 8;
      waveColor = 'rgba(255, 42, 95, ';
    } else if (STATE.agentState === 'speaking') {
      amplitude = 16 + Math.sin(angleOffset * 4) * 6;
      waveColor = 'rgba(79, 172, 254, ';
    } else if (STATE.agentState === 'listening') {
      amplitude = 14 + Math.sin(angleOffset * 3) * 5;
      waveColor = 'rgba(0, 245, 160, ';
    } else if (STATE.agentState === 'thinking') {
      amplitude = 8;
      waveColor = 'rgba(155, 81, 224, ';
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
    ctx.strokeStyle = waveColor + '0.6)';
    ctx.lineWidth = 1.8;
    ctx.shadowBlur = 15;
    ctx.shadowColor = waveColor + '0.8)';
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
    ctx.strokeStyle = waveColor + '0.35)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.shadowBlur = 0;

    requestAnimationFrame(draw);
  }
  draw();
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
    DOM.agentStateLabel.textContent = '🚨 ALARM ACTIVE • WAKE UP BOSS! (Say "Good morning")';
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
      DOM.agentStateLabel.textContent = '🗣️ DELIVERING MORNING BRIEFING';
      DOM.footerSpokenStatus.textContent = 'Speaking morning update';
    } else if (newState === 'thinking') {
      DOM.agentStateLabel.textContent = '🧠 PROCESSING NEURAL BRIEFING...';
      DOM.footerSpokenStatus.textContent = 'Fetching and compiling news...';
    } else {
      DOM.agentStateLabel.textContent = 'STANDBY • MONITORING DAILY 6:00 AM IST';
      DOM.footerSpokenStatus.textContent = 'AI Standby • Ready to awaken Boss at 6:00 AM';
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
  // Compute current time in Asia/Kolkata (GMT+5:30)
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
  const formatter = new Intl.DateTimeFormat('en-US', options);
  DOM.liveClock.textContent = formatter.format(now);

  // Calculate countdown to next 6:00 AM IST
  // Convert current UTC time to IST timestamp
  const nowUtc = now.getTime() + now.getTimezoneOffset() * 60000;
  const istNow = new Date(nowUtc + 5.5 * 3600000);

  let targetIst = new Date(istNow);
  targetIst.setHours(6, 0, 0, 0);

  if (targetIst <= istNow) {
    targetIst.setDate(targetIst.getDate() + 1);
  }

  const diffSec = Math.max(0, Math.floor((targetIst - istNow) / 1000));
  const h = Math.floor(diffSec / 3600);
  const m = Math.floor((diffSec % 3600) / 60);
  const s = diffSec % 60;

  DOM.cdHours.textContent = String(h).padStart(2, '0');
  DOM.cdMinutes.textContent = String(m).padStart(2, '0');
  DOM.cdSeconds.textContent = String(s).padStart(2, '0');

  const dayName = targetIst.getDate() === istNow.getDate() ? 'Today' : 'Tomorrow';
  DOM.targetAlarmTime.textContent = `Target: ${dayName} at 06:00:00 AM IST`;
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

    if (data.platform) DOM.platformText.textContent = data.platform;
    if (data.user_title) STATE.userTitle = data.user_title;

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
  appendChatMessage('bot', `⏰ 6:00 AM Routine Triggered! Wake up ${STATE.userTitle}! Say 'Good morning' to dismiss.`);
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
  appendChatMessage('user', 'Dismiss Alarm');
  appendChatMessage('bot', `Good morning ${STATE.userTitle}, alarm turned off. How can I assist you?`);
  try {
    await fetch('/api/stop-alarm', { method: 'POST' });
  } catch (e) {}
});

DOM.btnFetchNews.addEventListener('click', async () => {
  setAgentState('thinking');
  appendChatMessage('user', 'Read the latest morning news');
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
  author.textContent = isBot ? 'J.A.D. Morning Assistant' : STATE.userTitle;

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

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    setAgentState('speaking');
    appendChatMessage('bot', data.reply);
    setTimeout(() => {
      if (STATE.agentState === 'speaking') setAgentState('idle');
    }, 4000);
  } catch (err) {
    setAgentState('idle');
    appendChatMessage('bot', "I received your message Boss. I am standing by for 6:00 AM.");
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
  if (speechRecognizer && !STATE.isListeningMic) {
    try {
      speechRecognizer.start();
    } catch (e) {}
  } else {
    // Fallback focus to input
    DOM.chatInput.focus();
  }
}

function stopListening() {
  STATE.isListeningMic = false;
  DOM.chatMicBtn.classList.remove('listening');
  DOM.btnVoiceMic.classList.remove('btn-primary');
  DOM.micLabel.textContent = 'Talk to Bot';
  if (STATE.agentState === 'listening') setAgentState('idle');
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
