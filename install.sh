#!/usr/bin/env bash
# Installs Ollama Tray Buddy for the current user (no root needed).
set -euo pipefail
cd "$(dirname "$0")"

python3 -m pip install --user --upgrade .

install -Dm644 assets/ollama-tray-buddy.svg \
    "$HOME/.local/share/icons/hicolor/scalable/apps/ollama-tray-buddy.svg"
install -Dm644 assets/ollama-tray-buddy.desktop \
    "$HOME/.local/share/applications/ollama-tray-buddy.desktop"
gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "Installed. Launch 'Ollama Tray Buddy' from the app menu or run: ollama-tray-buddy &"
