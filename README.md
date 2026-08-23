# ToneDetect

A real-time guitar practice tool for Windows. Plug in your guitar, and ToneDetect
listens through your audio interface, detects the note you're playing, and shows
it — both as a note name and as a highlighted position on a fretboard diagram.

Built around gear that doesn't map cleanly onto existing practice apps (starting
with gypsy jazz repertoire), with an eye towards growing into a full practice
sandbox: comparing what you play against a reference lesson, scoring timing and
pitch accuracy, and authoring scales, arpeggios, and tabs as simple data.

## Stage 1 (current)

- Live monophonic pitch detection (YIN algorithm) from any Windows audio input device
- Note name + cents-off-pitch display
- Fretboard diagram highlighting every position on a standard-tuned guitar where
  the detected note occurs
- Input device picker, so you can select a USB audio interface (e.g. a NUX MG-300 II)
  instead of your system mic

## Planned

- Polyphonic / chord detection
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
- `tonedetect/pitch_detector.py` — estimates the fundamental frequency of each buffer using YIN
- `tonedetect/notes.py` — converts frequency to note name/octave and maps notes to fretboard positions (standard tuning)
- `tonedetect/fretboard_widget.py` — Tkinter canvas that draws the fretboard and highlights detected notes
- `tonedetect/app.py` — wires it all together into the main window
