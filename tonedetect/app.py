"""ToneDetect main window: live pitch detection displayed on a fretboard."""

import queue
import tkinter as tk
from tkinter import ttk

from .audio_input import AudioInput, list_input_devices
from .fretboard_widget import FretboardWidget
from .notes import freq_to_note, fretboard_positions
from .pitch_detector import YinPitchDetector

SAMPLE_RATE = 44100
BLOCK_SIZE = 4096
POLL_MS = 80
SILENCE_RMS = 0.01

BG = "#1e1e1e"
FG = "#e0542a"
FG_DIM = "#aaaaaa"


class ToneDetectApp:
    def __init__(self, root):
        self.root = root
        root.title("ToneDetect")
        root.geometry("900x460")
        root.configure(bg=BG)

        self._build_device_bar()

        self.note_label = tk.Label(root, text="—", font=("Segoe UI", 48, "bold"), fg=FG, bg=BG)
        self.note_label.pack(pady=(10, 0))

        self.freq_label = tk.Label(root, text=" ", font=("Segoe UI", 12), fg=FG_DIM, bg=BG)
        self.freq_label.pack()

        self.fretboard = FretboardWidget(root, height=220)
        self.fretboard.pack(fill=tk.X, padx=20, pady=20)

        self.detector = YinPitchDetector(SAMPLE_RATE)
        self.audio = AudioInput(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE)
        self.audio.start()

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

        if buf is not None:
            rms = float((buf ** 2).mean() ** 0.5)
            if rms >= SILENCE_RMS:
                freq = self.detector.detect(buf)
                if freq:
                    note = freq_to_note(freq)
                    self.note_label.config(text=note["name"])
                    self.freq_label.config(text=f"{freq:.1f} Hz   {note['cents']:+.0f} cents")
                    self.fretboard.set_highlight(fretboard_positions(note["midi"]))
                else:
                    self._clear_display()
            else:
                self._clear_display()

        self.root.after(POLL_MS, self.poll_audio)

    def _clear_display(self):
        self.note_label.config(text="—")
        self.freq_label.config(text=" ")
        self.fretboard.set_highlight([])

    def on_close(self):
        self.audio.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    ToneDetectApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
