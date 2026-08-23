"""Data model for lessons: a lesson is a sequence of sections, each made of
steps the practice engine checks live audio against.

Lessons are plain data (see tonedetect/lessons/) so new ones can be authored
without touching any detection or UI code.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

from .notes import note_name_to_midi


@dataclass
class LessonStep:
    label: str
    expected_notes: List[str]                      # note names, e.g. ["A2"] or ["E3", "C#4"]
    target_positions: List[Tuple[int, int]] = field(default_factory=list)  # (string, fret), for display only
    instructions: str = ""

    @property
    def expected_midis(self):
        return [note_name_to_midi(n) for n in self.expected_notes]


@dataclass
class LessonSection:
    title: str
    description: str
    steps: List[LessonStep]


@dataclass
class Lesson:
    id: str
    title: str
    description: str
    sections: List[LessonSection]

    def all_steps(self):
        for section in self.sections:
            for step in section.steps:
                yield section, step
