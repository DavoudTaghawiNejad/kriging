#numpy.indices usabel instead of itertools
import itertools
import numpy as np


def lowest_values(n, ncparm, chaines, predict, simulations):
    """ uses predict to predict the outcome of all parameters in chains, return the 20 most promising values
    """
    cdef int negative_value = 0
    cdef float nth = float("Inf")
    cdef float y
    candidate_ys = np.ones(n, float) * float("Inf")
    candidate_xs = np.ones((n, ncparm), float) * float("Inf")
    for x in itertools.product(*chaines):
        x = np.array(x)
        if simulations.is_new(x):
            y = predict(x)
            if 0 > y:
                negative_value += 1
            elif y <= nth:
                i = np.argmax(candidate_ys)
                candidate_ys[i] = y
                candidate_xs[i] = x
                nth = y
    return candidate_xs[np.isfinite(candidate_ys)], candidate_ys[np.isfinite(candidate_ys)], negative_value