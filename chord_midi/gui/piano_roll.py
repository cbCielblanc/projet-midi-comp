# SPDX-License-Identifier: MIT
from __future__ import annotations
from typing import List, Tuple

from PySide6.QtCore    import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui     import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QScrollBar, QSizePolicy
)

from .note_item import NoteItem

_DEG_WHITE = {0, 2, 4, 5, 7, 9, 11}   # touches blanches

class PianoRoll(QGraphicsView):
    BAR_W, NOTE_H = 80, 8
    STEP_X        = BAR_W // 4
    Z_MIN, Z_MAX  = .4, 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setBackgroundBrush(QColor(30, 30, 30))
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # fait connaître STEP_X / NOTE_H aux NoteItem
        NoteItem.STEP_X = self.STEP_X
        NoteItem.NOTE_H = self.NOTE_H

        self.labels: List[Tuple[int, str, str]] = []

    # — zoom molette
    def wheelEvent(self, e):
        f   = 1.003 ** e.angleDelta().y()
        cur = self.transform().m11()
        new = max(self.Z_MIN, min(self.Z_MAX, cur * f))
        self.scale(new/cur, new/cur)

    # — Ctrl+0 : reset zoom
    def keyPressEvent(self, e):
        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_0:
            self.resetTransform()
            self.centerOn(0, 0)
        else:
            super().keyPressEvent(e)

    # — clic milieu ou clic droit (hors note) : pan
    def mousePressEvent(self, e):
        if (e.button() == Qt.MiddleButton or
            (e.button() == Qt.RightButton and not self.itemAt(e.position().toPoint()))):
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.viewport().setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if (self.dragMode() == QGraphicsView.ScrollHandDrag and
            e.button() in (Qt.MiddleButton, Qt.RightButton)):
            self.setDragMode(QGraphicsView.NoDrag)
            self.viewport().setCursor(Qt.ArrowCursor)

    # — grille & noms
    def drawBackground(self, p: QPainter, r: QRectF):
        l = int(r.left())  - int(r.left())  % self.BAR_W
        t = int(r.top())   - int(r.top())   % self.NOTE_H
        right, bottom = int(r.right()), int(r.bottom())

        for y in range(t, bottom, self.NOTE_H):
            midi = 127 - y // self.NOTE_H
            deg  = midi % 12
            p.fillRect(l, y, right-l, self.NOTE_H,
                       QColor(45, 45, 45) if deg in _DEG_WHITE else QColor(35, 35, 35))
            if deg == 0:
                p.setPen(QPen(QColor(240, 240, 240), 1))
                p.drawLine(l, y+self.NOTE_H-1, right, y+self.NOTE_H-1)

        beat, sub = QPen(QColor(80, 80, 80)), QPen(QColor(55, 55, 55))
        for x in range(l, right, self.STEP_X):
            p.setPen(beat if x % self.BAR_W == 0 else sub)
            p.drawLine(x, t, x, bottom)

        p.setPen(QColor(200, 200, 200))
        p.setFont(QFont("Sans", 7))
        for y in range(t, bottom, self.NOTE_H):
            midi = 127 - y // self.NOTE_H
            deg  = midi % 12
            name = ['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'][deg]
            octv = midi // 12 - 1
            lbl  = f"{name}{octv if name == 'C' else ''}"
            p.drawText(l-34, y+6, lbl)
            p.drawText(right+4, y+6, lbl)

    # — libellés accords
    def drawForeground(self, p: QPainter, rect: QRectF):
        p.setPen(QColor(235, 235, 235))
        p.setFont(QFont("Sans", 8))
        y = rect.top() + 4
        for x, rn, sym in self.labels:
            if rect.left() - self.STEP_X < x < rect.right():
                p.drawText(x+4, y+8, rn)
                p.drawText(x+4, y+18, sym)

    # — chargement progression
    def load(self, prog):
        sc = self.scene()
        sc.clear()
        self.labels.clear()

        for i, rn in enumerate(prog):
            x0 = i * self.BAR_W
            for nt in rn.pitches:
                y = (127 - nt.midi) * self.NOTE_H
                sc.addItem(NoteItem(x0, y, self.BAR_W, self.NOTE_H, nt.midi))
            suf = {'major':'','minor':'m','diminished':'dim','augmented':'aug'}.get(rn.quality, '')
            self.labels.append((x0, rn.figure, f"{rn.root().name}{suf}"))

        bounds = sc.itemsBoundingRect()
        padL, padT, padR, padB = 0, -60, 40, 40
        rect = QRectF(padL,
                      bounds.top()  + padT,
                      bounds.width() + padR,
                      bounds.height() - padT + padB)
        self.setSceneRect(rect)

        QTimer.singleShot(0, self._reset_scroll)

    def _reset_scroll(self):
        for bar in (self.horizontalScrollBar(), self.verticalScrollBar()):
            bar.setValue(bar.minimum())

    # — conversion en événements MIDI
    def to_events(self, ticks, ch=0):
        ev = []
        for it in self.scene().items():
            if not isinstance(it, NoteItem):
                continue
            # start = int(it.x() * 480 / self.BAR_W)
            # 1 accord (BAR_W px)  →  `ticks`  (beats/chord * 480)
            start = int(it.x() * ticks / self.BAR_W)
            ev += [(start,       'control_change', 10,  it.pan, ch),
                   (start,       'note_on',        it.pitch, it.vel, ch),
                   (start+ticks, 'note_off',       it.pitch, 0, ch)]
        return sorted(ev, key=lambda t: t[0])
