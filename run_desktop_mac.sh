#!/usr/bin/env bash
# ==============================================================================
# 🌅 Daily 6:00 AM Wake Up & Morning Assistant Bot - macOS Desktop Launcher
# ==============================================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================="
echo "🌅 Launching Wake Up Bot on macOS Desktop"
echo "⏰ Daily Alarm Time: 6:00 AM IST (GMT+5:30)"
echo "☕ Automatic sleep prevention (caffeinate) enabled"
echo "======================================================="

python3 main.py "$@"
