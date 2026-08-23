"""ToneDetect main window: live pitch detection displayed on a fretboard."""

import queue
import time
import tkinter as tk
from tkinter import ttk

from .audio_input import AudioInput, list_input_devices
from .chord_detector import ChordDetector
from .fretboard_widget import FretboardWidget
from .notes import freq_to_note, fretboard_positions
from .pitch_detector import YinPitchDetector

SAMPLE_RATE = 44100
BLOCK_SIZE = 4096
POLL_MS = 80

DEFAULT_SILENCE_RMS = 0.01
DEFAULT_HOLD_MS = 300
DEFAULT_YIN_THRESHOLD = 0.10
DEFAULT_CHORD_PEAK_RATIO = 0.15

BG = "#1e1e1e"
FG = "#e0542a"
FG_DIM = "#aaaaaa"
SLIDER_TROUGH = "#3a3a3a"


class ToneDetectApp:
    def __init__(self, root):
        self.root = root
        root.title("ToneDetect")
        root.geometry("900x460")
        root.configure(bg=BG)

        self.silence_rms = DEFAULT_SILENCE_RMS
        self.hold_ms = DEFAULT_HOLD_MS
        self._last_active_time = None

        self._build_device_bar()

        self.note_label = tk.Label(root, text="—", font=("Segoe UI", 48, "bold"), fg=FG, bg=BG)
        self.note_label.pack(pady=(10, 0))

        self.freq_label = tk.Label(root, text=" ", font=("Segoe UI", 12), fg=FG_DIM, bg=BG)
        self.freq_label.pack()

        self.fretboard = FretboardWidget(root, height=220)
        self.fretboard.pack(fill=tk.X, padx=20, pady=(10, 0))

        self.detector = YinPitchDetector(SAMPLE_RATE, threshold=DEFAULT_YIN_THRESHOLD)
        self.chord_detector = ChordDetector(SAMPLE_RATE, peak_ratio_threshold=DEFAULT_CHORD_PEAK_RATIO)
        self.audio = AudioInput(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE)
        self.audio.start()

        self._build_controls()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(POLL_MS, self.poll_audio)

    def _build_device_bar(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill=tk.X, padx=20, pady=(15, 0))

        tk.Label(bar, text="Input device:", fg=FG_DIM, bg=BG, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.devices = list_input_devices()
        names = [name for _, name in self.devices]
        self.device_var = tk.StringVar(value=names[0] if names else "")

        self.device_combo = ttk.Combobox(bar, textvariable=self.device_var, values=names, state="readonly", width=50)
        self.device_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_selected)

    def _build_controls(self):
        panel = tk.Frame(self.root, bg=BG)
        panel.pack(fill=tk.X, padx=20, pady=(4, 10))
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

        self._add_slider(
            panel, row=0, column=0,
            label="Silence threshold",
            from_=0.0, to=0.05, resolution=0.001, default=self.silence_rms,
            on_change=self._set_silence_rms,
        )
        self._add_slider(
            panel, row=0, column=1,
            label="Note hold (ms)",
            from_=0, to=1500, resolution=10, default=self.hold_ms,
            on_change=self._set_hold_ms,
        )
        self._add_slider(
            panel, row=1, column=0,
            label="Pitch clarity threshold",
            from_=0.05, to=0.30, resolution=0.01, default=self.detector.threshold,
            on_change=self._set_yin_threshold,
        )
        self._add_slider(
            panel, row=1, column=1,
            label="Chord sensitivity",
            from_=0.05, to=0.50, resolution=0.01, default=self.chord_detector.peak_ratio_threshold,
            on_change=self._set_chord_sensitivity,
        )

    def _add_slider(self, parent, row, column, label, from_, to, resolution, default, on_change):
        frame = tk.Frame(parent, bg=BG)
        frame.grid(row=row, column=column, sticky="ew", padx=8, pady=4)

        tk.Label(frame, text=label, fg=FG_DIM, bg=BG, font=("Segoe UI", 9)).pack(anchor="w")
        scale = tk.Scale(
            frame, from_=from_, to=to, resolution=resolution, orient=tk.HORIZONTAL,
            bg=BG, fg=FG_DIM, troughcolor=SLIDER_TROUGH, highlightthickness=0,
            bd=0, showvalue=True, sliderrelief=tk.FLAT, activebackground=FG,
            command=lambda v: on_change(float(v)),
        )
        scale.set(default)
        scale.pack(fill=tk.X)

    def _set_silence_rms(self, value):
        self.silence_rms = value

    def _set_hold_ms(self, value):
        self.hold_ms = value

    def _set_yin_threshold(self, value):
        self.detector.threshold = value

    def _set_chord_sensitivity(self, value):
        self.chord_detector.peak_ratio_threshold = value

    def on_device_selected(self, _event=None):
        selected_name = self.device_var.get()
        for index, name in self.devices:
            if name == selected_name:
                self.audio.set_device(index)
                break

    def poll_audio(self):
        buf = None
        try:
            while True:
                buf = self.audio.q.get_nowait()
        except queue.Empty:
            pass

        now = time.monotonic()

        if buf is not None:
            rms = float((buf ** 2).mean() ** 0.5)
            if rms >= self.silence_rms:
                chord_freqs = self.chord_detector.detect(buf)
                chord_notes = self._dedupe_notes(chord_freqs)

                if len(chord_notes) >= 2:
                    self._show_chord(chord_notes)
                    self._last_active_time = now
                else:
                    freq = self.detector.detect(buf)
                    if freq:
                        self._show_single_note(freq)
                        self._last_active_time = now
                    else:
                        self._maybe_clear(now)
            else:
                self._maybe_clear(now)

        self.root.after(POLL_MS, self.poll_audio)

    def _maybe_clear(self, now):
        """Keep showing the last detected note for `hold_ms` after the signal
        drops out, so quickly-decaying (especially high) notes don't flicker
        off the instant amplitude dips below the silence threshold."""
        if self._last_active_time is None or (now - self._last_active_time) * 1000 >= self.hold_ms:
            self._clear_display()

    @staticmethod
    def _dedupe_notes(freqs):
        """Convert frequencies to notes, collapsing any that land on the same
        MIDI note (e.g. two detected peaks an octave apart)."""
        seen = set()
        notes = []
        for f in freqs:
            note = freq_to_note(f)
            if note and note["midi"] not in seen:
                seen.add(note["midi"])
                notes.append(note)
        notes.sort(key=lambda n: n["midi"])
        return notes

    def _show_single_note(self, freq):
        note = freq_to_note(freq)
        self.note_label.config(text=note["name"])
        self.freq_label.config(text=f"{freq:.1f} Hz   {note['cents']:+.0f} cents")
        self.fretboard.set_highlight(fretboard_positions(note["midi"]))

    def _show_chord(self, notes):
        self.note_label.config(text=" · ".join(n["name"] for n in notes))
        self.freq_label.config(text=f"{len(notes)} notes detected")
        positions = []
        for n in notes:
            positions.extend(fretboard_positions(n["midi"]))
        self.fretboard.set_highlight(positions)

    def _clear_display(self):
        self.note_label.config(text="—")
        self.freq_label.config(text=" ")
        self.fretboard.set_highlight([])
        self._last_active_time = None

    def on_close(self):
        self.audio.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    ToneDetectApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
