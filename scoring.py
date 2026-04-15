"""Scoring system definitions for use in the geologic periods problem

The solver needs to optimize for something, and the scoring system is what it
uses to evaluate different possible matchings of students to topics. The
scoring system takes in the sets of model input data, then uses those data to
construct an array of scoring weights for each possible student-topic pair.

Created 7 Mar 2023 by Greg Vance
"""

import numpy as np

from mytypes import Array
from organization import Sets


def classic_scoring(sets: Sets) -> Array:
    """Compute weights that implement the classic "tuple scoring" method.

    The tuple scoring method prioritizes "happy" students, then students who
    get their first choice, then second choice, and so on. Choices of high
    priority students are prioritized over other students whenever all else is
    equal. These factors are optimized for in exactly this order.
    """
    # Note for Future Greg:
    # In this function, I use the built-in list.insert() method several times
    # to append values to the starts of Python list objects. I am aware that
    # this is inefficient, but the lists are ultimately quite short and it
    # makes for much more readable code, so I'm chosing to do it anyway.

    # 1) Giving a high-priority student their last choice is worth 1 point.
    scores_hp = [1]

    # 2) Giving a high-priority student their second-to-last choice is worth
    #    more points. In fact, it should always be true that the next step up
    #    is worth more than the previous step could ever yield. Since the most
    #    points you can get for 1) is n_hp, we just multiply by n_hp at each
    #    stage and add 1 to exceed that maximum value.
    while len(scores_hp) < sets.n_c:
        previous_step = scores_hp[0]
        next_step = previous_step * sets.n_hp + 1
        scores_hp.insert(0, next_step)

    # 3) At this point, scores_hp[c] contains the point value of giving a high
    #    priority student their choice number c. Now, for the next step up, we
    #    want giving *any* student (including high priority students) thier
    #    last choice to be worth even more points than giving a high priority
    #    student their 1st choice on its own. Do the same trick of multiplying
    #    by n_hp and adding 1 again.
    scores_any = [scores_hp[0] * sets.n_hp + 1]

    # 4) Now we play the same game stepping up through the point values for
    #    giving *any* student their choice c in the same way as 2) went. The
    #    difference is that now we can get n_s times the previous step's point
    #    value, so we have to multiply by n_s and add 1 to exceed it.
    while len(scores_any) < sets.n_c:
        previous_step = scores_any[0]
        next_step = previous_step * sets.n_s + 1
        scores_any.insert(0, next_step)

    # 5) The entry in scores_any[c] now contains the point value of giving
    #    *any* student their choice number c. For the final step, we use the
    #    trick of multiplying by n_s and adding 1 one last time to get the
    #    point value of creating a "happy" student, that is, *any* student who
    #    got *any* one of their stated choices.
    score_happy = scores_any[0] * sets.n_s + 1

    # The classic scoring system is thusly created by steps 1) through 5)
    # above. The plan here is to motivate the solver to first maximize the
    # number of happy students, then the total number of students getting their
    # first choice, then their second choice, and so on. Then we want to
    # maximize the number of high priority students getting their first choice,
    # second choice, and so on. We want to fully optimize for each criterion in
    # that order before moving on to the next criterion. This is why each step
    # *must* be worth more ponits than the next lowest step could ever yield.
    # However, we don't want to make the point values any *larger* than they
    # absolutely need to be, because they grow exponentially and the float64s
    # used by the solver only have so many digits of precision...
    weights = np.zeros((sets.n_s, sets.n_t), dtype='int64')
    for s in sets.s:
        for t in sets.t:
            weight_sum = 0
            for c in sets.c:
                pref = sets.pref[s, t, c]
                weight_sum += pref * score_happy
                weight_sum += pref * scores_any[c]
                weight_sum += pref * sets.hp[s] * scores_hp[c]
            weights[s, t] = weight_sum

    # Do a quick test to try and detect if the classic scoring system is
    # breaking down. This could conceivably happen if n_s, n_c, and n_hp are
    # all just much too big for the strategy being used here.
    int_info = np.iinfo(weights.dtype)
    nonzero = (weights != 0)
    weight_min = np.amin(weights, initial=int_info.max, where=nonzero)
    weight_max = np.amax(weights, initial=int_info.min, where=nonzero)
    float_min, float_max = np.float64(weight_min), np.float64(weight_max)
    if not (float_max + float_min > float_max):
        raise RuntimeError("classic scoring system broke down")

    return weights
