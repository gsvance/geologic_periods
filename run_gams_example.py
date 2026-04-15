#!/usr/bin/env python3
# Test the model using my GAMS example

# Created 7 Mar 2023 by Greg Vance


from typing import List

from model import solve_geologic_periods_problem, classic_scoring
from mytypes import Choices


s = [f"student-{i+1}" for i in range(8)]
t = [f"topic-{i+1}" for i in range(6)]

hp = [False for _ in range(len(s))]
hp[s.index('student-5')] = True

ch: List[Choices] = [
    ['topic-1', 'topic-4', 'topic-2'],
    ['topic-1', 'topic-5', 'topic-6'],
    ['topic-6', 'topic-1', 'topic-2'],
    ['topic-5', 'topic-6', 'topic-2'],
    ['topic-5', 'topic-3', 'topic-4'],
    ['topic-4', 'topic-3', 'topic-5'],
    ['topic-1', 'topic-6', 'topic-2'],
    ['topic-6', 'topic-3', 'topic-2'],
]

lims = (1, 2)

report = solve_geologic_periods_problem(
    s, t, ch,
    high_priority_flags=hp,
    scoring_system=classic_scoring,
    limits_per_topic=lims,
    shuffle_students=True,
    solver_output=True,
)

print(report)
