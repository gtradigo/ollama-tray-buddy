from __future__ import annotations

import shlex
import shutil
import signal
import sys
from datetime import datetime

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSpinBox,
    QSystemTrayIcon,
)

from . import __version__
from .config import (
    APP_ID,
    DEFAULT_HOST,
    Config,
    autostart_enabled,
    normalize_host,
    set_autostart,
)
from .icons import icon_for
from .monitor import OllamaMonitor
from .status import LABELS, State, Status, human_size


def _exec_command() -> str:
    exe = shutil.which(APP_ID)
    if exe:
        return exe
    return f"{shlex.quote(sys.executable)} -m ollama_tray_buddy"


class SettingsDialog(QDialog):
    def __init__(self, cfg: Config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ollama Tray Buddy — Settings")
        self.setWindowIcon(icon_for(State.IDLE))
        form = QFormLayout(self)

        self.host = QLineEdit(cfg.host)
        self.host.setPlaceholderText(DEFAULT_HOST)
        self.host.setMinimumWidth(280)
        form.addRow("Ollama host:", self.host)

        self.interval = QSpinBox()
        self.interval.setRange(1, 3600)
        self.interval.setSuffix(" s")
        self.interval.setValue(cfg.interval)
        form.addRow("Check every:", self.interval)

        self.notify = QCheckBox("Notify when the status changes")
        self.notify.setChecked(cfg.notify)
        form.addRow(self.notify)

        self.autostart = QCheckBox("Start automatically at login")
        self.autostart.setChecked(autostart_enabled())
        form.addRow(self.autostart)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            lambda: (self.host.setText(DEFAULT_HOST), self.interval.setValue(5))
        )
        form.addRow(buttons)


class TrayBuddy:
    def __init__(self, app: QApplication):
        self.app = app
        self.cfg = Config.load()
        self.status = Status()
        self.last_check: datetime | None = None
        self.dialog: SettingsDialog | None = None

        self.tray = QSystemTrayIcon(icon_for(State.UNKNOWN))
        self.menu = QMenu()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)

        self.monitor = OllamaMonitor(self.cfg.host, self.cfg.interval)
        self.monitor.updated.connect(self.on_status)

        self._rebuild_menu()
        self.tray.show()
        self.monitor.start()

    # ---- UI -------------------------------------------------------------
    def _rebuild_menu(self) -> None:
        m = self.menu
        m.clear()
        s = self.status

        def info(text: str) -> None:
            a = m.addAction(text)
            a.setEnabled(False)

        info(f"Ollama: {LABELS[s.state]}")
        info(f"Host: {self.cfg.host}")
        if s.version:
            info(f"Version: {s.version}")
        if s.state == State.OFFLINE and s.error:
            info(f"Error: {s.error[:70]}")
        if s.models:
            m.addSeparator()
            info("Loaded models:")
            for model in s.models:
                vram = f" — {human_size(model.size_vram)} VRAM" if model.size_vram else ""
                info(f"   • {model.name}{vram}")
        if self.last_check:
            info(f"Last check: {self.last_check:%H:%M:%S}")

        m.addSeparator()
        refresh = m.addAction("Refresh now")
        refresh.triggered.connect(self.monitor.poll)
        open_host = m.addAction("Open host in browser")
        open_host.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(self.cfg.host)))
        settings = m.addAction("Settings…")
        settings.triggered.connect(self.open_settings)
        about = m.addAction("About")
        about.triggered.connect(self.about)
        m.addSeparator()
        quit_action = QAction("Quit", m)
        quit_action.triggered.connect(self.app.quit)
        m.addAction(quit_action)

    def _tooltip(self) -> str:
        s = self.status
        lines = [f"Ollama: {LABELS[s.state]}", self.cfg.host]
        if s.version:
            lines.append(f"v{s.version}")
        for model in s.models:
            lines.append(f"• {model.name}")
        return "\n".join(lines)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.monitor.poll()

    # ---- logic ----------------------------------------------------------
    def on_status(self, status: Status) -> None:
        prev = self.status
        self.status = status
        self.last_check = datetime.now()
        self.tray.setIcon(icon_for(status.state))
        self.tray.setToolTip(self._tooltip())
        self._rebuild_menu()

        if self.cfg.notify and prev.state != State.UNKNOWN and prev.state != status.state:
            self._notify(prev, status)

    def _notify(self, prev: Status, new: Status) -> None:
        if new.state == State.OFFLINE:
            title, msg, kind = "Ollama is offline", new.error or self.cfg.host, \
                QSystemTrayIcon.MessageIcon.Warning
        elif prev.state == State.OFFLINE:
            title, msg, kind = "Ollama is back online", self.cfg.host, \
                QSystemTrayIcon.MessageIcon.Information
        elif new.state == State.BUSY:
            title = "Model loaded"
            msg = ", ".join(m.name for m in new.models)
            kind = QSystemTrayIcon.MessageIcon.Information
        else:
            title, msg, kind = "Models unloaded", "Ollama is idle", \
                QSystemTrayIcon.MessageIcon.Information
        self.tray.showMessage(title, msg, kind, 4000)

    def open_settings(self) -> None:
        if self.dialog is not None:
            self.dialog.raise_()
            self.dialog.activateWindow()
            return
        self.dialog = SettingsDialog(self.cfg)
        try:
            if self.dialog.exec() != QDialog.DialogCode.Accepted:
                return
            new_host = normalize_host(self.dialog.host.text())
            self.cfg.interval = self.dialog.interval.value()
            self.cfg.notify = self.dialog.notify.isChecked()
            host_changed = new_host != self.cfg.host
            self.cfg.host = new_host
            self.cfg.save()
            try:
                set_autostart(self.dialog.autostart.isChecked(), _exec_command())
            except OSError as e:
                QMessageBox.warning(None, "Autostart", f"Could not update autostart: {e}")
            self.monitor.set_interval(self.cfg.interval)
            if host_changed:
                self.status = Status()
                self.tray.setIcon(icon_for(State.UNKNOWN))
                self.monitor.set_host(self.cfg.host)
            self._rebuild_menu()
        finally:
            self.dialog = None

    def about(self) -> None:
        QMessageBox.about(
            None,
            "Ollama Tray Buddy",
            f"<b>Ollama Tray Buddy</b> {__version__}<br>"
            "Shows the status of an Ollama server in the system tray.<br><br>"
            "<a href='https://github.com/gtradigo/ollama-tray-buddy'>"
            "github.com/gtradigo/ollama-tray-buddy</a>",
        )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog=APP_ID, description=__doc__)
    parser.add_argument("--host", help=f"Ollama host to monitor (default: {DEFAULT_HOST}); "
                                       "saved to the config file")
    parser.add_argument("--interval", type=int, help="polling interval in seconds")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()

    if args.host or args.interval:
        cfg = Config.load()
        if args.host:
            cfg.host = normalize_host(args.host)
        if args.interval:
            cfg.interval = max(1, args.interval)
        cfg.save()

    signal.signal(signal.SIGINT, signal.SIG_DFL)  # allow Ctrl+C from terminal
    app = QApplication(sys.argv)
    app.setApplicationName(APP_ID)
    app.setDesktopFileName(APP_ID)
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None, "Ollama Tray Buddy",
            "No system tray available.\nOn GNOME enable the "
            "'AppIndicator and KStatusNotifierItem Support' extension.",
        )
        return 1

    buddy = TrayBuddy(app)  # noqa: F841 (keep reference alive)
    return app.exec()
