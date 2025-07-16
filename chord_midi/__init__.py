"""
Chord-MIDI – génération et édition de progressions d’accords en temps réel.

Exporte :
    generate_progression, build_midi  (depuis chord_midi.midi.progression)
    ChordMidiWindow                  (depuis chord_midi.gui.main_window)
"""
from importlib import import_module

# réexportations “flat” pour la praticité
_progression = import_module("chord_midi.midi.progression")
generate_progression = _progression.generate_progression
build_midi           = _progression.build_midi
STYLE_MAP            = _progression.STYLE_MAP

_main_window = import_module("chord_midi.gui.main_window")
ChordMidiWindow = _main_window.ChordMidiWindow

__all__ = [
    "generate_progression",
    "build_midi",
    "STYLE_MAP",
    "ChordMidiWindow",
]
