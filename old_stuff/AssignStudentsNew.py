#!/usr/bin/env python3

# Algorithm for assigning "options" (i.e., geologic periods) to students
# Assignments are based, as much as possible, on students' top three choices
# A few students, marked as high priority, get more weight applied to them

# COMMENTS FROM CONVERSATION WITH RHONDA, 8 DEC 2020
# Assign at most two students per geologic period
# Prioritize having as many students as possible get one of their choices
# Secondly, grant as many first choices as possible
# Then as many second choices, then as many third choices
# All else being equal, prioritize the choices of a high priority student
# What if the optimal solution leaves one or more geologic periods empty?
# - Make sure to put at least 1 student in each period, this is essential
# How should we assign students who can't get any of their choices?
# - Prioritize assigning them to the most empty geologic periods
# Max students per geologic period might need to be increased to 3 sometimes

# CURRENT STRATEGY:
# Optimize for the same set of factors and priorities as the older strategy
#  0. Obey min and max, and assign everyone a single project
#  1. Maximize the number of "happy" students
#  2. Maximize the number of 1st choices, then 2nd choices, and so on
#  3. Prioritize choices of HP students, all else being equal
# Those first couple priorities are actually decently restrictive conditions
# A really good algorithm would exploit those restrictions to its advantage
# 

# OLD STRATEGY FROM DEC 2020:
# REPEATED RANDOM SERIAL DICTATORSHIP!!! (with scoring as below)
# or........
# Optimize for only one factor at a time, prioritizing factors like so:
#  0. Assign exactly one project option to every student in the class
#  1. Satisfy min and max numbers of students assigned per geologic period
#  2. Minimize the number of students assigned to something they didn't choose
#  3. Maximize the number of students who got their first choice
#  4.    "      "    "    "     "      "   "    "   second choice
#  5.    "      "    "    "     "      "   "    "   third choice
#  6. All else being equal, prioritize the picks of a high priority student
# How do we find a solution in practice that fits all of these criteria?
#  Define an "unhappy" student to be one who doesn't get any of their choices
#  Priority #2 above says to "minimize the number of unhappy students"
#  Geologic periods that recieved no votes at all are helpful here, since
#  at least one unhappy student will need to be assigned to there
#  This provides a nice lower bound on the number of unhappy students
#  Starting with that lower bound, iterate over all possible matchings (*)
#  If no matchings work, then add another unhappy student and try again
#  If one or more models work, choose between them using priorities 3-6
# The iteration step (*) has to check through a lot of possible matchings
#  If I'm not clever about how I do it, it will take waaaaay too long to run
#  Let's use iterators for this so I'm not storing all of them simultaneously
#  Use a class data structure with dicts for keeping track of the matching
#  Use a recursive generator with effectively one nested for loop per student
#  Check the max assignment limits per geologic period at every level
#  Hopefully we can cut out enough potential matchings to make it run quickly

# OLD STRATEGY FROM NOV 2020:
# It's a variant of the "assignment problem" called "rank-maximal allocation"
# Let's solve it using the matrix version of the "Hungarian algorithm"
# This is not simple, so we will use scipy.optimize.linear_sum_assignment()
# All we have to do is carefully set up the input cost matrix it expects
# We want to do the whole "greedy matching" "rank-maximal allocation" thing
# That means "maximize the number of students getting their first choice"
# Afterwards, we maximize the number getting their second choice and so on
# Assigning a student their first choice should be worth a ton of points
# It should be worth more than *any* number of lesser choice assignments

# Last modified 20 Mar 2021 by Greg Vance

# IMPORTS
###########

import pandas as pd  # Uses the xlrd package to read MS Excel files
import re
import math
import itertools as it
import random

# CONSTANTS
#############

