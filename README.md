<div align="center">

# ⚡ J.A.D. • Agentic AI Bot
### *Autonomous Personal Morning Intelligence & Wake-Up Agent*

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Android-00f2fe?style=for-the-badge&logo=apple&logoColor=white)](https://github.com/)
[![Status](https://img.shields.io/badge/Status-Development%20Phase-ffaa00?style=for-the-badge&logo=git&logoColor=white)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-00f5a0?style=for-the-badge)](LICENSE)
[![Zero-Dependency Core](https://img.shields.io/badge/Dependencies-Standard%20Library%20Only-7928ca?style=for-the-badge)](requirements.txt)

<br/>

**An intelligent autonomous companion engineered in Python to orchestrate precision routines, interactive voice conversations, and real-time morning intelligence briefings.**

[Key Features](#-features) • [Visual UI/UX](#-animated-ai-agent-dashboard) • [Quick Start](#-quick-start) • [Architecture](#-project-architecture) • [Security](#-security-hardening)

</div>

---

## 🌌 Overview

**J.A.D.** *(Just Another Daily assistant)* is an **agentic AI bot** in active development, engineered from the ground up in Python. Unlike passive alarms or simple scripts, JAD functions as a proactive agent:

- ⏰ **Self-Governing Scheduler**: Operates continuously in low-power standby, monitoring for scheduled routines (**6:00:00 AM IST** / GMT+5:30).
- 🧠 **Context-Aware Dialogue**: Rings until greeted, asks how it can assist, and understands voice or text commands.
- 🌐 **Live Intelligence Synthesis**: Dispatches real-time web grounding via **Google Gemini API** (`gemini-3.6-flash`) with automatic fallback to live verified RSS news feeds.
- 🔋 **Desktop-Aware Energy Management**: Automatically acquires system wake-locks (`caffeinate` on Mac, `SetThreadExecutionState` on Windows) so your laptop never sleeps through an alarm.

---

## ✨ Features

| Feature | Description | Platform Support |
| :--- | :--- | :--- |
| **🤖 3D AI Hologram** | Real-time orbital ring animations, audio reactive waves, and dynamic state aura. | Browser / Desktop UI |
| **👋 Spoken Welcome** | Voice greeting on launch: *"Hello Boss, how may I help you?"* | macOS say / SAPI5 |
| **⏰ Adaptive Alarm** | Default 6:30 AM weekdays, 7:00 AM Sundays; adjust anytime by voice or chat. | Cross-Platform |
| **📍 Smart Geolocation** | Automatic GPS lat/long detection with interactive place-name geocoding fallback. | HTML5 / Open-Meteo |
| **⛅ Real-Time Weather** | Live local weather & forecasts with umbrella / hydration advice. | wttr.in / Open-Meteo |
| **🗣️ Conversational Voice** | Bi-directional voice engine supporting macOS `say`, Windows SAPI5, and Web Speech STT. | macOS, Windows, Android |
| **📰 Morning Briefing** | Live breaking news in conversational spoken English with zero markdown artifacts. | Global (Gemini / RSS) |
| **🛡️ Zero-Dependency Core** | Runs 100% out-of-the-box using the Python 3.9+ standard library. | Cross-Platform |
| **🔒 Security Hardened** | Protected against XSS, command injection, and cross-origin hijacking. | End-to-End |

---

## 🎨 Animated AI Agent Dashboard

JAD features a cyberpunk, glassmorphic visual interface served locally via a zero-dependency Python HTTP server (`http://localhost:8000`):


---

## 🚀 Quick Start

### 1. Prerequisites
- Python **3.9+** (Standard installation, zero pip packages needed for core operation).

### 2. Launching JAD

<table>
<tr>
<th>🍎 macOS Desktop</th>
<th>🪟 Windows Desktop</th>
<th>📟 Terminal / Headless</th>
</tr>
<tr>
<td>

```bash
./run_desktop_mac.sh
# or
python3 main.py
```
*Auto-launches browser & caffeinate sleep lock.*

</td>
<td>

```powershell
.\run_desktop_windows.bat
# or
python main.py
```
*Auto-launches browser & Windows sleep lock.*

</td>
<td>

```bash
python3 main.py --cli
```
*Runs purely inside your terminal window.*

</td>
</tr>
</table>

---

## 🛠️ Testing & Simulation Commands

Test any component immediately without waiting for 6:00 AM:

```bash
# 1. Check countdown to next alarm & current IST time
python3 main.py --status

# 2. Simulate complete 6:00 AM wake-up routine right now
python3 main.py --now

# 3. Test alarm audio ringer for 5 seconds
python3 main.py --test-alarm

# 4. Test native OS banner/toast notification
python3 main.py --test-notification

# 5. Fetch and speak today's morning news briefing
python3 main.py --test-news

# 6. Fetch and speak today's live weather forecast
python3 main.py --test-weather
```

---

## 📁 Project Architecture

The codebase follows a modular package architecture under `src/`:

```
jad-bot/
├── src/
│   ├── core/                  # Configuration & bot orchestrator
│   │   ├── config.py          # Environment settings loader
│   │   └── bot.py             # WakeUpBot scheduling & routine coordinator
│   ├── audio/                 # Audio playback & voice synthesis
│   │   ├── alarm.py           # Cross-platform AlarmController & tone generator
│   │   └── voice.py           # VoiceEngine (macOS say, Windows SAPI/pyttsx3)
│   ├── services/              # External intelligence & data feeds
│   │   ├── news.py            # Gemini API & RSS news parser
│   │   └── weather.py         # Real-time weather client (wttr.in / Open-Meteo)
│   ├── platform_util/         # OS detection, wake-locks & notifications
│   │   └── desktop.py         # Caffeinate, SetThreadExecutionState, notifications
│   └── server/                # Local UI & REST API server
│       └── web.py             # Hardened ThreadingHTTPServer & endpoints
├── assets/                    # Audio tone assets (alarm_sound.wav)
├── ui/                        # Web dashboard static files (HTML, CSS, JS)
├── tests/                     # Automated unit and security test suite
│   ├── test_desktop.py        # Desktop platform & speech tests
│   └── test_security.py       # CORS, DoS, and permission tests
├── .env                       # Local secrets (chmod 600, gitignored)
├── .gitignore                 # Protected git rules
├── main.py                    # Root entrypoint
├── requirements.txt           # Optional dependencies for physical mic STT
├── run_desktop_mac.sh         # macOS one-click launcher
└── run_desktop_windows.bat    # Windows one-click launcher
```

---

## 🔑 Gemini API Configuration (Optional)

JAD features out-of-the-box live search grounding via Google Gemini. If no key is configured, it automatically falls back to live RSS news feeds without failing.

To configure your key, add it to `.env`:

```env
GEMINI_API_KEY="AIzaSy...your_gemini_api_key_here"
```

---

## 🛡️ Security Hardening

- 🔒 **XSS Defense**: UI dynamically renders news headlines strictly using safe `textContent` DOM nodes.
- 🛡️ **Command Injection Immunity**: Replaced shell string formatting (`os.system`) with native Windows API `SetConsoleTitleW` and parameter bindings for AppleScript (`on run argv`) and PowerShell (`$args[0]`).
- 🌐 **Strict CORS Policy**: Local API rejects all non-localhost origins with `403 Forbidden`.
- 🛑 **DoS Protection**: Incoming HTTP request payloads are strictly capped at 64KB (`413 Payload Too Large`).
- 🔐 **Secrets Protection**: `.env` is locked to `chmod 600` and permanently ignored in `.gitignore`.

Run the automated test suite:
```bash
python3 -m unittest -v tests/test_desktop.py tests/test_security.py
```

---

<div align="center">

### 🚧 Development Roadmap

`[x] Core Audio Engine` • `[x] Cross-Platform Desktop` • `[x] Animated 3D UI` • `[x] Security Hardening`  
`[ ] Local Offline LLM Integration` • `[ ] Smart Home (Home Assistant) Webhook Trigger` • `[ ] Mobile Companion App`

<br/>

*Built with ❤️ in Python • Designed for productive mornings.*

</div>
