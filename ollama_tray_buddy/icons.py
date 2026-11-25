"""Tray icons: a llama head inspired by the Ollama logo, with a status badge."""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from .status import State

OUTLINE = "#1b1b1b"

# Per-state look: (head fill, badge fill, badge glyph)
STYLES: dict[State, tuple[str, str, str]] = {
    State.IDLE: ("#ffffff", "#2ecc71", "check"),
    State.BUSY: ("#ffffff", "#3d8bfd", "bolt"),
    State.OFFLINE: ("#a7a7a7", "#e74c3c", "cross"),
    State.UNKNOWN: ("#d0d0d0", "#f1c40f", "dots"),
}

_GLYPHS = {
    "check": '<path d="M44.5 50.5 L48.5 54.5 L55.5 46" fill="none" stroke="#fff" '
             'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>',
    "cross": '<path d="M46 46 L54 54 M54 46 L46 54" fill="none" stroke="#fff" '
             'stroke-width="3.2" stroke-linecap="round"/>',
    "bolt": '<path d="M51.5 43.5 L45.5 51 L50 51 L48.5 56.5 L54.5 49 L50 49 Z" '
            'fill="#fff" stroke="#fff" stroke-width="1" stroke-linejoin="round"/>',
    "dots": '<g fill="#fff"><circle cx="45.5" cy="50" r="1.8"/><circle cx="50" cy="50" r="1.8"/>'
            '<circle cx="54.5" cy="50" r="1.8"/></g>',
}


def svg_for(state: State) -> str:
    head, badge, glyph = STYLES[state]
    if state == State.OFFLINE:
        # sleepy, closed eyes
        eyes = ('<path d="M21.5 31 Q24.5 33.5 27.5 31 M36.5 31 Q39.5 33.5 42.5 31" '
                f'fill="none" stroke="{OUTLINE}" stroke-width="2.2" stroke-linecap="round"/>')
    else:
        eyes = (f'<g fill="{OUTLINE}"><ellipse cx="24.5" cy="31" rx="2.4" ry="3"/>'
                '<ellipse cx="39.5" cy="31" rx="2.4" ry="3"/></g>'
                '<g fill="#fff"><circle cx="25.3" cy="29.9" r="0.8"/>'
                '<circle cx="40.3" cy="29.9" r="0.8"/></g>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <g fill="{head}" stroke="{OUTLINE}" stroke-width="2.6" stroke-linejoin="round">
    <path d="M18.5 24 C15.5 16 15.5 7 19.5 4.5 C23.5 2.5 26 10 26 20 Z"/>
    <path d="M45.5 24 C48.5 16 48.5 7 44.5 4.5 C40.5 2.5 38 10 38 20 Z"/>
    <path d="M32 14 C21 14 13.5 21 13.5 32 C13.5 43 18 51 22 58.5 L42 58.5
             C46 51 50.5 43 50.5 32 C50.5 21 43 14 32 14 Z"/>
    <ellipse cx="32" cy="41" rx="9" ry="7" fill="#fff"/>
  </g>
  {eyes}
  <path d="M29.5 39 Q32 41.5 34.5 39" fill="none" stroke="{OUTLINE}"
        stroke-width="2" stroke-linecap="round"/>
  <path d="M32 41 L32 43.5 M29.5 45 Q32 46.5 34.5 45" fill="none" stroke="{OUTLINE}"
        stroke-width="1.6" stroke-linecap="round"/>
  <circle cx="50" cy="50" r="11.5" fill="{badge}" stroke="#fff" stroke-width="2.5"/>
  {_GLYPHS[glyph]}
</svg>"""


def render(state: State, size: int = 64) -> QImage:
    renderer = QSvgRenderer(QByteArray(svg_for(state).encode()))
    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p, QRectF(0, 0, size, size))
    p.end()
    return img


_cache: dict[State, QIcon] = {}


def icon_for(state: State) -> QIcon:
    if state not in _cache:
        icon = QIcon()
        for s in (16, 22, 24, 32, 48, 64, 128):
            icon.addPixmap(QPixmap.fromImage(render(state, s)))
        _cache[state] = icon
    return _cache[state]
