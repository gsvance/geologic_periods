#!/usr/bin/env python3

# Use BoyNames.txt, Girlnames.txt, and Colors.txt to generate random fake data
# In reality, we'll want real student names with geologic period preferences
# For now, just use a few common first names and a list of tweleve colors
# This data will be more than good enough to help us test the algorithm

# Last modified 29 Nov 2020 by Greg Vance

import random

# Preset values for input/output files
NAME_FILES = ["BoyNames.txt", "GirlNames.txt"]
COLOR_FILE = "Colors.txt"
OUTPUT_FILE = "FakeChoices.csv"

# Randomization parameters to use
N_STUDENTS = 22
N_CHOICES = 3
N_HIGH_PRIORITY = 2
assert N_HIGH_PRIORITY <= N_STUDENTS
random.seed(9121)  # For reproducible results

# Read in the boy and girl names that are available to choose from
all_names = set()
for file_name in NAME_FILES:
	with open(file_name, "r") as name_f:
		for line in name_f:
			cleaned = line.strip()
			if cleaned:
				all_names.add(cleaned)
all_names = list(all_names)
all_names.sort()  # Unsorted defeats the point of the random seed

# Read in the list of colors that the students can choose from
colors = set()
with open(COLOR_FILE, "r") as color_f:
	for line in color_f:
		cleaned = line.strip()
		if cleaned:
			colors.add(cleaned)
colors = list(colors)
colors.sort()  # Unsorted defeats the point of the random seed
N_COLORS = len(colors)  # Could specify above as a randomization parameter...
assert N_CHOICES <= N_COLORS

# Generate our random list of student names without replacement
names = random.sample(all_names, N_STUDENTS)
names.sort()  # Might as well alphabetize them

# Try to replicate the reality of some options being more popular than others
# We'll use a Zipf's Law distribution for the popularity of color options
zipf = [1. / (n + 1) for n in range(N_COLORS)]
norm = 1. / sum(zipf)
prob = [p * norm for p in zipf]
random.shuffle(prob)  # In-place shuffle
cumulative = [sum(prob[:i+1]) for i in range(N_COLORS)]
c_norm = 1. / cumulative[-1]
cumulative = [c * c_norm for c in cumulative]  # Just to make sure
assert cumulative[-1] == 1.0

# Write a function that uses the cumulative probabilities to select k choices
def select_choices(items, c_prob, k):
	choices = list()
	while len(choices) < k:
		r = random.random()
		i = 0
		while c_prob[i] <= r:
			i += 1
		if items[i] not in choices:
			choices.append(items[i])
	return choices

# Pick each student's top chocies from the list of available colors
# Use our popularity distribution when we do this
choices = list()
for name in names:
	values_list = select_choices(colors, cumulative, N_CHOICES)
	choices.append(values_list)

# Mark a few randomly-chosen students as high-priority
delta_n = N_STUDENTS - N_HIGH_PRIORITY
high_priority = ["yes"] * N_HIGH_PRIORITY + ["no"] * delta_n
random.shuffle(high_priority)  # In-place shuffle

# Put the data into the desired output file
with open(OUTPUT_FILE, "w") as out_f:
	headers = ["Student Name", "High Priority"]
	for n in range(N_CHOICES):
		headers.append("Choice {:d}".format(n + 1))
	header = ','.join(headers) + '\n'
	out_f.write(header)
	for i in range(N_STUDENTS):
		columns = [names[i], high_priority[i]]
		columns.extend(choices[i])
		row = ','.join(columns) +'\n'
		out_f.write(row)


