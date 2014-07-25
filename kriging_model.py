from __future__ import division
from lowest_values import lowest_values
from predictedset import PredictedSet
from time import time
import logging

logger = logging.getLogger('kriging.kriger')


def kriger(simulations, InputSet, schlinge, num_return_best, old_best_metric, gp):
    gp.fit(simulations.inputs, simulations.metrics)
    best_input, best_result = simulations.best()
    t = time()
    inputs, metrics, negative_values = lowest_values(num_return_best, len(InputSet.lb), gp.predict, simulations, InputSet, best_input, schlinge, old_best_metric)
    logger.info("    time: %f" % (time() - t))
    logger.info("    candidates better: %i" % len(inputs))
    logger.info("    candidates < 0: %i" % negative_values)
    candidates = PredictedSet()
    for inputs, metrics in zip(inputs, metrics):
        candidates.insert(inputs, metrics)
    return candidates

