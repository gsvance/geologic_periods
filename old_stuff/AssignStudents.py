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
# REPEATED RANDOM SERIAL DICTATORSHIP!!!
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

# Last modified 16 Dec 2020 by Greg Vance

# SETUP CODE AND CONSTANTS
##########################

import json  # For pretty printing of dict objects
#import numpy as np
#from scipy.optimize import linear_sum_assignment
#import pandas  # For reading an XLSX file if needed
import random

import AlgorithmUtilities as au

# File name strings for input/output files
OPTIONS_FILE = "Colors.txt"  # List of geologic periods
CHOICES_FILE = "FakeChoices.csv"  # Spreadsheet of student choices
OUTPUT_FILE = "Assignments.txt"  # Final assignments for students

# Parameters to test and constant conditions to enforce
N_OPTIONS = 12  # Number of geologic periods to pick from
N_CHOICES = 3  # Number of ranked picks each student gets
MIN_PER_OPTION = 1  # Minimum number of students assigned per geologic period
MAX_PER_OPTION = 2  # Maximum number of students assigned per geologic period

# READ DATA FROM FILES
######################

# Read the list of options (geologic periods) from file
with open(OPTIONS_FILE, "r") as options_f:
	options = [line.strip() for line in options_f if line.strip() != ""]

# Sanity checks on the options data
assert len(options) == len(set(options))  # Make sure options are all unique
assert len(options) == N_OPTIONS  # Check for the right number of options

# Read the student choices (and high priority status) info from file
choices, high_priority = dict(), dict()
column_headers = ["Student Name", "High Priority"]
column_headers.extend(["Choice {:d}".format(n+1) for n in range(N_CHOICES)])
n_columns = len(column_headers)
header_line = ','.join(column_headers) + '\n'
with open(CHOICES_FILE, 'r') as choices_f:
	assert choices_f.readline() == header_line
	for line in choices_f:
		row = line.strip()
		if not row:
			continue  # Skip any lines that are blank
		columns = row.split(',')
		assert len(columns) == n_columns
		name = columns[0]
		assert name not in high_priority  # Make sure names are unique
		high_priority[name] = {"yes": True, "no": False}[columns[1]]
		assert name not in choices  # Make sure names are unique
		choices[name] = list()
		for my_choice in columns[2:]:
			assert my_choice in options
			assert my_choice not in choices[name]  # Must pick distinct choices
			choices[name].append(my_choice)
		assert len(choices[name]) == N_CHOICES

# Sanity checks on the student choices data
n_students = len(choices)
assert len(high_priority) == n_students
assert N_OPTIONS * MIN_PER_OPTION <= n_students  # Make sure matches possible
assert N_OPTIONS * MAX_PER_OPTION >= n_students  # Make sure matches possible

# STATISTICS ON THE INPUT DATA
##############################

# Record tallies of first choices and all top choices
first_choices = {key : 0 for key in options}
all_choices = {key : 0 for key in options}
for choice_list in choices.values():
	first_choices[choice_list[0]] += 1
	for my_choice in choice_list:
		all_choices[my_choice] += 1

# Print the tally dictionaries
print("First choices:", first_choices, sep='\n')
print("All top choices:", all_choices, sep='\n')

# SETUP INITIALIZATIONS FOR THE ALGORITHM
#########################################

match_iter = au.MatchingsIterator(options, choices)
#match_iter.set_min_and_max()

n_unhappy_students = 1 # calculate minimum limit

scorer = au.ScoreCalculator(choices, high_priority)

best_matches = None
best_score = None

# RUNNING THE ACTUAL ALGORITHM
##############################

while True:
	
	for match in match_iter.all_permitted_matchings(n_unhappy_students):
		score = scorer.calculate_score(match)
		if best_matches is None or score > best_score:
			best_matches = set()
			best_matches.add(match.as_tuples())
			best_score = score
		elif score == best_score:
			best_matches.add(match.as_tuples())
	
	if best_matches is None:
		n_unhappy_students += 1
	else:
		break

# REPORTING ON THE RESULTS
##########################

print(scorer.interpret_score(best_score))

'''
if type(bestmatch) is type(frozenset()):
	bestmatch = {bestmatch}

print("Found", len(bestmatch), "alternate best matchings")

for i, match in enumerate(bestmatch):
	
	print("MATCHING", i + 1)
	
	for option in options:
		print(" ", option)
		for name, assignment in match:
			if assignment == option:
				try:
					rank = choices[name].index(assignment)
					rank = "(choice #" + str(rank + 1) + ")"
				except ValueError:
					rank = "(unhappy)"
				print("   ", name, rank)
'''

# WRITING RESULTS OUT TO FILE
#############################