# File name strings to use for input/output
OPTIONS_FILE = "Colors.txt"  # List of colors to pick from
#OPTIONS_FILE = "GeologicPeriods.txt"  # List of geologic periods to pick from
STUDENTS_FILE = "FakeChoices.csv"  # Student choices and high priorities
OUTPUT_FILE = "Assignments.txt"  # Final student assignments from algorithm

# Parameters for the matching algorithm


# MAIN FUNCTION
#################

def main():
	
	# Read the options list and student data from the appropriate input files
	# The students file will also tell us how many choices each student gets
	options = read_options(OPTIONS_FILE)
	students, n_choices = read_student_data(STUDENTS_FILE, options)
	
	# Determine a few other important numbers from the data
	n_options = len(options)
	n_students = len(students)
	min_per_option = math.floor(n_students / n_options)  # Can change this
	max_per_option = math.ceil(n_students / n_options)  # Can change this
	
	# Make sure the minimum and maximum per option can be satisfied
	assert min_per_option * n_options <= n_students, "cannot satisfy minimum"
	assert max_per_option * n_options >= n_students, "cannot satisfy maximum"
	
	# Set up the mutable matching data structure for the algorithm
	match = Matching(students, options)
	
	# Run the recursive algorithm to find the best student-option pairings
	best_pairings, best_score = recursive_assignment_algorithm(match, students,
		options, n_choices, min_per_option, max_per_option)
	
	# Clear the matching data structure and fill it with the best matches
	match.erase_all()
	match.assign_pairs(best_pairings)

	# Print the score of the best matching and the matching itself
	print("Score of best matching:", best_score)
	print("Best matching:")
	match.pretty_print_in_order(options, students, n_choices)

# SUBROUTINES
###############

def read_options(options_file_name):
	"""Read the list of geologic period options from the input text file and
	make sure they are all unique, then return a list of strings.
	"""
	
	# Read options from TXT file, expecting one per non-blank line
	with open(options_file_name, 'r') as options_file:
		options = [line.strip() for line in options_file if line.strip() != ""]
	
	# Return the list of options as long as they are all unique
	assert len(options) == len(set(options)), "options must all be unique"
	return options

def read_student_data(students_file_name, options_list):
	""""""
	
	# Use pandas to read a CSV or XLS(X) file
	if students_file_name.endswith('.csv'):
		df = pd.read_csv(students_file_name)
	elif students_file_name.endswith(('.xls', '.xlsx')):
		df = pd.read_excel(students_file_name)
	else:
		raise TypeError("unsupported students data file format")
	
	# Regular expressions to try and match the column headers
	name_re = re.compile(r"(\A|\s+)NAME(\Z|\s+)", re.IGNORECASE)
	hp_re = re.compile(r"(\A|\s+)PRIORITY(\Z|\s+)", re.IGNORECASE)
	choice_re = re.compile(r"(\A|\s+)CHOICE(\Z|\s+)", re.IGNORECASE)
	
	# Identify the columns in the spreadsheet using the REs
	columns = df.columns.tolist()
	name_matches = [col for col in columns if name_re.search(col)]
	hp_matches = [col for col in columns if hp_re.search(col)]
	choice_matches = [col for col in columns if choice_re.search(col)]
	all_matches = name_matches + hp_matches + choice_matches
	
	# Sanity check the column identities as much as possible
	assert len(all_matches) == len(set(all_matches)), "column id failure"
	assert 1 <= len(name_matches) <= 2, "column id failure"
	assert len(hp_matches) == 1, "column id failure"
	assert len(choice_matches) >= 1, "column id failure"
	
	# Extract student names and high priority info from the pandas dataframe
	if len(name_matches) == 2:
		n1, n2 = name_matches
		names = list(zip(df[n1].tolist(), df[n2].tolist()))
	else:  # len(name_matches) == 1
		names = df[name_matches[0]].tolist()
	hps = df[hp_matches[0]].tolist()
	
	# Make sure that the student names are all unique
	assert len(names) == len(set(names)), "student names must be unique"
	
	# Extract the choice rank integers from the choice column headers
	number_re = re.compile(r"\A[^\d]*(\d+)[^\d]*\Z")
	n_choices = len(choice_matches)
	ranks = [int(number_re.match(col).group(1)) for col in choice_matches]
	
	# Check that all of the choices are ranked from 1 through n
	assert set(ranks) == set(range(1, n_choices + 1)), "choice rank failure"
	
	# Zip the choice columns together in descending order of preference
	choice_columns = list()
	for rank in range(1, n_choices + 1):
		col = choice_matches[ranks.index(rank)]
		choice_columns.append(df[col].tolist())
	choices_rows = zip(*choice_columns)
	
	# Make the list of options into a set for convenience reasons
	options_set = set(options_list)
	
	# Assemble the list of student objects that will be returned
	students = list()
	for name, hp, choices in zip(names, hps, choices_rows):
		
		# Interpret the high priority marks in the spreadsheet
		if hp in {'yes', 'y', '1', 1}:
			hp_TF = True
		elif hp in {'no', 'n', '0', 0}:
			hp_TF = False
		else:
			raise ValueError("unknown student high priority: {!r}".format(hp))
		
		# Make sure that the student's choices make sense
		choices_set = set(choices)
		assert len(choices_set) == n_choices, "ranked choices must be unique"
		assert choices_set.issubset(options_set), \
			"invalid student choices: {!r}".format(choices)
		
		# Construct student object and append to list
		student = Student(name, hp_TF, choices)
		students.append(student)
	
	# Return the list that we've been working towards this whole time
	return students, n_choices

