"""Class for informatively reporting the solver's results to the user

Created 7 Mar 2023 by Greg Vance
"""

import numpy as np

from mytypes import Array, Result
from organization import Sets, Maps


class SolutionReport:
    """Takes a scipy solver result and makes it more understandable."""

    def __init__(self, sets: Sets, maps: Maps, result: Result) -> None:
        """Initialize a new SolutionReport object with the provided data."""

        self.sets = sets
        self.maps = maps
        self.result = result

    def __str__(self) -> str:
        """Very involved str method that produces a human-readable report."""

        out = list()

        out.append(_header('scipy solver report'))
        out.append(f'solver message: {self.result.message}')
        out.append(f'success flag: {self.result.success}')
        out.append(f'status code: {self.result.status}')
        out.append(f'maximum score: {-int(self.result.fun)}')

        out.append(_header('solution array'))
        vars_shape = (self.sets.n_s, self.sets.n_t)
        assign = self.result.x.reshape(vars_shape).astype('int8')
        out.append(str(assign))

        out.append(_header('assignments by student'))
        for student in self.sets.students_unshuffled:
            s = self.maps.s[student]
            t = _find_one(assign[s, :])
            topic = self.maps.topics[t]
            hp = '*' if self.maps.high_priority[s] else ''
            choice = self.maps.choices[s, t]
            if choice is not None:
                choice_str = f'({choice} choice)'
            else:
                choice_str = '(unhappy)'
            line = f'{hp}{student}: {topic} {choice_str}'
            out.append(line)

        out.append(_header('assignments by topic'))
        indent = '  ' * 1
        for t in self.sets.t:
            topic = self.maps.topics[t]
            out.append(topic)
            s_t = _find_all_ones(assign[:, t])
            students = [self.maps.students[s] for s in s_t]
            if len(students) == 0:
                out.append(f'{indent}(no students assigned)')
                continue
            for s, student in zip(s_t, students):
                hp = '*' if self.maps.high_priority[s] else ''
                choice = self.maps.choices[s, t]
                if choice is not None:
                    choice_str = f'({choice} choice)'
                else:
                    choice_str = '(unhappy)'
                line = f'{indent}{hp}{student} {choice_str}'
                out.append(line)

        # breakdown of tuple scoring? maybe be aware of scoring systems.

        return '\n'.join(out)


# Utility function for producing standardized report section headers
def _header(text: str) -> str:
    emphasis = '*' * 4
    return ' '.join([emphasis, text.upper(), emphasis])


# Utility function to find the indices of 1s in a Numpy array of mostly 0s
def _find_all_ones(arr: Array) -> Array:
    assert np.all(np.logical_or(arr == 0, arr == 1))
    tup = np.nonzero(arr)
    assert len(tup) == 1
    ind = tup[0]
    return ind


# Utility function for finding the index of a single 1 in a Numpy array of 0s
def _find_one(arr: Array) -> int:
    ind = _find_all_ones(arr)
    assert ind.size == 1
    return ind[0]
