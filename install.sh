#!/usr/bin/env bash
# AMARTIE Trade Witness — one-command installer.
# Installs ffmpeg (if missing), installs the package, writes config, and
# enables auto-start on login (systemd user service on Linux).
set -euo pipefail

U="\033[1;34m"; G="\033[1;32m"; R="\033[1;31m"; Z="\033[0m"
echo -e "${U}AMARTIE Trade Witness — installer${Z}"

# --- platform ---
OS="$(uname -s)"
PY="${PYTHON:-python3}"

# --- 1) ffmpeg (screen capture) ---
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo -e "${R}ffmpeg not found — this is required for screen capture.${Z}"
  case "$OS" in
    Linux)
      if command -v apt-get >/dev/null; then sudo apt-get install -y ffmpeg
      elif command -v dnf >/dev/null; then sudo dnf install -y ffmpeg
      else echo "install ffmpeg with your package manager, then re-run."; exit 1; fi ;;
    Darwin)
      command -v brew >/dev/null && brew install ffmpeg || { echo "install homebrew + ffmpeg, then re-run."; exit 1; } ;;
    *) echo "install ffmpeg, then re-run."; exit 1 ;;
  esac
fi
echo -e "${G}ffmpeg: $(ffmpeg -version 2>/dev/null | head -1)${Z}"

# --- 2) install the package ---
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$PY" -m pip install --user -e "$HERE" >/dev/null 2>&1 \
  || { echo -e "${R}pip install failed — installing with pip install -e requires pip.${Z}"; exit 1; }
echo -e "${G}package installed${Z}"

# --- 3) config ---
CFG="${XDG_CONFIG_HOME:-$HOME/.config}/trade-witness/config.json"
if [ ! -f "$CFG" ]; then
  "$PY" - <<'PY'
from trade_witness.config import Config
Config().save()
print("wrote default config")
PY
fi
echo -e "${G}config: $CFG${Z}"

# --- 4) auto-start on login ---
if [ "$OS" = "Linux" ] && command -v systemctl >/dev/null 2>&1; then
  mkdir -p "$HOME/.config/systemd/user"
  cat > "$HOME/.config/systemd/user/trade-witness.service" <<EOF
[Unit]
Description=AMARTIE Trade Witness (automatic trading witness)
After=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY=${DISPLAY:-:0}
ExecStart=${PY} -m trade_witness
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable trade-witness.service
  systemctl --user start trade-witness.service
  echo -e "${G}auto-start enabled (systemd user service: trade-witness)${Z}"
elif [ "$OS" = "Darwin" ]; then
  echo -e "macOS: install a launchd agent (LaunchAgents/trade-witness.plist) — see README."
else
  echo "auto-start: run \`trade-witness\` or \`python3 -m trade_witness\` at login."
fi

echo ""
echo -e "${G}Done. It now runs automatically and witnesses every session.${Z}"
echo -e "  status : trade-witness status"
echo -e "  record : trade-witness record --duration 10"
echo -e "  report : trade-witness report --session <id>"