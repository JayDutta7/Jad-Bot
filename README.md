<div align="center">

# ⚡ J.A.D. • Agentic AI Bot
### *Autonomous Personal Intelligence Agent*

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


## 🔑 Gemini API Configuration (Optional)

JAD features out-of-the-box live search grounding via Google Gemini. If no key is configured, it automatically falls back to live RSS news feeds without failing.

To configure your key, add it to `.env`:

```env
GEMINI_API_KEY="AIzaSy...your_gemini_api_key_here"
```

---

<div align="center">

### 🚧 Development Roadmap

`[x] Core Audio Engine` • `[x] Cross-Platform Desktop` • `[x] Animated 3D UI` • `[x] Security Hardening`  
`[ ] Local Offline LLM Integration` • `[ ] Smart Home (Home Assistant) Webhook Trigger` • `[ ] Mobile Companion App`

<br/>

*Built with ❤️ in Python • Designed for productive mornings.*

</div>
