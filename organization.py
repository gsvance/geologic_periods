"""Classes for collecting and organizing the model input data

Created 7 Mar 2023 by Greg Vance
"""

import random
from typing import Dict, List, Tuple, Union

import numpy as np

from mytypes import Choices


class Sets:
    """Organizes all the simple sets and integer indicies for a problem."""

    def __init__(
        self,
        students: List[str],
        topics: List[str],
        choices: List[Choices],
        high_priority: List[bool],
        shuffle: bool,
    ) -> None:
        """Initialize a new Sets object containing the given problem data."""

        # Make copies of all the problem data
        self.students = list(students)
        self.topics = list(topics)
        self.choices = list(map(list, choices))
        self.high_priority = list(high_priority)
        self.shuffle = shuffle

        self._validate()

        # Shuffle the order of the students around so that everyone has an
        # equal chance of good or bad luck if there exist multiple optimal
        # solutions. Save the input ordering for the reporting stage after the
        # model has been solved.
        self.students_unshuffled = list(self.students)
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
        self.n_s = len(self.students)
        self.n_t = len(self.topics)
        self.n_c = len(self.choices[0])
        self.n_hp = sum(int(flag) for flag in self.high_priority)

        # Create Numpy array sets of inidices and high priority flags
        self.s = np.arange(self.n_s)
        self.t = np.arange(self.n_t)
        self.c = np.arange(self.n_c)
        self.hp = np.array(self.high_priority, dtype='int8')

        # Finally, generate the student preferences array to be passed off the
        # the model's scoring_system function
        self.pref = np.zeros((self.n_s, self.n_t, self.n_c), dtype='int8')
        for s in self.s:
            for t, topic in zip(self.t, self.topics):
                for c, choice in zip(self.c, self.choices[s]):
                    self.pref[s, t, c] = int(choice == topic)


class Maps:
    """Organizes the more complicated mapping structures for a problem."""

    def __init__(self, sets: Sets) -> None:
        """Initialize a new Maps object using the problem data from sets."""

        self.sets = sets
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
        self.s: Dict[str, int] = {
            name: s for name, s in zip(self.sets.students, self.sets.s)
        }
        self.t: Dict[str, int] = {
            name: t for name, t in zip(self.sets.topics, self.sets.t)
        }
        self.hp: Dict[str, int] = {
            name: hp for name, hp in zip(self.sets.students, self.sets.hp)
        }

        # Make maps from integer indices to the friendlier names and booleans
        self.students: Dict[int, str] = {
            s: name for name, s in self.s.items()
        }
        self.topics: Dict[int, str] = {
            t: name for name, t in self.t.items()
        }
        self.high_priority: Dict[int, bool] = {
            s: flag for s, flag in zip(self.sets.s, self.sets.high_priority)
        }

        # Now for the complicated (but probably most important) part
        # Make maps for retrieving a student's opinion on a particular topic
        self.c: Dict[Tuple[str, str], Union[int, None]] = dict()
        for s, choices_sublist in zip(self.sets.s, self.sets.choices):
            student = self.students[s]
            for topic in self.sets.topics:
                try:
                    c = choices_sublist.index(topic)
                except ValueError:
                    c = None
                self.c[student, topic] = c
        self.choices: Dict[Tuple[int, int], Union[str, None]] = dict()
        for (student, topic), c in self.c.items():
            s = self.s[student]
            t = self.t[topic]
            if c is not None:
                self.choices[s, t] = _nth_string(c + 1)
            else:
                self.choices[s, t] = c


# Utility function to simultaneously shuffle three lists into the same order
def _shuffle_together(list1: List, list2: List, list3: List) -> None:
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
