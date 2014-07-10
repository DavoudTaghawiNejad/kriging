__author__ = 'taghawi'
import random
from lowest_values import lowest_values
import itertools
import numpy as np
from predictedset import PredictedSet
from time import time
import logging

logger = logging.getLogger('kriging.kriger')


def kriger(simulations, InputSet, sweep_intervals, schlinge, num_return_best, gp):
    gp.fit(simulations.inputs, simulations.metrics)
    best_input, best_result = simulations.best()
    t = time()
    inputs, metrics, negative_values = lowest_values(num_return_best, len(InputSet.lb), gp.predict, simulations, InputSet, best_input, schlinge)
    logger.info("    time: %f" % (t - time()))
    logger.info("    candidates better: %i" % len(inputs))
    logger.info("    candidates < 0: %i" % negative_values)
    candidates = PredictedSet()
    for inputs, metrics in zip(inputs, metrics):
        candidates.insert(inputs, metrics)
    if negative_values:
        logger.info("/// %i negative values" % negative_values)
    return candidates

