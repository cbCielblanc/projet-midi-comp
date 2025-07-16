#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import sys
from PySide6.QtWidgets import QApplication
from chord_midi.gui.main_window import ChordMidiWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ChordMidiWindow(); w.show()
    sys.exit(app.exec())
