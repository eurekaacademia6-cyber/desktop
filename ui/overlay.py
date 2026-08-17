from __future__ import annotations

from typing import Iterable, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.boxes = []
        self.signal_text = "NO TRADE"
        self.signal_probability = 50.0
        self.confidence = 0.0
        self.status = "WAITING"
        self.layer_summary = []

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def set_data(self, boxes: Iterable[Tuple[int, int, int, int]], label,
                 probability, confidence, status, layer_summary=None):
        self.boxes = list(boxes)
        self.signal_text = label
        self.signal_probability = probability
        self.confidence = confidence
        self.status = status
        self.layer_summary = layer_summary or []
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for i, (x, y, w, h) in enumerate(self.boxes):
            color = QColor(40, 220, 150, 150)
            if i == len(self.boxes) - 1:
                color = QColor(255, 190, 45, 220)
            pen = QPen(color)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)

        panel_w = min(450, max(300, self.width() - 20))
        panel_h = min(230, 120 + 16 * min(6, len(self.layer_summary)))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(5, 18, 28, 140))
        painter.drawRoundedRect(10, 10, panel_w, panel_h, 12, 12)

        painter.setPen(QColor(255, 255, 255, 240))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(24, 33, "QUOTEX VISION AI")

        color = QColor(255, 195, 45, 245)
        if self.signal_text == "UP":
            color = QColor(30, 225, 140, 245)
        elif self.signal_text == "DOWN":
            color = QColor(255, 95, 110, 245)

        painter.setPen(color)
        painter.setFont(QFont("Segoe UI", 21, QFont.Bold))
        painter.drawText(24, 64, self.signal_text)

        painter.setPen(QColor(255, 255, 255, 220))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(135, 60, f"UP {self.signal_probability:.1f}%")
        painter.drawText(135, 80, f"Confidence {self.confidence*100:.0f}%")
        painter.drawText(24, 98, self.status[:54])

        y = 118
        for item in self.layer_summary[:6]:
            painter.drawText(24, y, item[:64])
            y += 16