def recursive_assignment_algorithm(match, students, options, n_choices,
	min_per_option, max_per_option, stage=1):
	""""""
	
	# If there are no student choices remaining, then trigger the base case
	if stage > n_choices:
		return assignment_algorithm_base_case(match, students, options,
			n_choices, min_per_option, max_per_option)
	
	# Otherwise, assign every unassigned student to their "stage-th" choice
	assigned_students = list()
	for student in students:
		if not match.is_matched(student.get_name()):
			match.assign(student.get_name(), student.get_choice(stage))
			assigned_students.append(student.get_name())
	
	# Find every option in the match that is now overfilled with students
	overfilled = match.list_overfilled_options(max_per_option)
	
	# For each overfilled option, use an iterable to generate all the ways that
	# students could be kicked out of the group to reduce it to the needed size
	trim_iterables = list()
	for option in overfilled:
		trim_iterables.append(match.make_trim_iterable(option, max_per_option))
	
	# Combine the iterables together into one big Cartesian product iterable
	# that hopefully isn't actually very big
	if len(trim_iterables) > 0:
		trim_product = it.product(*trim_iterables)
	else:
		trim_product = it.repeat(tuple(), n=1)  # Case with no overfull groups
	
	# Initialize variables to store the best matching and its associated score
	best_match, best_score = None, None
	
	# Iterate over all the trimming options and try out each one of them
	for trim in trim_product:
		
		# Use the trimming option to remove pairings from the match object
		# Save all the removed pairings so we can restore them later
		saved_pairs = list()
		for group in trim:
			for student in group:
				saved_pairs.append((student, match.get_match(student)))
				match.erase(student)
		
		# Recurse this same function to the next stage of choices
		# Lock any work we've done so the other stages can't mess with it
		locked_students = match.lock_all_matched()
		new_match, new_score = recursive_assignment_algorithm(match, students,
			options, n_choices, min_per_option, max_per_option, stage + 1)
		match.unlock_many(locked_students)
		
		# Compare the returned match from the recursion, save it if warranted
		if best_score is None or new_score > best_score:
			best_match = new_match
			best_score = new_score
		
		# Restore all the pairings that were removed from the match object
		match.assign_pairs(saved_pairs)
	
	# Clean up any assignments we made here before returning
	match.erase_many(assigned_students)
	
	# Return the best we've found so far to the previous layer of recursion
	return best_match, best_score

