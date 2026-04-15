#!/usr/bin/env python3
# Test the model using a single randomly-generated example

# Created 11 Mar 2023 by Greg Vance


import itertools
import random
from typing import Dict, List, Tuple

from model import solve_geologic_periods_problem
from mytypes import Choices


# Parameters to sets limits on the randomization
N_VALIDATION_TRIALS = 100
MIN_N_STUDENTS, MAX_N_STUDENTS = (1, 9)
MIN_N_TOPICS, MAX_N_TOPICS = (1, 5)
MIN_N_CHOICES, MAX_N_CHOICES = (1, 4)
MIN_N_HIGH_PRIORITY, MAX_N_HIGH_PRIORITY = (0, 3)
PROB_NONE_CHOICE = 1.0 / 50


def randomize() -> Tuple[List[str], List[str], List[Choices], List[bool], int]:
    """Generate one randomized version of the geologic periods problem."""

    n_students = random.randint(MIN_N_STUDENTS, MAX_N_STUDENTS)
    n_topics = random.randint(MIN_N_TOPICS, MAX_N_TOPICS)
    n_choices = random.randint(MIN_N_CHOICES, min(MAX_N_CHOICES, n_topics))
    n_high_priority = random.randint(MIN_N_HIGH_PRIORITY,
                                     min(MAX_N_HIGH_PRIORITY, n_students))

    students = [f"Student {i+1}" for i in range(n_students)]
    topics = [f"Topic {i+1}" for i in range(n_topics)]

    choices = []
    n_none = 0
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

    return students, topics, choices, high_priority, n_none


def tuple_score(
    students: List[str],
    topics: List[str],
    choices: List[Choices],
    high_priority: List[bool],
    assignment: Dict[str, str],
) -> Tuple[int, ...]:
    """Return the old-style tuple score for a set of assignments."""

    n_s = len(students)
    n_t = len(topics)
    n_c = len(choices[0])

    min_topic_sum = n_s // n_t
    max_topic_sum = -(-n_s // n_t)
    for topic in topics:
        topic_sum = sum(
            int(assigned == topic) for assigned in assignment.values()
        )
        if not (min_topic_sum <= topic_sum <= max_topic_sum):
            return tuple((2 * n_c + 1) * [0])

    score = (2 * n_c + 1) * [0]

    for s, student in enumerate(students):
        topic = assignment[student]
        for c in range(n_c):
            if choices[s][c] == topic:
                score[0] += 1
                score[1 + c] += 1
                if high_priority[s]:
                    score[1 + n_c + c] += 1

    return tuple(score)


def brute_force_solutions(
    students: List[str],
    topics: List[str],
    choices: List[Choices],
    high_priority: List[bool],
) -> List[Dict[str, str]]:
    """Inefficiently produce the list of optimal solutions by brute force."""

    solutions = []
    best = tuple((2 * len(choices) + 1) * [0])

    all_options = itertools.product(*[list(topics) for _ in students])
    for assigned_topics in all_options:

        proposed_solution = dict(zip(students, assigned_topics))
        score = tuple_score(students, topics, choices, high_priority,
                            proposed_solution)

        if score > best:
            solutions.clear()
            best = score
        if score == best:
            solutions.append(proposed_solution)

    return solutions


# Run several randomized validation trials to check the model.py implementation
for i in range(N_VALIDATION_TRIALS):

    print(f'Running trial {i+1} of {N_VALIDATION_TRIALS}...')

    s, t, c, hp, nn = randomize()
    print(f'Random: n_s={len(s)}, n_t={len(t)}, n_c={len(c[0])},'
          f' n_hp={sum(hp)}, n_n={nn}')

    report = solve_geologic_periods_problem(s, t, c, hp)
    assign = report.result.x.reshape((len(s), len(t))).astype('int8')
    solution = dict()
    for student in report.sets.students_unshuffled:
        i_s = report.maps.s[student]
        i_t = [int(x) for x in assign[i_s, :]].index(1)
        solution[student] = t[i_t]

    if solution not in brute_force_solutions(s, t, c, hp):
        print("FAILED!")
        print(s)
        print(t)
        print(c)
        print(hp)
        break
    else:
        print("Succeeded.")
