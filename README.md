# Ollama Tray Buddy

A tiny Linux system-tray app that shows the status of an [Ollama](https://ollama.com) server
with a friendly llama icon.

| <img src="assets/unknown.svg" width="64"> | <img src="assets/offline.svg" width="64"> | <img src="assets/idle.svg" width="64"> | <img src="assets/busy.svg" width="64"> |
|:---:|:---:|:---:|:---:|
| Checking… | Offline | Running (idle) | Model loaded |

## Features

- Polls `/api/version` and `/api/ps` on the configured host
- Icon changes with the state: offline, running/idle, model loaded in memory
- Menu with version, loaded models (and VRAM used), last check time
- Configurable host (default `http://localhost:11434`) and polling interval
- Optional desktop notifications when the state changes
- Optional start at login

## Requirements

- Python 3.9+
- PyQt6 (`pip install PyQt6`)
- A desktop with a system tray. On **GNOME** you need the
  *AppIndicator and KStatusNotifierItem Support* extension
  (pre-installed and enabled on Ubuntu).

## Install

```bash
git clone https://github.com/gtradigo/ollama-tray-buddy.git
cd ollama-tray-buddy
./install.sh
```

This installs the `ollama-tray-buddy` command for your user, plus an app-menu entry and icon.

Or run it straight from the source tree:

```bash
python3 -m ollama_tray_buddy
```

## Configuration

Open **Settings…** from the tray menu, or use the command line:

```bash
ollama-tray-buddy --host http://192.168.1.50:11434 --interval 10
```

Options given on the command line are saved. Settings are stored in
`~/.config/ollama-tray-buddy/config.json`:

```json
{
  "host": "http://localhost:11434",
  "interval": 5,
  "notify": true
}
```

The environment variable `OLLAMA_TRAY_HOST` overrides the host for a single run.

## License

MIT. The llama icon is an original drawing inspired by the Ollama mascot;
Ollama is a trademark of its respective owners and this project is not affiliated with it.
