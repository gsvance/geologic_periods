# Python 3

# Auxiliary file for algorithm utilities that would clutter AssignStudents.py
# Some of the things in here are data structure classes that I need
# Others things are subroutines of the main algorithm or setup procedures

# Last modified 20 Dec 2020 by Greg Vance

# PACKAGE IMPORTS AND CONSTANTS
###############################

import itertools

# DATA STRUCTURE CLASSES
########################

class Matching:
	
	def __init__(self, options, students):
		"""Create a new matching using the options and student name lists."""
		
		self.by_option = {option: set() for option in options}
		self.by_student = {student: None for student in students}
		#self.unhappy = set()
	
	def add_pair(self, u, v):
		"""Add a new (student, option) pair to the matching."""
		
		# Figure out which way round the option and student were given
		if u in self.by_option and v in self.by_student:
			option, student = u, v
		elif v in self.by_option and u in self.by_student:
			option, student = v, u
		else:
			raise KeyError(repr((u, v)))
		
		# Make sure the student isn't already matched to another option
		if self.by_student[student] is None:
			self.by_option[option].add(student)
			self.by_student[student] = option
		else:
			message = "student {!r} has already been matched"
			raise ValueError(message.format(student))
	
	def delete_pair(self, u, v):
		"""Remove a particular (student, option) pair from the matching."""
		
		# Figure out which one is the option and which is the student
		if u in self.by_option and v in self.by_student:
			option, student = u, v
		elif v in self.by_option and u in self.by_student:
			option, student = v, u
		else:
			raise KeyError(repr((u, v)))
		
		# Make sure that given the pair exists before trying to delete it
		if self.by_student[student] == option:
			self.by_option[option].remove(student)
			self.by_student[student] = None
		else:
			message = "student {!r} is not matched to option {!r}"
			raise ValueError(message.format(student, option))
	
	def obeys_max_per_option(self, max_per_option, option=None):
		"""Return whether the given option has <= max_per_option students
		matched to it. If no option is given, then check all options.
		"""
		
		# If an option was given, then check that option
		if option is not None:
			return len(self.by_option[option]) <= max_per_option
		
		# Otherwise, check all of the options together
		for assigned_students in self.by_option.values():
			if len(assigned_students) > max_per_option:
				return False
		return True
	
	def obeys_min_per_option(self, min_per_option, option=None):
		"""Return whether the given option has >= min_per_option students
		matched to it. If no option is given, then check all options.
		"""
		
		# If we got an option, check that one
		if option is not None:
			return len(self.by_option[option]) >= min_per_option
		
		# With no option given, check all of them together
		for assigned_students in self.by_option.values():
			if len(assigned_students) < min_per_option:
				return False
		return True
	
	def as_tuples(self):
		"""Return a frozen set of (student, option) tuples fully summarizing
		the matching.
		"""
		
		return frozenset(self.by_student.items())
	
	def clear(self):
		"""Delete all pairs from the matching."""
		
		for student in self.by_student.keys():
			self.by_student[student] = None
		for option in self.by_option.keys():
			self.by_option[option].clear()
	
	def empty_options(self):
		"""Return a set of the names of all options without any matched
		students.
		"""
		
		empty = set()
		for option, assigned_students in self.by_option.items():
			if len(assigned_students) == 0:
				empty.add(option)
		return empty
	
	def lookup(self, u):
		"""Return the students or the option that are matched with the given
		option or student.
		"""
		
		if u in self.by_student:
			return self.by_student[u]
		elif u in self.by_option:
			return set(self.by_option[u])
		else:
			raise KeyError(repr(u))
	
	def underfilled(self, limit=1):
		return {x for x, y in self.by_option.items() if len(y) < limit}

class MatchingsIterator:
	
	def __init__(self, options, choices):
		""""""
		
		self.options = set(options)
		self.choices = {name: list(picks) for name, picks in choices.items()}
	
	def all_permitted_matchings(self, n_unhappy):
		""""""
		
		self.match = Matching(self.options, students=self.choices.keys())
		
		for unhappy in itertools.combinations(self.choices.keys(), n_unhappy):
			
			self.unhappy = set(unhappy)
			yield from self._iter_recurse()
	
	def _iter_recurse(self, index=0):
		
		if index == len(self.choices):
			for perm in itertools.permutations(self.unhappy):
				for n, e in zip(perm, self.match.underfilled()):
					self.match.add_pair(n, e)
				yield self.match
				for n, e in zip(perm, self.match.underfilled()):
					self.match.delete_pair(n, e)
		
		else:
			name = sorted(self.choices.keys())[index]
			if name in self.unhappy:
				yield from self._iter_recurse(index + 1)
			else:
				for pick in self.choices[name]:
					self.match.add_pair(name, pick)
					if self.match.obeys_max_per_option(2, pick):
						yield from self._iter_recurse(index + 1)
					self.match.delete_pair(name, pick)

class ScoreCalculator:
	
	def __init__(self, choices, high_priority):
		""""""
		
		if set(choices.keys()) != set(high_priority.keys()):
			raise TypeError("dict key set mismatch detected")
		
		lengths = {len(picks) for picks in choices.values()}
		if len(lengths) != 1:
			raise TypeError("choice list lengths mismatch")
		self.n_choices = lengths.pop()
		
		self.choices = {name: list(picks) for name, picks in choices.items()}
		self.high_priority = {name: hp for name, hp in high_priority.items()}
	
	def calculate_score(self, match):
		""""""
		
		score = list()
		
		score.append(len(self.choices))  # Number of happy students
		for i in range(self.n_choices * 2):
			score.append(0)
		
		for name, picks in self.choices.items():
			
			assigned = match.lookup(name)
			hp = self.high_priority[name]
			
			if assigned is None:
				raise ValueError("scoring an incomplete match")
			
			try:
				rank = picks.index(assigned)
			except ValueError:
				rank = None
			
			if rank is not None:
				score[1 + rank] += 1
				if hp:
					score[1 + self.n_choices + rank] += 1
			else:
				score[0] -= 1
		
		return tuple(score)
	
	def interpret_score(self, score):
		""""""
		
		s0 = "{:d}/{:d} happy students".format(score[0], len(self.choices))
		
		x1 = ["{:d} students got their choice #{:d}".format(score[i], i) \
			for i in range(1, 1 + self.n_choices)]
		x2 = ["{:d} hp students got their choice #{:d}".format(score[i], i) \
			for i in range(1 + self.n_choices, 1 + 2 * self.n_choices)]
		
		return '\n'.join([s0] + x1 + x2)

# ALGORITHM SUBROUTINES
#######################



# ALGORITHM-ADJACENT FUNCTIONS
##############################




