# ToneDetect

A real-time guitar practice tool for Windows. Plug in your guitar, and ToneDetect
listens through your audio interface, detects the note you're playing, and shows
it — both as a note name and as a highlighted position on a fretboard diagram.

Built around gear that doesn't map cleanly onto existing practice apps (starting
with gypsy jazz repertoire), with an eye towards growing into a full practice
sandbox: comparing what you play against a reference lesson, scoring timing and
pitch accuracy, and authoring scales, arpeggios, and tabs as simple data.

## Stage 1 (current)

- Live monophonic pitch detection (YIN algorithm) from any Windows audio input device,
  covering the full fretted range (up to ~2000 Hz, well past the 22nd fret on the high E)
- Note name + cents-off-pitch display
- Basic chord detection: spectral peak-picking with harmonic suppression identifies
  a handful of simultaneous notes. This is an approximation, not full polyphonic
  transcription — it works reasonably on clean, simple voicings (open chords, power
  chords, double-stops) but gets shakier on dense or heavily muted chords, since
  overlapping harmonics between notes can mask or fake a peak
- Fretboard diagram highlighting every position on a standard-tuned guitar where
  the detected note(s) occur
- Scale overlay: pick a root and scale (major/minor modes, harmonic minor, melodic
  minor, phrygian dominant, Hungarian/gypsy minor, pentatonics, blues) and its notes
  light up translucently across the fretboard, underneath your solid, opaque
  played-note markers — so you can see both what you're playing and where it sits
  in the scale at the same time
- Live-tunable detection: sliders for silence threshold, note hold time, pitch
  clarity, and chord sensitivity, plus an input device picker so you can select a
  USB audio interface (e.g. a NUX MG-300 II) instead of your system mic

## Planned

- More robust polyphonic detection
- Lesson content defined as data (scales, arpeggios, tabs) in one shared format
- A comparison/scoring layer: play along against an expected note sequence and
  get feedback on wrong notes and timing drift

## Requirements

- Windows 10+
- Python 3.10+
- A guitar audio interface (e.g. a multi-FX pedal with USB audio, like the NUX
  MG-300 II) — or just your system's default input device to try it out

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On launch, pick your audio interface from the **Input device** dropdown at the
top of the window, then play a note.

## How it works

- `tonedetect/audio_input.py` — captures audio from the selected input device via `sounddevice`
- `tonedetect/pitch_detector.py` — estimates the fundamental frequency of each buffer using YIN (single-note path)
- `tonedetect/chord_detector.py` — spectral peak-picking with harmonic suppression for multi-note detection
- `tonedetect/notes.py` — converts frequency to note name/octave and maps notes to fretboard positions (standard tuning)
- `tonedetect/fretboard_widget.py` — Tkinter canvas that draws the fretboard and highlights detected notes
- `tonedetect/app.py` — wires it all together into the main window
