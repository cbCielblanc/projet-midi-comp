# SPDX-License-Identifier: MIT
from __future__ import annotations

from PySide6.QtCore  import Qt, QPointF
from PySide6.QtGui   import QColor
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QInputDialog

class NoteItem(QGraphicsRectItem):
    """Rectangle déplaçable représentant une note MIDI."""
    def __init__(self, x, y, w, h, pitch, *, vel=100, pan=64):
        super().__init__(x, y, w, h)
        self.setBrush(QColor(0, 122, 204))
        self.setPen(Qt.NoPen)
        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.pitch, self.vel, self.pan = pitch, vel, pan

    # — quantisation grille
    STEP_X   = 20   # sera surchargé depuis PianoRoll
    NOTE_H   = 8

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            step = self.STEP_X
            return QPointF(round(value.x()/step) * step,
                           round(value.y()/self.NOTE_H) * self.NOTE_H)
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, e):
        self.pitch = max(0, min(127, 127 - int(self.y()/self.NOTE_H)))
        super().mouseReleaseEvent(e)

    def contextMenuEvent(self, _):
        v, ok = QInputDialog.getInt(None, "Velocity", "1–127 :", self.vel, 1, 127)
        if ok:
            self.vel = v
        p, ok = QInputDialog.getInt(None, "Pan", "0–127 :", self.pan, 0, 127)
        if ok:
            self.pan = p
