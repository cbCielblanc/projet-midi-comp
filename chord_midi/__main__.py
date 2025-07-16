#!/usr/bin/env python3
"""Point d’entrée pour l’interface graphique Chord-MIDI."""
import sys
from PySide6.QtWidgets import QApplication
from .gui.main_window import ChordMidiWindow


def main() -> None:
    """Lance l’application graphique."""
    app = QApplication(sys.argv)
    w = ChordMidiWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
