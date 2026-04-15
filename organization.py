"""Classes for collecting and organizing the model input data

Created 7 Mar 2023 by Greg Vance
"""

import random

import numpy as np
import numpy.typing as npt

from mytypes import Choices


class Sets:
    """Organizes all the simple sets and integer indicies for a problem."""

    def __init__(
        self,
        students: list[str],
        topics: list[str],
        choices: list[Choices],
        high_priority: list[bool],
        shuffle: bool,
    ) -> None:
        """Initialize a new Sets object containing the given problem data."""

        # Make copies of all the problem data
        self.students: list[str] = list(students)
        self.topics: list[str] = list(topics)
        self.choices: list[Choices] = list(map(list, choices))
        self.high_priority: list[bool] = list(high_priority)
        self.shuffle: bool = shuffle

        self._validate()

        # Shuffle the order of the students around so that everyone has an
        # equal chance of good or bad luck if there exist multiple optimal
        # solutions. Save the input ordering for the reporting stage after the
        # model has been solved.
        self.students_unshuffled: list[str] = list(self.students)
        if self.shuffle:
            _shuffle_together(self.students, self.choices, self.high_priority)

        self._populate()

    def _validate(self) -> None:
        # This method makes sure that the problem specification makes sense,
        # but will be complemeneted by further validation in Maps._validate()
        if len(self.students) < 1:
            raise ValueError("fewer than one student")
        if len(self.topics) < 1:
            raise ValueError("fewer than one topic")
        if len(self.choices) != len(self.students):
            raise TypeError("students and choices are mismatched")
        if len(set(map(len, self.choices))) != 1:
            raise TypeError("inconsistent number of choices")
        if len(self.choices[0]) < 1:
            raise ValueError("fewer than one choice")
        if len(self.high_priority) != len(self.students):
            raise TypeError("students and high priority flags are mismatched")

    def _populate(self) -> None:

        # Create attribute variables for the sizes of each set
        self.n_s: int = len(self.students)
        self.n_t: int = len(self.topics)
        self.n_c: int = len(self.choices[0])
        self.n_hp: int = sum(int(flag) for flag in self.high_priority)

        # Create Numpy array sets of inidices and high priority flags
        self.s: npt.NDArray[np.int32] = np.arange(self.n_s, dtype='int32')
        self.t: npt.NDArray[np.int32] = np.arange(self.n_t, dtype='int32')
        self.c: npt.NDArray[np.int32] = np.arange(self.n_c, dtype='int32')
        self.hp: npt.NDArray[np.int8] = np.array(
            self.high_priority, dtype='int8',
        )

        # Finally, generate the student preferences array to be passed off the
        # the model's scoring_system function
        self.pref: npt.NDArray[np.int8] = np.zeros(
            (self.n_s, self.n_t, self.n_c), dtype='int8',
        )
        for s in self.s:
            for t, topic in zip(self.t, self.topics):
                for c, choice in zip(self.c, self.choices[s]):
                    self.pref[s, t, c] = int(choice == topic)


class Maps:
    """Organizes the more complicated mapping structures for a problem."""

    def __init__(self, sets: Sets) -> None:
        """Initialize a new Maps object using the problem data from sets."""

        self.sets: Sets = sets
        self._validate()
        self._populate()
        del self.sets  # Remove the reference now that we no longer need it

    def _validate(self) -> None:
        # This method further ensures that the problem specification is valid,
        # and is meant to follow up on the validations from Sets._validate()
        if len(set(self.sets.students)) != self.sets.n_s:
            raise ValueError("non-unique students")
        if len(set(self.sets.topics)) != self.sets.n_t:
            raise ValueError("non-unique topics")
        for choices_sublist in self.sets.choices:
            if len(set(choices_sublist)) != self.sets.n_c:
                raise ValueError("non-unique choices")
            for topic_choice in choices_sublist:
                non_none = (topic_choice is not None)
                if non_none and topic_choice not in self.sets.topics:
                    raise ValueError("invalid topic choice")

    def _populate(self) -> None:

        # Make maps from student or topic names to the Numpy integer sets
        self.s: dict[str, int] = {
            name: int(s) for name, s in zip(self.sets.students, self.sets.s)
        }
        self.t: dict[str, int] = {
            name: int(t) for name, t in zip(self.sets.topics, self.sets.t)
        }
        self.hp: dict[str, int] = {
            name: int(hp) for name, hp in zip(self.sets.students, self.sets.hp)
        }

        # Make maps from integer indices to the friendlier names and booleans
        self.students: dict[int, str] = {
            s: name for name, s in self.s.items()
        }
        self.topics: dict[int, str] = {
            t: name for name, t in self.t.items()
        }
        self.high_priority: dict[int, bool] = {
            int(s): flag
            for s, flag in zip(self.sets.s, self.sets.high_priority)
        }

        # Now for the complicated (but probably most important) part
        # Make maps for retrieving a student's opinion on a particular topic
        self.c: dict[tuple[str, str], int | None] = dict()
        for s, choices_sublist in zip(self.sets.s, self.sets.choices):
            student = self.students[int(s)]
            for topic in self.sets.topics:
                try:
                    c = choices_sublist.index(topic)
                except ValueError:
                    c = None
                self.c[student, topic] = c
        self.choices: dict[tuple[int, int], str | None] = dict()
        for (student, topic), c in self.c.items():
            s = self.s[student]
            t = self.t[topic]
            if c is not None:
                self.choices[s, t] = _nth_string(c + 1)
            else:
                self.choices[s, t] = c


# Utility function to simultaneously shuffle three lists into the same order
def _shuffle_together[T1, T2, T3](
    list1: list[T1], list2: list[T2], list3: list[T3],
) -> None:
    zipped = list(zip(list1, list2, list3))
    random.shuffle(zipped)
    list1[:] = [z[0] for z in zipped]
    list2[:] = [z[1] for z in zipped]
    list3[:] = [z[2] for z in zipped]


# Silly utility function to convert an int to an 'nth' string
# Examples: 1 -> '1st', 4 -> '4th', 13 -> '13th', 22 -> '22nd'
def _nth_string(n: int) -> str:

    if n < 0:
        return '-' + _nth_string(-n)

    last_digit = n % 10
    last_two_digits = n % 100

    if last_digit == 1 and last_two_digits != 11:
        return str(n) + 'st'
    elif last_digit == 2 and last_two_digits != 12:
        return str(n) + 'nd'
    elif last_digit == 3 and last_two_digits != 13:
        return str(n) + 'rd'
    else:
        return str(n) + 'th'
