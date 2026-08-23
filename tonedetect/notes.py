"""Frequency <-> note-name conversion and standard-tuning fretboard lookup."""

import math
import re

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

A4_MIDI = 69
A4_FREQ = 440.0

# Standard tuning, string 6 (low E) to string 1 (high E), as MIDI note numbers.
STANDARD_TUNING = {
    6: 40,  # E2
    5: 45,  # A2
    4: 50,  # D3
    3: 55,  # G3
    2: 59,  # B3
    1: 64,  # E4
}

NUM_FRETS = 15


def freq_to_midi(freq):
    if freq is None or freq <= 0:
        return None
    return A4_MIDI + 12 * math.log2(freq / A4_FREQ)


def midi_to_note_name(midi_round):
    name = NOTE_NAMES[midi_round % 12]
    octave = midi_round // 12 - 1
    return f"{name}{octave}"


def freq_to_note(freq):
    """Return dict with midi, name, pitch class, octave, cents offset, and freq."""
    midi = freq_to_midi(freq)
    if midi is None:
        return None
    midi_round = round(midi)
    cents = (midi - midi_round) * 100
    return {
        "midi": midi_round,
        "name": midi_to_note_name(midi_round),
        "note": NOTE_NAMES[midi_round % 12],
        "octave": midi_round // 12 - 1,
        "cents": cents,
        "freq": freq,
    }


_NOTE_NAME_RE = re.compile(r"^([A-G]#?)(-?\d+)$")


def note_name_to_midi(name):
    """Parse a note name like 'A2' or 'C#4' into its MIDI number."""
    match = _NOTE_NAME_RE.match(name)
    if not match:
        raise ValueError(f"Bad note name: {name!r}")
    note, octave = match.group(1), int(match.group(2))
    return (octave + 1) * 12 + NOTE_NAMES.index(note)


def fretboard_positions(midi_note, num_frets=NUM_FRETS):
    """All (string_number, fret) positions producing this exact MIDI note
    on a standard-tuned guitar, within the first `num_frets` frets."""
    positions = []
    for string_num, open_midi in STANDARD_TUNING.items():
        fret = midi_note - open_midi
        if 0 <= fret <= num_frets:
            positions.append((string_num, fret))
    return positions
