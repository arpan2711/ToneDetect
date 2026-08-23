"""Runs a Lesson against live-detected notes: tracks the current step,
checks whether it's been played correctly, and advances when it has.

Matching is on pitch only (a set of expected MIDI notes), not string/fret --
audio alone can't tell which string produced a given note. A step counts as
played once every expected note is present in what's currently detected
(extra incidental notes are tolerated) and that match holds steadily for
MATCH_HOLD_MS, to avoid triggering on a passing transient.
"""

MATCH_HOLD_MS = 150


class PracticeSession:
    def __init__(self, lesson):
        self.lesson = lesson
        self.steps = [step for _, step in lesson.all_steps()]
        self.index = 0
        self.correct_count = 0
        self.finished = False
        self._match_since = None

    @property
    def current_step(self):
        if self.finished or not self.steps:
            return None
        return self.steps[self.index]

    @property
    def progress(self):
        return self.index, len(self.steps)

    def reset(self):
        self.index = 0
        self.correct_count = 0
        self.finished = False
        self._match_since = None

    def check(self, detected_midis, now):
        """detected_midis: set of MIDI notes currently detected. Returns True
        if this call completed (advanced past) the current step."""
        step = self.current_step
        if step is None:
            return False

        expected = set(step.expected_midis)
        is_match = bool(detected_midis) and expected.issubset(detected_midis)

        if is_match:
            if self._match_since is None:
                self._match_since = now
            elif (now - self._match_since) * 1000 >= MATCH_HOLD_MS:
                self._advance()
                return True
        else:
            self._match_since = None
        return False

    def skip(self):
        """Move on without crediting this step as correctly played."""
        self._match_since = None
        self._move_next()

    def _advance(self):
        self.correct_count += 1
        self._match_since = None
        self._move_next()

    def _move_next(self):
        if self.index + 1 >= len(self.steps):
            self.finished = True
        else:
            self.index += 1
