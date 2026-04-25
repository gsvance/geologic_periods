#!/usr/bin/env python3
# Test the model using my *original* colors example from years ago

# Created 11 Mar 2023 by Greg Vance


from scoring_model import solve_geologic_periods_problem, classic_scoring


with open('old_stuff/Colors.txt', 'r', encoding='ascii') as colors:
    topics = colors.read().strip().split()

students, high_priority, choices = [], [], []
with open('old_stuff/FakeChoices.csv', 'r', encoding='ascii') as csv:
    csv.readline()
    for line in csv:
        name, yesno, choice1, choice2, choice3 = line.strip().split(',')
        students.append(name)
        high_priority.append({'yes': True, 'no': False}[yesno])
        choices.append([choice1, choice2, choice3])

limits = (1, 2)

report = solve_geologic_periods_problem(
    students, topics, choices,
    high_priority_flags=high_priority,
    scoring_system=classic_scoring,
    limits_per_topic=limits,
    shuffle_students=True,
    solver_output=True,
)

print(report)
