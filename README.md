# Chord-MIDI

Ce projet propose une petite application graphique pour générer et éditer des progressions d'accords, puis exporter le résultat au format MIDI. Les modules sont également importables pour utilisation dans vos propres scripts Python.

## Prérequis

- Python ≥ 3.10
- [PySide6](https://pypi.org/project/PySide6/)
- [mido](https://pypi.org/project/mido/)
- [music21](https://pypi.org/project/music21/)

## Installation

Clonez le dépôt puis installez les dépendances :

```bash
pip install -r requirements.txt
```

## Utilisation

### Lancer l'interface graphique

```bash
python main.py
```

### Utiliser les fonctions dans un script

```python
from chord_midi import generate_progression, build_midi

prog = generate_progression("C", mode="major", style="pop", total=4)
mid_path = build_midi(prog, out="progression.mid")
print("MIDI enregistré dans", mid_path)
```

