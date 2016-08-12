from __future__ import division
from lowest_values import lowest_values
from predictedset import PredictedSet
from time import time
import logging
from scipy import optimize

logger = logging.getLogger('kriging.kriger')


def kriger(simulations, InputSet, schlinge, num_return_best, old_best_metric, gp):
    """ fits a gaussian model, returns the most promising values, which includes
    candidates choosen by a latin hypercube as will as the minimum of the gaussian
    model choosen by basinhopping """
    print('kriger fit'),
    try:
        gp.fit(simulations.inputs, simulations.metrics)
    except MemoryError:
        print("Memory Error, forgetting first half")
        simulations.half()
        gp.fit(simulations.inputs, simulations.metrics)
    best_input, best_result = simulations.best()
    t = time()
    print('find lowest'),
    inputs, metrics, negative_values = lowest_values(num_return_best - 1, len(InputSet.lb), gp.predict, simulations, InputSet, best_input, schlinge, old_best_metric, delete_negatives=False)
    print("time: %f" % (time() - t))
    candidates = PredictedSet()
    for inputs, metrics in zip(inputs, metrics):
        candidates.insert(inputs, metrics)
    bnds = zip(InputSet.lb, InputSet.ub)
    minimizer_kwargs = {"method": "L-BFGS-B", "bounds": bnds, "tol": 1e0}
    res = optimize.basinhopping(gp.predict, best_input, minimizer_kwargs=minimizer_kwargs, niter=10, T=0.01)
    print res.message
    if 0 <= res.fun <= old_best_metric:
        candidates.insert(res.x, res.fun)
    logger.info("    candidates better: %i" % len(candidates))
    logger.info("    candidates < 0: %i" % negative_values)
    return candidates

