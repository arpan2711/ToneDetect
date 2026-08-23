"""ToneDetect main window: live pitch detection displayed on a fretboard."""

import queue
import time
import tkinter as tk
from tkinter import ttk

from .audio_input import AudioInput, list_input_devices
from .chord_detector import ChordDetector
from .fretboard_widget import FretboardWidget
from .lessons import LESSONS
from .notes import NOTE_NAMES, freq_to_note, fretboard_positions
from .pitch_detector import YinPitchDetector
from .practice_engine import PracticeSession
from .scales import SCALE_NAMES, scale_fretboard_positions

NO_SCALE = "— None —"
NO_LESSON = "— None —"

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
FG_GREEN = "#4fc471"
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
        self.practice_session = None
        self._lessons_by_title = {lesson.title: lesson for lesson in LESSONS.values()}

        self._build_device_bar()
        self._build_scale_bar()
        self._build_lesson_panel()

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

    def _build_scale_bar(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill=tk.X, padx=20, pady=(10, 0))

        tk.Label(bar, text="Scale:", fg=FG_DIM, bg=BG, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.scale_root_var = tk.StringVar(value=NO_SCALE)
        root_values = [NO_SCALE] + NOTE_NAMES
        self.scale_root_combo = ttk.Combobox(
            bar, textvariable=self.scale_root_var, values=root_values, state="readonly", width=10,
        )
        self.scale_root_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.scale_root_combo.bind("<<ComboboxSelected>>", self._update_scale_overlay)

        self.scale_type_var = tk.StringVar(value=SCALE_NAMES[0])
        self.scale_type_combo = ttk.Combobox(
            bar, textvariable=self.scale_type_var, values=SCALE_NAMES, state="readonly", width=26,
        )
        self.scale_type_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.scale_type_combo.bind("<<ComboboxSelected>>", self._update_scale_overlay)

    def _update_scale_overlay(self, _event=None):
        root = self.scale_root_var.get()
        if root == NO_SCALE:
            self.fretboard.set_scale_overlay([])
            return
        positions = scale_fretboard_positions(root, self.scale_type_var.get())
        self.fretboard.set_scale_overlay(positions)

    def _build_lesson_panel(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill=tk.X, padx=20, pady=(10, 0))

        tk.Label(bar, text="Lesson:", fg=FG_DIM, bg=BG, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.lesson_var = tk.StringVar(value=NO_LESSON)
        lesson_names = [NO_LESSON] + list(self._lessons_by_title.keys())
        self.lesson_combo = ttk.Combobox(
            bar, textvariable=self.lesson_var, values=lesson_names, state="readonly", width=40,
        )
        self.lesson_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.lesson_combo.bind("<<ComboboxSelected>>", self._on_lesson_selected)

        self.lesson_skip_btn = tk.Button(
            bar, text="Skip step", command=self._skip_lesson_step, state=tk.DISABLED,
            bg=SLIDER_TROUGH, fg=FG_DIM, activebackground=FG, relief=tk.FLAT,
        )
        self.lesson_skip_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.lesson_reset_btn = tk.Button(
            bar, text="Restart", command=self._restart_lesson, state=tk.DISABLED,
            bg=SLIDER_TROUGH, fg=FG_DIM, activebackground=FG, relief=tk.FLAT,
        )
        self.lesson_reset_btn.pack(side=tk.LEFT, padx=(6, 0))

        panel = tk.Frame(self.root, bg=BG)
        panel.pack(fill=tk.X, padx=20, pady=(4, 0))

        self.lesson_step_label = tk.Label(
            panel, text="", fg=FG_GREEN, bg=BG, font=("Segoe UI", 13, "bold"), anchor="w", justify=tk.LEFT,
        )
        self.lesson_step_label.pack(fill=tk.X)

        self.lesson_progress_label = tk.Label(
            panel, text="", fg=FG_DIM, bg=BG, font=("Segoe UI", 9), anchor="w", justify=tk.LEFT,
        )
        self.lesson_progress_label.pack(fill=tk.X)

    def _on_lesson_selected(self, _event=None):
        title = self.lesson_var.get()
        if title == NO_LESSON:
            self.practice_session = None
            self.lesson_skip_btn.config(state=tk.DISABLED)
            self.lesson_reset_btn.config(state=tk.DISABLED)
            self.lesson_step_label.config(text="")
            self.lesson_progress_label.config(text="")
            self.fretboard.set_target_overlay([])
            return

        lesson = self._lessons_by_title[title]
        self.practice_session = PracticeSession(lesson)
        self.lesson_skip_btn.config(state=tk.NORMAL)
        self.lesson_reset_btn.config(state=tk.NORMAL)
        self._refresh_lesson_ui()

    def _restart_lesson(self):
        if self.practice_session is not None:
            self.practice_session.reset()
            self._refresh_lesson_ui()

    def _skip_lesson_step(self):
        if self.practice_session is not None:
            self.practice_session.skip()
            self._refresh_lesson_ui()

    def _refresh_lesson_ui(self):
        session = self.practice_session
        if session is None:
            return

        idx, total = session.progress
        if session.finished:
            self.lesson_step_label.config(text=f"Lesson complete — {session.correct_count}/{total} correct.")
            self.lesson_progress_label.config(text="")
            self.fretboard.set_target_overlay([])
            return

        step = session.current_step
        self.lesson_step_label.config(text=step.label)
        progress_text = f"Step {idx + 1} of {total}"
        if step.instructions:
            progress_text += f"   —   {step.instructions}"
        self.lesson_progress_label.config(text=progress_text)
        self.fretboard.set_target_overlay(step.target_positions)

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
        detected_notes = []

        if buf is not None:
            rms = float((buf ** 2).mean() ** 0.5)
            if rms >= self.silence_rms:
                chord_freqs = self.chord_detector.detect(buf)
                chord_notes = self._dedupe_notes(chord_freqs)

                if len(chord_notes) >= 2:
                    detected_notes = chord_notes
                else:
                    freq = self.detector.detect(buf)
                    if freq:
                        note = freq_to_note(freq)
                        if note:
                            detected_notes = [note]

        if detected_notes:
            self._last_active_time = now
            if len(detected_notes) >= 2:
                self._show_chord(detected_notes)
            else:
                self._show_single_note(detected_notes[0])
        else:
            self._maybe_clear(now)

        if self.practice_session is not None:
            detected_midis = {n["midi"] for n in detected_notes}
            if self.practice_session.check(detected_midis, now):
                self._refresh_lesson_ui()

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

    def _show_single_note(self, note):
        self.note_label.config(text=note["name"])
        self.freq_label.config(text=f"{note['freq']:.1f} Hz   {note['cents']:+.0f} cents")
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
