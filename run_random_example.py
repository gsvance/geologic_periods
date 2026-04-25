#!/usr/bin/env python3
# Test the model using a single randomly-generated example

# Created 11 Mar 2023 by Greg Vance


import random
from typing import Final

from scoring_model import solve_geologic_periods_problem
from mytypes import Choices


# Parameters to sets limits on the randomization
MIN_N_STUDENTS: Final[int] = 1
MAX_N_STUDENTS: Final[int] = 120
MIN_N_TOPICS: Final[int] = 1
MAX_N_TOPICS: Final[int] = 30
MIN_N_CHOICES: Final[int] = 1
MAX_N_CHOICES: Final[int] = 6
MIN_N_HIGH_PRIORITY: Final[int] = 0
MAX_N_HIGH_PRIORITY: Final[int] = 12
PROB_NONE_CHOICE: Final[float] = 1.0 / 150

n_students = random.randint(MIN_N_STUDENTS, MAX_N_STUDENTS)
n_topics = random.randint(MIN_N_TOPICS, MAX_N_TOPICS)
n_choices = random.randint(MIN_N_CHOICES, min(MAX_N_CHOICES, n_topics))
n_high_priority = random.randint(
    MIN_N_HIGH_PRIORITY, min(MAX_N_HIGH_PRIORITY, n_students),
)

students = [f"Student {i+1}" for i in range(n_students)]
topics = [f"Topic {i+1}" for i in range(n_topics)]

choices, n_none = [], 0
for student in students:
    my_choices: Choices = random.sample(topics, k=n_choices)
    random.shuffle(my_choices)
    for i in range(n_choices):
        if random.random() < PROB_NONE_CHOICE:
            my_choices[i] = None
            n_none += 1
    choices.append(list(my_choices))

high_priority = [False for _ in range(n_students)]
for i in random.sample(range(n_students), k=n_high_priority):
    high_priority[i] = True

if n_high_priority == 0 and bool(random.randrange(2)):
    report = solve_geologic_periods_problem(
        students, topics, choices, solver_output=True,
    )
else:
    report = solve_geologic_periods_problem(
        students, topics, choices, high_priority, solver_output=True,
    )

print(report)
print(
    f'RANDOMIZATION: {n_students} students ({n_high_priority}'
    + f' high priority), {n_topics} topics, {n_choices} choices'
    + f' ({n_none} none)'
)
