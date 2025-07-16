# SPDX-License-Identifier: MIT
from __future__ import annotations
from pathlib import Path

import mido
from PySide6.QtCore    import Qt, QSize
from PySide6.QtGui     import QColor, QPalette, QAction
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QFormLayout, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QComboBox, QSpinBox, QPushButton, QFileDialog,
    QToolBar, QStatusBar
)

from chord_midi.midi.progression import generate_progression, STYLE_MAP
from .piano_roll import PianoRoll

TONICS = ["C","C#","D","Eb","E","F","F#","G","Ab","A","Bb","B"]

class ChordMidiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._palette()
        self._ui()
        self.resize(920, 540)
        self.setWindowTitle("Chord → MIDI Generator")

    # — thème sombre Fusion
    def _palette(self):
        from PySide6.QtWidgets import QApplication
        QApplication.setStyle("Fusion")
        pal = QPalette()
        for role, col in [(QPalette.Window,       (35, 35, 37)),
                          (QPalette.WindowText,   (255, 255, 255)),
                          (QPalette.Base,         (25, 25, 25)),
                          (QPalette.Text,         (255, 255, 255)),
                          (QPalette.Button,       (45, 45, 47)),
                          (QPalette.ButtonText,   (255, 255, 255)),
                          (QPalette.Highlight,    (0, 122, 204))]:
            pal.setColor(role, QColor(*col))
        QApplication.setPalette(pal)

    # — helpers widgets
    def _cb(self, items): return self._build(QComboBox(), lambda w: w.addItems(items))
    def _sp(self, val, mi, ma): return self._build(QSpinBox(),
                                                   lambda w: (w.setRange(mi, ma), w.setValue(val)))
    def _build(self, widget, init):
        init(widget); return widget

    # — UI
    def _ui(self):
        card, form = QGroupBox("Settings"), QFormLayout()
        self.tonic = self._cb(TONICS)
        self.mode  = self._cb(["major", "minor"])
        self.style = self._cb(list(STYLE_MAP))
        self.count = self._sp(4, 1, 64)
        self.beats = self._sp(4, 1, 16)
        self.tempo = self._sp(120, 20, 300)
        self.oct   = self._sp(4, 1, 8)
        for l, w in [("Tonic", self.tonic), ("Mode", self.mode), ("Style", self.style),
                     ("Total chords", self.count), ("Beats / chord", self.beats),
                     ("Tempo", self.tempo), ("Octave floor", self.oct)]:
            form.addRow(l, w)
        card.setLayout(form)

        self.out_lbl = QLabel(str(Path.cwd() / "progression.mid"))
        self.out_lbl.setStyleSheet("background:#1e1e1e;padding:4px;")
        b = QPushButton("Browse…"); b.clicked.connect(self._browse)
        row = QHBoxLayout(); row.addWidget(self.out_lbl, 1); row.addWidget(b)

        self.roll = PianoRoll()

        v = QVBoxLayout()
        v.addWidget(card); v.addLayout(row); v.addWidget(self.roll)
        cen = QWidget(); cen.setLayout(v); self.setCentralWidget(cen)

        tb = QToolBar(); tb.setIconSize(QSize(22, 22))
        gen = QAction("Generate", self); gen.triggered.connect(self._gen); tb.addAction(gen)
        self.setStatusBar(QStatusBar()); self.addToolBar(tb)

    # — browse
    def _browse(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save MIDI",
                                            self.out_lbl.text(), "MIDI files (*.mid)")
        if fn: self.out_lbl.setText(fn)

    # — generate + export
    def _gen(self):
        try:
            prog = generate_progression(self.tonic.currentText(),
                                        self.mode.currentText(),
                                        self.style.currentText(),
                                        self.count.value())
            self.roll.load(prog)
            path = self._export()
            self.statusBar().showMessage(f"Saved → {path}", 5000)
        except Exception as e:
            self.statusBar().showMessage(str(e), 7000)

    def _export(self):
        ticks = self.beats.value() * 480
        ev    = self.roll.to_events(ticks)
        mid, tr = mido.MidiFile(ticks_per_beat=480), mido.MidiTrack(); mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo",
                                   tempo=mido.bpm2tempo(self.tempo.value()), time=0))
        clock = 0
        for t, typ, d1, d2, ch in ev:
            dt, t = t - clock, t
            if typ == "control_change":
                tr.append(mido.Message('control_change', control=d1, value=d2,
                                       channel=ch, time=dt))
            else:
                tr.append(mido.Message(typ, note=d1, velocity=d2,
                                       channel=ch, time=dt))
            clock = t
        path = Path(self.out_lbl.text()).resolve(); mid.save(path); return path
