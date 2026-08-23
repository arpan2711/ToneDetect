"""Prep lesson for Chuck Berry's 'Johnny B. Goode', taught in the key of A
(the common teaching key, though the original recording sits in Bb).

The scale warm-up and chord shapes below are exact. The intro lick is a
simplified practice version built on the same 6ths double-stop technique
(same fret on the D and B strings) the real riff uses -- it is NOT claimed
to be a note-for-note transcription of Chuck Berry's recording. Swap in the
exact tab here if you want note-perfect accuracy; the rest of the lesson
doesn't depend on it.
"""

from ..lesson_model import Lesson, LessonSection, LessonStep

_warmup_notes = [
    ("A2", [(5, 0)]),
    ("B2", [(5, 2)]),
    ("C#3", [(5, 4)]),
    ("E3", [(4, 2)]),
    ("F#3", [(4, 4)]),
    ("A3", [(3, 2)]),
    ("B3", [(2, 0)]),
    ("C#4", [(2, 2)]),
    ("E4", [(1, 0)]),
    ("F#4", [(1, 2)]),
    ("A4", [(1, 5)]),
]

_warmup_steps = [
    LessonStep(
        label=f"Play {name}",
        expected_notes=[name],
        target_positions=positions,
    )
    for name, positions in _warmup_notes
]
# Ascend then descend back down, without repeating the top note.
_warmup_steps = _warmup_steps + list(reversed(_warmup_steps[:-1]))

warmup_section = LessonSection(
    title="Warm-up: A Major Pentatonic",
    description="The scale the intro lick and solo phrasing both live in. Go slow and clean before speeding up.",
    steps=_warmup_steps,
)

chords_section = LessonSection(
    title="Chords: A, D, E (I - IV - V)",
    description="The three open chords the whole song is built from.",
    steps=[
        LessonStep(
            label="Play A major (x02220)",
            expected_notes=["A2", "E3", "A3", "C#4", "E4"],
            target_positions=[(5, 0), (4, 2), (3, 2), (2, 2), (1, 0)],
        ),
        LessonStep(
            label="Play D major (xx0232)",
            expected_notes=["D3", "A3", "D4", "F#4"],
            target_positions=[(4, 0), (3, 2), (2, 3), (1, 2)],
        ),
        LessonStep(
            label="Play E major (022100)",
            expected_notes=["E2", "B2", "E3", "G#3", "B3", "E4"],
            target_positions=[(6, 0), (5, 2), (4, 2), (3, 1), (2, 0), (1, 0)],
        ),
    ],
)

lick_section = LessonSection(
    title="Intro lick (practice version)",
    description=(
        "Double-stops on the D and B strings, same fret each time -- that's what keeps "
        "the interval a 6th apart as you climb. This is a simplified practice pattern in "
        "the style of the real riff, not a verbatim transcription."
    ),
    steps=[
        LessonStep(
            label="Double-stop: fret 2 (E3 + C#4)",
            expected_notes=["E3", "C#4"],
            target_positions=[(4, 2), (2, 2)],
        ),
        LessonStep(
            label="Double-stop: fret 4 (F#3 + D#4)",
            expected_notes=["F#3", "D#4"],
            target_positions=[(4, 4), (2, 4)],
        ),
        LessonStep(
            label="Double-stop: fret 5 (G3 + E4)",
            expected_notes=["G3", "E4"],
            target_positions=[(4, 5), (2, 5)],
        ),
        LessonStep(
            label="Snap back: fret 2 (E3 + C#4)",
            expected_notes=["E3", "C#4"],
            target_positions=[(4, 2), (2, 2)],
        ),
        LessonStep(
            label="Resolve on open A (A2)",
            expected_notes=["A2"],
            target_positions=[(5, 0)],
        ),
    ],
)

progression_section = LessonSection(
    title="Put it together: the changes",
    description="Hit the changes in order -- this is the harmonic skeleton of the whole song.",
    steps=[
        LessonStep(label="Play A", expected_notes=["A2", "E3", "A3", "C#4", "E4"],
                    target_positions=[(5, 0), (4, 2), (3, 2), (2, 2), (1, 0)]),
        LessonStep(label="Play D", expected_notes=["D3", "A3", "D4", "F#4"],
                    target_positions=[(4, 0), (3, 2), (2, 3), (1, 2)]),
        LessonStep(label="Play A", expected_notes=["A2", "E3", "A3", "C#4", "E4"],
                    target_positions=[(5, 0), (4, 2), (3, 2), (2, 2), (1, 0)]),
        LessonStep(label="Play E", expected_notes=["E2", "B2", "E3", "G#3", "B3", "E4"],
                    target_positions=[(6, 0), (5, 2), (4, 2), (3, 1), (2, 0), (1, 0)]),
        LessonStep(label="Play D", expected_notes=["D3", "A3", "D4", "F#4"],
                    target_positions=[(4, 0), (3, 2), (2, 3), (1, 2)]),
        LessonStep(label="Play A", expected_notes=["A2", "E3", "A3", "C#4", "E4"],
                    target_positions=[(5, 0), (4, 2), (3, 2), (2, 2), (1, 0)]),
    ],
)

LESSON = Lesson(
    id="johnny_b_goode",
    title="Johnny B. Goode Prep (key of A)",
    description="Scale, chords, intro lick, and the I-IV-V changes for Chuck Berry's 'Johnny B. Goode'.",
    sections=[warmup_section, chords_section, lick_section, progression_section],
)
