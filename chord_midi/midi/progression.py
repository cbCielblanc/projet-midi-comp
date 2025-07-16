#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Logique “théorie musicale” + export MIDI.

Dépendances : music21 ≥ 6, mido ≥ 1.3
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Union
import json

import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
from music21 import key as m21key, roman, pitch

# ——————————— styles d’accords (haute-niveau) ———————————
FALLBACK_STYLE_MAP = {
    "pop":     {"maj": ["I","V","vi","IV"],      "min": ["i","VI","III","VII"]},
    "classic": {"maj": ["I","IV","V","I"],       "min": ["i","iv","V","i"]},
    "jazz":    {"maj": ["ii","V7","I"],          "min": ["iiø","V7","i"]},
    "soul":    {"maj": ["I","iii","IV","ii","V","I"],
                "min": ["i","bIII","IV","V"]},
    "blues":   {"maj": ["I","IV","I","I","IV","IV","I","I","V","IV","I","V"],
                "min": ["i","iv","i","i","iv","iv","i","i","V","iv","i","V"]}
}

DEFAULT_STYLES_FILE = Path(__file__).with_name("styles.json")

def load_style_map(path: Union[str, Path] = DEFAULT_STYLES_FILE) -> Dict[str, Dict[str, List[str]]]:
    """Charge un fichier JSON contenant les styles de progressions."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

try:  # charge le JSON par défaut, avec repli en dur
    STYLE_MAP = load_style_map()
except Exception:
    STYLE_MAP = FALLBACK_STYLE_MAP

# ————————————————— helpers internes —————————————————
def _repeat_to_len(seq: List[str], n: int) -> List[str]:
    q, r = divmod(n, len(seq))
    return seq * q + seq[:r]

def _chord_midi_closed(rn: roman.RomanNumeral, floor: int) -> List[int]:
    """Renvoie les MIDIs d’un accord (position fermée ≥ floor)."""
    root = pitch.Pitch(rn.root().name); root.octave = floor
    base = root.midi
    out = []
    for p in rn.pitches:
        n = pitch.Pitch(p.name)
        while n.midi < base:
            n.midi += 12
        out.append(n.midi)
    return sorted(out)

def _vl_distance(a: roman.RomanNumeral, b: roman.RomanNumeral, floor=4) -> int:
    pa, pb = _chord_midi_closed(a, floor), _chord_midi_closed(b, floor)
    ln = min(len(pa), len(pb))
    return sum(abs(pa[i] - pb[i]) for i in range(ln))

def _best_inversion(prev: roman.RomanNumeral,
                    curr: roman.RomanNumeral) -> roman.RomanNumeral:
    best, best_d = curr, float('inf')
    for inv in range(len(curr.pitches)):
        test = roman.RomanNumeral(curr.figure, curr.key)  # clone
        test.inversion(inv)
        d = _vl_distance(prev, test)
        if d < best_d:
            best, best_d = test, d
    return best

# ——————————————— API publique ———————————————
def generate_progression(tonic: str, mode="major",
                         style="pop", total=4, *, smart_voicing=True,
                         style_map: Union[Dict[str, Dict[str, List[str]]], str, Path, None] = None):
    """Liste de RomanNumeral music21 avec inversions optimisées."""
    mode, tonic = mode.lower().strip(), tonic.strip()
    smap = STYLE_MAP if style_map is None else style_map
    if isinstance(smap, (str, Path)):
        smap = load_style_map(smap)
    romans = smap[style]["maj" if mode == "major" else "min"]
    romans = _repeat_to_len(romans, total)
    k = m21key.Key(tonic, mode)
    prog = [roman.RomanNumeral(rn, k) for rn in romans]
    if smart_voicing:
        for i in range(1, len(prog)):
            prog[i] = _best_inversion(prog[i-1], prog[i])
    return prog

def build_midi(rprog: List[roman.RomanNumeral], out="progression.mid",
               bpm=120, beats=4, floor=4, channel=0, vel=100):
    """Construit un fichier MIDI à partir d’une progression."""
    mid, tr = MidiFile(ticks_per_beat=480, type=1), MidiTrack()
    mid.tracks.append(tr)
    tr.append(MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    tr.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tr.append(Message("program_change", program=0, channel=channel, time=0))
    tick_bar = beats * 480
    events = []
    clock = 0
    for rn in rprog:
        notes = _chord_midi_closed(rn, floor)
        for n in notes:
            events.append((clock, 'note_on',  n, vel))
            events.append((clock + tick_bar, 'note_off', n, 0))
        clock += tick_bar

    events.sort(key=lambda e: (e[0], 0 if e[1] == 'note_off' else 1))
    prev = 0
    for t, typ, note, velocity in events:
        tr.append(Message(typ, note=note, velocity=velocity,
                          channel=channel, time=t - prev))
        prev = t
    path = Path(out).resolve()
    mid.save(path)
    return path
