from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

APP_ID = "ollama-tray-buddy"
DEFAULT_HOST = "http://localhost:11434"


def _config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_ID


CONFIG_FILE = _config_dir() / "config.json"
AUTOSTART_FILE = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") \
    / "autostart" / f"{APP_ID}.desktop"


def normalize_host(host: str) -> str:
    host = (host or "").strip().rstrip("/")
    if not host:
        return DEFAULT_HOST
    if "://" not in host:
        host = "http://" + host
    return host


@dataclass
class Config:
    host: str = DEFAULT_HOST
    interval: int = 5          # seconds between polls
    notify: bool = True        # desktop notification on state change

    @classmethod
    def load(cls) -> "Config":
        cfg = cls()
        try:
            data = json.loads(CONFIG_FILE.read_text())
            for k in ("host", "interval", "notify"):
                if k in data:
                    setattr(cfg, k, data[k])
        except (OSError, ValueError):
            pass
        env_host = os.environ.get("OLLAMA_TRAY_HOST")
        if env_host:
            cfg.host = env_host
        cfg.host = normalize_host(cfg.host)
        cfg.interval = max(1, int(cfg.interval))
        return cfg

    def save(self) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2) + "\n")


def autostart_enabled() -> bool:
    return AUTOSTART_FILE.exists()


def set_autostart(enabled: bool, exec_cmd: str) -> None:
    if not enabled:
        AUTOSTART_FILE.unlink(missing_ok=True)
        return
    AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTOSTART_FILE.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Ollama Tray Buddy\n"
        "Comment=Show Ollama status in the system tray\n"
        f"Exec={exec_cmd}\n"
        "Icon=ollama-tray-buddy\n"
        "X-GNOME-Autostart-enabled=true\n"
        "X-GNOME-Autostart-Delay=5\n"
    )
