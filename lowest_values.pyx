#numpy.indices usabel instead of itertools
import itertools
import numpy as np
from hypercube import centered_latin_hypercube_A

def lowest_values(n, ncparm, predict, simulations, InputSet, best_input, schlinge, best_metric):
    """ uses predict to predict the outcome of all parameters in chains, return the 20 most promising values
    """
    cdef int negative_value = 0
    cdef float nth = best_metric
    cdef float y
    candidate_ys = np.ones(n, float) * float("Inf")
    candidate_xs = np.ones((n, ncparm), float) * float("Inf")
    for _ in range(100):
        for x in centered_latin_hypercube_A(best_input, schlinge, InputSet.lb, InputSet.ub, ncparm * 10):
            if simulations.is_new(x):
                y = predict(x)
                if y < 0:
                    negative_value += 1
                elif y <= nth:
                    i = np.argmax(candidate_ys)
                    candidate_ys[i] = y
                    candidate_xs[i] = x
                    nth = min(np.max(candidate_ys), best_metric)
    return candidate_xs[np.isfinite(candidate_ys)], candidate_ys[np.isfinite(candidate_ys)], negative_value