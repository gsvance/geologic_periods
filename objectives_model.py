"""Interface to the solver for the alternative multiple objectives model

As opposed to the scoring model, this approach to the geologic periods problem
involves calling the solver multiple times in sequence with different objective
functions and more constraints each time.
"""

from typing import Any, Callable

import numpy as np
import numpy.typing as npt
from scipy import optimize

from mytypes import Choices
from organization import Sets, Maps
from reporting import SolutionReport


def solve_geologic_periods_problem(
    student_names: list[str],
    topic_names: list[str],
    student_choices: list[Choices],
    high_priority_flags: list[bool] | None = None,
    limits_per_topic: tuple[int, int] | None = None,
    shuffle_students: bool = True,
    solver_output: bool = False,
) -> SolutionReport:
    """Solve a version of the geologic periods problem and return a report.

    This function organizes and validates the input data, translates the inputs
    to a linear programming matrix model, feeds the model to the milp() solver
    from scipy.optimize, and then translates the solution matrix back into a
    human-readable report format.

    The first two inputs are a list of the students' names and a list of names
    for each topic that must be assigned. Note that the students' names must be
    unique and the topic names must also be unique. The third input is a list
    containing lists of each students' choices, such that (for example) the 8th
    student's 3rd choice is accessible as student_choices[7][2]. Each sublist
    must be the same length, and each choice should either be a unique element
    of topic_names or None.

    If present, high_priority_flags should be a list of booleans with the same
    length as student_names. High priority students are flagged with entires
    that are True. The default is False for all students.

    If provided, limits_per_topic is a tuple of two ints giving the lower and
    upper bounds (in that order) on the number of students that can be assigned
    to any one topic. The default is a strict approach of forcibly balancing
    students among topics to the greatest extent mathematically possible.

    The shuffle_students flag indicates whether the list of students should be
    internally shuffled in order to avoid biasing the solver towards certain
    students because of their positions in the input list. The default is True
    because this lack of bias can be desirable, but it does mean that running
    this function with the same problem multiple times could yield different
    (but equally optimal) solutions.

    The solver_output flag indicates whether the scipy solver should print
    diagnostic messages as it works. This can be kind of noisy, especially when
    calling this function multiple times, so the default is False.
    """
    sets, maps = organize_input_data(
        student_names,
        topic_names,
        student_choices,
        high_priority_flags,
        shuffle_students,
    )
    model = set_up_model(sets, limits_per_topic, solver_output)
    result = optimize.milp(**model)
    return SolutionReport(sets, maps, result)


def organize_input_data(
    students: list[str],
    topics: list[str],
    choices: list[Choices],
    high_priority: list[bool] | None,
    shuffle: bool,
) -> tuple[Sets, Maps]:
    """Carry out initial organization of the problem's input data."""

    if high_priority is None:
        high_priority = [False for _ in students]
    sets = Sets(students, topics, choices, high_priority, shuffle)
    maps = Maps(sets)
    return sets, maps


def set_up_model(
    sets: Sets,
    limits_per_topic: tuple[int, int] | None,
    solver_output: bool,
) -> dict[str, Any]:
    """Translate model input data to a format understandable by milp()."""

    vars_shape = (sets.n_s, sets.n_t)

    scoring_weights = scoring_system(sets)

    all_students_assigned = optimize.LinearConstraint(
        np.vstack([_flat_ones_row(vars_shape, int(s)) for s in sets.s]),
        lb=1, ub=1
    )

    strict_min_per_topic = sets.n_s // sets.n_t
    strict_max_per_topic = -(-sets.n_s // sets.n_t)
    if limits_per_topic is None:
        min_per_topic = strict_min_per_topic
        max_per_topic = strict_max_per_topic
    else:
        min_per_topic, max_per_topic = limits_per_topic
        if min_per_topic > strict_min_per_topic:
            raise ValueError("min per topic is too large")
        if max_per_topic < strict_max_per_topic:
            raise ValueError("max per topic is too small")

    all_topics_balanced = optimize.LinearConstraint(
        np.vstack([_flat_ones_col(vars_shape, int(t)) for t in sets.t]),
        lb=min_per_topic, ub=max_per_topic
    )

    return {
        'c': -scoring_weights.flatten(),
        'integrality': np.ones(vars_shape, dtype='int8').flatten(),
        'bounds': optimize.Bounds(0, 1),
        'constraints': [all_students_assigned, all_topics_balanced],
        'options': {'disp': solver_output},
    }


# Utility function to create and flatten an array with a single row of ones
def _flat_ones_row(shape: tuple[int, int], row: int) -> npt.NDArray[np.int32]:
    matrix = np.zeros(shape, dtype='int32')
    matrix[row, :] = 1
    return matrix.flatten()


# Utility function to create and flatten an array with a single column of ones
def _flat_ones_col(shape: tuple[int, int], col: int) -> npt.NDArray[np.int32]:
    matrix = np.zeros(shape, dtype='int32')
    matrix[:, col] = 1
    return matrix.flatten()
