"""Tkinter Canvas widget that draws a fretboard diagram and highlights notes."""

import tkinter as tk

from .notes import NUM_FRETS, STANDARD_TUNING, midi_to_note_name

# Drawn top-to-bottom: high E (string 1) at the top, low E (string 6) at the bottom.
STRING_ORDER = [1, 2, 3, 4, 5, 6]

SINGLE_MARKER_FRETS = {3, 5, 7, 9, 15}
DOUBLE_MARKER_FRETS = {12}

BG = "#f5f0e6"
FRET_COLOR = "#999999"
NUT_COLOR = "#2b2b2b"
STRING_COLOR = "#555555"
MARKER_COLOR = "#d8cdb0"
HIGHLIGHT_FILL = "#e0542a"
HIGHLIGHT_OUTLINE = "#8a2f14"
TEXT_COLOR = "#333333"


def _blend(fg_hex, bg_hex, alpha):
    """Fake translucency: blend fg over bg at the given alpha, since Tk
    canvas fills don't support real alpha compositing."""
    fg = tuple(int(fg_hex[i:i + 2], 16) for i in (1, 3, 5))
    bg = tuple(int(bg_hex[i:i + 2], 16) for i in (1, 3, 5))
    blended = tuple(round(alpha * f + (1 - alpha) * b) for f, b in zip(fg, bg))
    return "#%02x%02x%02x" % blended


_SCALE_BASE = "#2f6fb0"
SCALE_NOTE_COLOR = _blend(_SCALE_BASE, BG, 0.32)
SCALE_ROOT_COLOR = _blend(_SCALE_BASE, BG, 0.60)
SCALE_ROOT_OUTLINE = _blend("#1c4066", BG, 0.75)

TARGET_RING_COLOR = "#2fa84f"


class FretboardWidget(tk.Canvas):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("bg", BG)
        kwargs.setdefault("highlightthickness", 0)
        super().__init__(master, **kwargs)
        self.margin_left = 55
        self.margin_top = 25
        self.margin_bottom = 25
        self.margin_right = 25
        self._highlight_positions = []
        self._scale_positions = []
        self._target_positions = []
        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    def set_highlight(self, positions):
        self._highlight_positions = positions
        self._redraw()

    def set_scale_overlay(self, positions):
        """positions: iterable of (string_num, fret, is_root)."""
        self._scale_positions = positions
        self._redraw()

    def set_target_overlay(self, positions):
        """positions: iterable of (string_num, fret) -- lesson step targets."""
        self._target_positions = positions
        self._redraw()

    def _string_y(self, string_num, board_h):
        idx = STRING_ORDER.index(string_num)
        gap = board_h / (len(STRING_ORDER) - 1)
        return self.margin_top + idx * gap

    def _fret_x(self, fret, fret_w):
        return self.margin_left + fret * fret_w

    def _note_xy(self, string_num, fret, board_h, fret_w):
        y = self._string_y(string_num, board_h)
        x = (self.margin_left - 15) if fret == 0 else self._fret_x(fret - 0.5, fret_w)
        return x, y

    def _redraw(self):
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 20 or height < 20:
            return

        board_w = width - self.margin_left - self.margin_right
        board_h = height - self.margin_top - self.margin_bottom
        fret_w = board_w / NUM_FRETS
        mid_y = self.margin_top + board_h / 2

        # Inlay markers, centered between fret lines.
        for f in SINGLE_MARKER_FRETS:
            cx = self._fret_x(f - 0.5, fret_w)
            self.create_oval(cx - 5, mid_y - 5, cx + 5, mid_y + 5, fill=MARKER_COLOR, outline="")
        for f in DOUBLE_MARKER_FRETS:
            cx = self._fret_x(f - 0.5, fret_w)
            self.create_oval(cx - 5, mid_y - 22, cx + 5, mid_y - 12, fill=MARKER_COLOR, outline="")
            self.create_oval(cx - 5, mid_y + 12, cx + 5, mid_y + 22, fill=MARKER_COLOR, outline="")

        # Fret lines (nut is thick).
        for f in range(NUM_FRETS + 1):
            x = self._fret_x(f, fret_w)
            if f == 0:
                self.create_line(x, self.margin_top, x, self.margin_top + board_h, width=5, fill=NUT_COLOR)
            else:
                self.create_line(x, self.margin_top, x, self.margin_top + board_h, width=1, fill=FRET_COLOR)

        # Strings, thicker towards the low E.
        for string_num in STRING_ORDER:
            y = self._string_y(string_num, board_h)
            lw = 1 + (6 - string_num) * 0.4
            self.create_line(self.margin_left, y, self.margin_left + board_w, y, width=lw, fill=STRING_COLOR)
            label = midi_to_note_name(STANDARD_TUNING[string_num])
            self.create_text(self.margin_left - 25, y, text=label, font=("Segoe UI", 9), fill=TEXT_COLOR)

        # Fret numbers.
        for f in range(1, NUM_FRETS + 1):
            x = self._fret_x(f - 0.5, fret_w)
            self.create_text(x, self.margin_top + board_h + 12, text=str(f), font=("Segoe UI", 8), fill="#777777")

        # Scale overlay: translucent, drawn under the played-note highlight
        # so both stay visible even when a played note lands on a scale tone.
        for string_num, fret, is_root in self._scale_positions:
            x, y = self._note_xy(string_num, fret, board_h, fret_w)
            if is_root:
                r = 10
                self.create_oval(x - r, y - r, x + r, y + r, fill=SCALE_ROOT_COLOR, outline=SCALE_ROOT_OUTLINE, width=1)
            else:
                r = 7
                self.create_oval(x - r, y - r, x + r, y + r, fill=SCALE_NOTE_COLOR, outline="")

        # Lesson step targets: hollow rings, drawn under the played-note
        # highlight so a correct hit shows the orange dot landing inside the ring.
        for string_num, fret in self._target_positions:
            x, y = self._note_xy(string_num, fret, board_h, fret_w)
            r = 13
            self.create_oval(x - r, y - r, x + r, y + r, outline=TARGET_RING_COLOR, width=3)

        # Highlighted (played) note positions, on top of everything else.
        for string_num, fret in self._highlight_positions:
            x, y = self._note_xy(string_num, fret, board_h, fret_w)
            r = 11
            self.create_oval(x - r, y - r, x + r, y + r, fill=HIGHLIGHT_FILL, outline=HIGHLIGHT_OUTLINE, width=2)
