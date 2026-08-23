"""Scale definitions and their fretboard positions in standard tuning."""

from .notes import NOTE_NAMES, NUM_FRETS, STANDARD_TUNING

# Semitone intervals from the root. Includes the diatonic modes, common
# pentatonic/blues scales, and a few scales that come up constantly in
# gypsy jazz (harmonic minor, phrygian dominant, and the Hungarian/gypsy
# minor) that mainstream practice apps tend to skip.
SCALE_PATTERNS = {
    "Major (Ionian)": [0, 2, 4, 5, 7, 9, 11],
    "Dorian": [0, 2, 3, 5, 7, 9, 10],
    "Phrygian": [0, 1, 3, 5, 7, 8, 10],
    "Lydian": [0, 2, 4, 6, 7, 9, 11],
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "Natural Minor (Aeolian)": [0, 2, 3, 5, 7, 8, 10],
    "Locrian": [0, 1, 3, 5, 6, 8, 10],
    "Harmonic Minor": [0, 2, 3, 5, 7, 8, 11],
    "Melodic Minor": [0, 2, 3, 5, 7, 9, 11],
    "Phrygian Dominant": [0, 1, 4, 5, 7, 8, 10],
    "Hungarian / Gypsy Minor": [0, 2, 3, 6, 7, 8, 11],
    "Major Pentatonic": [0, 2, 4, 7, 9],
    "Minor Pentatonic": [0, 3, 5, 7, 10],
    "Blues": [0, 3, 5, 6, 7, 10],
    "Chromatic": list(range(12)),
}

SCALE_NAMES = list(SCALE_PATTERNS.keys())


def scale_pitch_classes(root_note, scale_name):
    root_index = NOTE_NAMES.index(root_note)
    intervals = SCALE_PATTERNS[scale_name]
    return {(root_index + i) % 12 for i in intervals}


def scale_fretboard_positions(root_note, scale_name, num_frets=NUM_FRETS):
    """Return (string, fret, is_root) for every fretboard position, across
    all six strings, whose note belongs to the given scale."""
    root_pitch_class = NOTE_NAMES.index(root_note)
    pitch_classes = scale_pitch_classes(root_note, scale_name)

    positions = []
    for string_num, open_midi in STANDARD_TUNING.items():
        for fret in range(0, num_frets + 1):
            pitch_class = (open_midi + fret) % 12
            if pitch_class in pitch_classes:
                positions.append((string_num, fret, pitch_class == root_pitch_class))
    return positions
