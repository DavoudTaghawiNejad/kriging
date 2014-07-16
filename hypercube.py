from __future__ import division
from pyDOE import lhs
from inputset import InputSet
import numpy as np
import math


def _centered_latin_hypercube(center, schlinge, lb, ub, samples):
    samples = max(samples, len(center))
    design = lhs(len(lb), samples)
    diameter = (ub - lb) / 2
    _lb = center - diameter * schlinge
    _ub = center + diameter * schlinge
    lb = np.maximum(lb, _lb)
    ub = np.minimum(ub, _ub)
    return design * (ub - lb) + lb


def centered_latin_hypercube_A(center, schlinge, lb, ub, samples):
    samples = max(samples, len(center))
    fields = np.logical_and(schlinge > .1, ub > lb)
    t_center = center[fields]
    t_schlinge = schlinge[fields]
    t_lb = lb[fields]
    t_ub = ub[fields]
    t_samples = int(math.ceil(samples / len(fields) * sum(fields)))
    lh = _centered_latin_hypercube(t_center, t_schlinge, t_lb, t_ub, t_samples)
    ret_lh = np.empty([t_samples, len(center)], dtype=np.float64)
    j = 0
    for i in range(len(center)):
        if fields[i]:
            ret_lh[:, i] = lh[:, j]
            j += 1
        else:
            ret_lh[:, i] = np.array(center[i] * t_samples)  # ret_lh[:, i].fill(means[i])

    return ret_lh

def centered_latin_hypercube_I(center, schlinge, lb, ub, samples):
    ret_lh = _centered_latin_hypercube(center, schlinge, lb, ub, samples)
    candidates = InputSet()
    for input in ret_lh:
        candidates.insert(input)
    return candidates
