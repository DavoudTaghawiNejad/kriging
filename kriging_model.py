__author__ = 'taghawi'
import random
from lowest_values import lowest_values
import itertools
import numpy as np


def kriger(simulations, InputSet, sweep_intervals, schlinge, num_return_best, gp):
    gp.fit(simulations.inputs, simulations.metrics)
    best_input, best_result = simulations.best()
    diameter = (InputSet.ub - InputSet.lb) / 2
    assert (diameter >= 0).all(), diameter
    assert (schlinge > 0).all(), schlinge
    lb = best_input - diameter * schlinge
    ub = best_input + diameter * schlinge
    lb = InputSet.respect_bounds(lb)
    ub = InputSet.respect_bounds(ub)
    assert (ub >= InputSet.lb).all()
    assert (lb <= ub).all()
    index = range(len(lb))
    chaines = [[]] * len(lb)
    print("len chaines: %i" % len(chaines))
    print(np.array(chaines).shape)
    for i, l, u, slb, sub, d in zip(index, lb, ub, InputSet.lb, InputSet.ub, InputSet.dtypes):
        half_interval = (u - l) / sweep_intervals[i] / 2
        rnd = random.uniform(- half_interval, half_interval)
        l += rnd
        u += rnd
        chaines[i] = np.arange(l, u, (u - l) / sweep_intervals[i], dtype=d)
        if u > sub:
            chaines[i] = chaines[i][:-2]
        if l < slb:
            chaines[i] = chaines[i][1:]
    print("    brute_force iterations: chaines: %i" % (len(chaines)))
    print("    candidates for predict: %i" % len([_ for _ in itertools.product(*chaines)]))
    inputs, metrics, negative_values = lowest_values(num_return_best, len(lb), chaines, gp.predict, simulations)
    print("    candidates better: %i" % len(inputs))
    candidates = InputSet()
    for inputs, metrics in zip(inputs, metrics):
        candidates.update_a(inputs, metrics)
    if negative_values:
        print("/// %i negative values of %i" % (negative_values, (sweep_intervals - 1) ** len(lb)))
    return candidates, negative_values > 0.5 * (np.mean(sweep_intervals) - 1) ** len(lb)

