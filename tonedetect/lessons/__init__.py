"""Lesson registry. Add a new module here and register it in LESSONS to add
a lesson to the app -- lessons are plain data, no detection/UI changes needed.
"""

from .johnny_b_goode import LESSON as JOHNNY_B_GOODE

LESSONS = {
    JOHNNY_B_GOODE.id: JOHNNY_B_GOODE,
}