def assignment_algorithm_base_case(match, students, options, n_choices,
	min_per_option, max_per_option):
	""""""
	
	# Determine how many unhappy students there are in this matching
	n_unhappy = match.get_n_unmatched()
	
	# Identify any unfilled spaces that need to be filled to finish the match
	underfilled = match.list_underfilled_options(min_per_option)
	
	# Create even more unhappy students to fill the empty spaces if necessary
	if n_unhappy < len(underfilled):
		unhappy_queue = find_more_unhappy_students(match, students, options,
			n_choices, min_per_option, max_per_option)
		for i in range(len(underfilled) - n_unhappy):
			match.unlock(unhappy_queue[i])
			unhappy_queue[i] = (unhappy_queue[i],
				match.get_match(unhappy_queue[i]))
			match.erase(unhappy_queue[i][0])
	
	# Assign all the unhappy students to the spaces that need filling
	unhappy = match.list_unmatched_students()
	random.shuffle(unhappy)
	for i, option in enumerate(underfilled):
		match.assign(unhappy[i], option)
	
	# Excess unhappy students can just be randomly assigned to available spots
	if len(unhappy) > len(underfilled):
		empty_spots = match.list_empty_spots(min_per_option, max_per_option)
		random.shuffle(empty_spots)
		for i in range(len(underfilled), len(unhappy)):
			j = i - len(underfilled)
			match.assign(unhappy[i], empty_spots[j])
	
	# Score the resulting assignment of students
	score = score_assignment(match, students, options, n_choices,
		min_per_option, max_per_option)
	
	# Reduce the assignment of students to a list of pairs for later
	pairs = match.reduce_to_pairs()
	
	# Remove all of the assignments given to the unhappy students
	match.erase_many(unhappy)
	
	# Restore any unhappy students that needed to be created to fill spots
	if n_unhappy < len(underfilled):
		for i in range(len(underfilled) - n_unhappy):
			match.assign(unhappy_queue[i][0], unhappy_queue[i][1])
			match.lock(unhappy_queue[i][0])
	
	# Return the assignment of students (as a list of pairs) and its score
	return pairs, score

def find_more_unhappy_students(match, students, options, n_choices,
	min_per_option, max_per_option):
	""""""
	
	happiness = dict()
	priority = dict()
	for student in students:
		assigned = match.get_match(student.get_name())
		priority[student.get_name()] = int(student.is_high_priority())
		happiness[student.get_name()] = 0
		for i in range(1, n_choices + 1):
			if student.get_choice(i) == assigned:
				happiness[student.get_name()] = n_choices - i + 1
				break
	
	tiers = dict()
	for option in options:
		option_students = match.list_students_by_option(option)
		random.shuffle(option_students)
		option_students.sort(key=lambda x: happiness[x])
		option_students.sort(key=lambda x: priority[x], reverse=True)
		for i in range(len(option_students)):
			tiers[option_students[i]] = i + 1
	
	queue = [student for student in happiness.keys() if happiness[student] > 0]
	random.shuffle(queue)
	queue.sort(key=lambda x: happiness[x], reverse=True)
	queue.sort(key=lambda x: tiers[x], reverse=True)
	
	return queue

def score_assignment(match, students, options, n_choices, min_per_option,
	max_per_option):
	"""Score the optimality of a particular match based on number of happy
	students, number of 1st choices, 2nd choices, ..., high priority 1st
	choices, high priority 2nd choices, ...
	"""
	
	score = [0] + [0] * (2 * n_choices)
	
	for student in students:
		assigned = match.get_match(student.get_name())
		for i in range(1, n_choices + 1):
			if student.get_choice(i) == assigned:
				score[0] += 1
				score[i] += 1
				if student.is_high_priority():
					score[n_choices + i] += 1
				break
	
	return tuple(score)

# CLASSES
###########

