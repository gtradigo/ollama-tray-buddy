from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class State(Enum):
    UNKNOWN = "unknown"   # not checked yet
    OFFLINE = "offline"   # host unreachable / error
    IDLE = "idle"         # server up, no model loaded
    BUSY = "busy"         # server up, at least one model loaded in memory


@dataclass
class LoadedModel:
    name: str
    size_vram: int = 0
    size: int = 0
    expires_at: str = ""


@dataclass
class Status:
    state: State = State.UNKNOWN
    version: str = ""
    models: list[LoadedModel] = field(default_factory=list)
    error: str = ""


LABELS = {
    State.UNKNOWN: "Checking…",
    State.OFFLINE: "Offline",
    State.IDLE: "Running (idle)",
    State.BUSY: "Running — model loaded",
}


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{n} B"
