"""Asynchronous polling of an Ollama server via Qt networking (no threads)."""

from __future__ import annotations

import json

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from .status import LoadedModel, State, Status

TIMEOUT_MS = 3000


class OllamaMonitor(QObject):
    updated = pyqtSignal(object)  # Status

    def __init__(self, host: str, interval: int, parent=None):
        super().__init__(parent)
        self.host = host
        self.nam = QNetworkAccessManager(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.set_interval(interval)
        self._busy = False
        self._generation = 0  # invalidates in-flight replies after host change

    def set_interval(self, seconds: int) -> None:
        self.timer.setInterval(max(1, seconds) * 1000)

    def set_host(self, host: str) -> None:
        self.host = host
        self._generation += 1
        self._busy = False
        self.poll()

    def start(self) -> None:
        self.timer.start()
        self.poll()

    def _get(self, path: str, callback) -> None:
        req = QNetworkRequest(QUrl(self.host + path))
        req.setTransferTimeout(TIMEOUT_MS)
        reply = self.nam.get(req)
        gen = self._generation
        reply.finished.connect(lambda: self._done(reply, gen, callback))

    def _done(self, reply: QNetworkReply, gen: int, callback) -> None:
        reply.deleteLater()
        if gen != self._generation:
            return
        if reply.error() != QNetworkReply.NetworkError.NoError:
            callback(None, reply.errorString())
            return
        try:
            callback(json.loads(bytes(reply.readAll()).decode() or "{}"), "")
        except ValueError as e:
            callback(None, f"Invalid response: {e}")

    def poll(self) -> None:
        if self._busy:
            return
        self._busy = True

        def on_version(data, err):
            if data is None:
                self._finish(Status(State.OFFLINE, error=err))
                return
            version = str(data.get("version", ""))
            self._get("/api/ps", lambda d, e: on_ps(version, d, e))

        def on_ps(version, data, err):
            if data is None:
                # server answered /api/version, so it's up; ps failed though
                self._finish(Status(State.IDLE, version=version, error=err))
                return
            models = [
                LoadedModel(
                    name=m.get("name") or m.get("model", "?"),
                    size_vram=int(m.get("size_vram") or 0),
                    size=int(m.get("size") or 0),
                    expires_at=m.get("expires_at", ""),
                )
                for m in data.get("models") or []
            ]
            state = State.BUSY if models else State.IDLE
            self._finish(Status(state, version=version, models=models))

        self._get("/api/version", on_version)

    def _finish(self, status: Status) -> None:
        self._busy = False
        self.updated.emit(status)