class Student:
	"""Simple data class representing a student. A student has a name, a high
	priority flag, and a tuple listing their project choices.
	"""
	
	def __init__(self, name, high_priority, choices):
		"""Create a new student object. Name can be a string or sequence of
		strings, high_priority is a boolean flag, and choices is a sequence of
		unique strings from the available project options.
		"""
		
		# Handle either permissible type for the name argument
		if type(name) == type(""):
			self.name = str(name)
		else:
			self.name = tuple(str(part) for part in name)
		
		# Save the other two arguments, ensuring they have the correct types
		self.high_priority = bool(high_priority)
		self.choices = tuple(str(choice) for choice in choices)
	
	def n_choices(self):
		"""Return the number of top choices that this student has."""
		
		pass
		#return len(self.choices)
	
	def get_name(self):
		"""Return the student's name string or name tuple."""
		
		return self.name
	
	def get_choice(self, rank):
		"""Return the student's nth ranked choice (use one-based indexing)."""
		
		return self.choices[rank - 1]
	
	def is_high_priority(self):
		"""Return whether the student is flagged as high priority."""
		
		return self.high_priority

class Matching:
	"""Class representing a mutable matching between students and options that
	the algorithm can tinker with as it works."""
	
	def __init__(self, students, options):
		"""Given a list of student objects and a list of options, set up two
		inner dict objects that will drive a new matching instance, along with
		other needed internal machinery.
		"""
		
		# Set up the dict organized by student name
		self.by_student = dict()
		for student in students:
			self.by_student[student.get_name()] = None
		assert len(self.by_student) == len(students)
		
		# Set up the dict organized by option
		self.by_option = dict()
		for option in options:
			self.by_option[option] = set()
		assert len(self.by_option) == len(options)
		
		# Set up the dict to keep track of whether students are "locked"
		# Locked students cannot have their match changed
		self.student_locked = dict()
		for student in self.by_student.keys():
			self.student_locked[student] = False
	
	def assign(self, student, option):
		"""Match the named student with the named option. If the student is
		already matched, raise an error."""
		
		assert not self.is_matched(student)
		assert not self.is_locked(student)
		self.by_option[option].add(student)
		self.by_student[student] = option
	
	def get_match(self, student):
		"""Return the option matched to the given student, if any."""
		
		return self.by_student[student]
	
	def erase(self, student):
		"""Unmatch the named student from whatever option they are matched to.
		Raise an error if the student is already unmatched.
		"""
		
		assert self.is_matched(student)
		assert not self.is_locked(student)
		option = self.by_student[student]
		self.by_option[option].remove(student)
		self.by_student[student] = None
	
	def lock(self, student):
		"""Lock the named student, making their match immutable for now."""
		
		assert not self.is_locked(student)
		self.student_locked[student] = True
	
	def unlock(self, student):
		"""Unlock the named student, making their match mutable again."""
		
		assert self.is_locked(student)
		self.student_locked[student] = False
	
	def is_locked(self, student):
		"""Return whether the named student is currently locked."""
		
		return self.student_locked[student]
	
	def is_matched(self, student):
		"""Return whether the student named has been matched to an option."""
		
		return self.by_student[student] is not None
	
	def get_n_unmatched(self):
		"""Return the number of students who are not currently matched."""
		
		total = 0
		for student in self.by_student.keys():
			if not self.is_matched(student):
				total += 1
		return total
	
	def list_unmatched_students(self):
		"""Return a list of students who are not matched."""
		
		unmatched = list()
		for student in self.by_student.keys():
			if not self.is_matched(student):
				unmatched.append(student)
		return unmatched
	
	def reduce_to_pairs(self):
		"""Return a new list of student-option tuples summarizing the matching
		stored in this instance.
		"""
		
		pairs = list()
		for student in self.by_student.keys():
			assert self.is_matched(student)
			pairs.append((student, self.by_student[student]))
		return pairs
	
	def assign_pairs(self, student_option_pairs):
		"""Add several pairs to the matching. The input should be a sequence of
		student-option pairs, all of which will be added to the match."""
		
		for student, option in student_option_pairs:
			self.assign(student, option)
	
	def erase_many(self, students):
		"""Given a sequence of student names, unmatch all of them."""
		
		for student in students:
			self.erase(student)
	
	def erase_all(self):
		"""Unmatch every matched student."""
		
		for student in self.by_student.keys():
			if self.is_matched(student):
				self.erase(student)
	
	def lock_all_matched(self):
		"""Lock every student who is currently matched and unlocked. Return a
		list of all the students who were locked by this call.
		"""
		
		were_locked = list()
		for student in self.by_student.keys():
			if self.is_matched(student) and not self.is_locked(student):
				self.lock(student)
				were_locked.append(student)
		return were_locked
	
	def unlock_many(self, students):
		"""Unlock every named student on the given list."""
		
		for student in students:
			self.unlock(student)
	
	def list_overfilled_options(self, threshold):
		"""Return a list of every option in the match which has more than
		threshold number of students matched to it.
		"""
		
		overfilled = list()
		for option in self.by_option.keys():
			if len(self.by_option[option]) > threshold:
				overfilled.append(option)
		return overfilled
	
	def make_trim_iterable(self, option, threshold):
		"""Return an iterator over every possible combination of unlocked
		students who can be removed from their matches with the given option in
		order to bring the option down to the provided threshold number of
		matched students.
		"""
		
		# Make sure it actually is overfilled first
		n_assigned = len(self.by_option[option])
		assert n_assigned > threshold
		
		removable = list()
		for student in self.by_option[option]:
			if not self.is_locked(student):
				removable.append(student)
		
		return it.combinations(removable, n_assigned - threshold)
	
	def list_underfilled_options(self, threshold):
		"""Return a list of every option in the match which has fewer than
		threshold number of students matched to it. An option will appear once
		in the list if it requires one student to reach the threshold, twice if
		it requires two students, and so on."""
		
		underfilled = list()
		for option in self.by_option.keys():
			if len(self.by_option[option]) < threshold:
				for i in range(threshold - len(self.by_option[option])):
					underfilled.append(option)
		return underfilled
	
	def list_empty_spots(self, low_threshold, high_threshold):
		"""Return a list of each option with at least low_threshold matches,
		but fewer than high_threshold matches. An option appears once in the
		list if it has high_theshold - 1 matches, appears twice if it has
		high_theshold - 2 matches, and so on."""
		
		empty_spots = list()
		for option in self.by_option.keys():
			if low_threshold <= len(self.by_option[option]) < high_threshold:
				for i in range(high_threshold - len(self.by_option[option])):
					empty_spots.append(option)
		return empty_spots
	
	def list_students_for_option(self, option):
		"""Given one option, return a list of all student names matched to that
		option.
		"""
		
		return list(self.by_option[option])
	
	def pretty_print_in_order(self, options_order, students, n_choices):
		"""Pretty print the matching by option category, adhering to the order
		set by the option order list. Also document students' choices.
		"""
		
		got_choice = dict()
		high_priority = dict()
		for student in students:
			assigned = self.get_match(student.get_name())
			high_priority[student.get_name()] = student.is_high_priority()
			got_choice[student.get_name()] = None
			for i in range(1, n_choices + 1):
				if student.get_choice(i) == assigned:
					got_choice[student.get_name()] = i
					break
		
		for option in options_order:
			print('  ' + option)
			student_list = self.list_students_for_option(option)
			student_list.sort()
			for student in student_list:
				ch_str = 'choice #{:d}'.format(got_choice[student]) if \
					got_choice[student] is not None else 'unhappy'
				hp_str = ', high priority' if high_priority[student] else ''
				print('    {!s} ({:s}{:s})'.format(student, ch_str, hp_str))

# CALL TO MAIN
################

main()


