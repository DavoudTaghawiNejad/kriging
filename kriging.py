from __future__ import division
from simulationset import SimulationSet
from inputset import InputSet
from split import split
from keypress import Keypress
from remotesaudifirms import RemoteSaudiFirms
from kriging_model import kriger
import numpy as np
from copy import deepcopy
from hypercube import centered_latin_hypercube_I
from sklearn import gaussian_process
import json
import dataset
from hashlib import sha224
from collections import defaultdict, MutableMapping
import logging


logger = logging.getLogger('kriging')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('kriging.log')
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter_stream = logging.Formatter('%(asctime)s\t%(message)s', datefmt='%H:%M:%S')
formatter_file = logging.Formatter('%(asctime)s\t%(message)s', datefmt='%m-%d %H:%M:%S')
fh.setFormatter(formatter_file)
ch.setFormatter(formatter_stream)
logger.addHandler(fh)
logger.addHandler(ch)


class Kriging:
    def __init__(self, parameters, target, repetitions, db_name):
        print("v. 0.1")
        fixed_parameters, lower_limits, upper_limits, dtypes = split(parameters)
        SimulationSet.setup(dtypes, target)
        InputSet.setup(lower_limits, upper_limits, dtypes, fixed_parameters)
        self.repetitions = repetitions
        self.remote_saudifirms = RemoteSaudiFirms(task=5007, result=5008, kill=5009)
        self.local_saudifirms = RemoteSaudiFirms(task=5567, result=5568, kill=5569)

        self._db = dataset.connect("sqlite:///%s.sqlite3" % db_name)
        parameters = json.dumps(fixed_parameters)
        hash = sha224(parameters).hexdigest()[:7]
        overview = self._db['overview']
        overview.insert({'hash': hash, 'json_string': parameters})
        self.db = self._db[hash]
        self.db_name = db_name

    def initialize(self, initial_runs):
        self.simulations = SimulationSet()
        for row in self.db:
            try:
                input = json.loads(row['input'])
                output = json.loads(row['output'])
            except TypeError:
                logger.info(row['output'])
            self.simulations.insert(input, output)
        logger.info("loaded %i" % len(self.simulations))

        if len(self.simulations) < initial_runs:
            middle_point = InputSet.middle_point()
            simulation_candidates = centered_latin_hypercube_I(middle_point, np.ones_like(middle_point), InputSet.lb, InputSet.ub, initial_runs)
            self.run_add(simulation_candidates)

    def print_dict(self):
        inputset = InputSet()
        inputset.insert(InputSet.middle_point())
        logger.info(dict(inputset[0]))

    def kriging(self, batch_size=28, success=0.01, schlinge_start=2.0, schlinge_change=0.05):
        INPUT, RESULT = 0, 1
        log_values = self._db['log_values']
        gp = gaussian_process.GaussianProcess(
            nugget=2.2204460492503131e-13, storage_mode='light'
        )
        get_key = Keypress()
        diameter = (InputSet.ub - InputSet.lb) / 2
        initial_distance = InputSet.ub - InputSet.lb
        schlinge = np.empty_like(InputSet.ub)
        schlinge.fill(schlinge_start)
        stats_innovation_kriging = 0
        stats_innovation_simulation = 0
        stats_iterations = 0
        while True:
            logger.info("")
            logger.info("iteration: %i total simulations: %i" % (stats_iterations, len(self.simulations)))
            old_best = self.simulations.best()
            kriging_candidates = kriger(self.simulations, InputSet, schlinge, batch_size, gp)
            kriging_candidates = self.run_add(kriging_candidates)
            kriging_candidate_is_better, kriging_candidate, num_better = self.candidates_better(old_best, kriging_candidates)
            if kriging_candidate_is_better:
                logger.info("+k+ %s (%s) better: %i" % (kriging_candidate[1], old_best[1], num_better))
                stats_innovation_kriging += 1
                candidate = kriging_candidate
            else:
                logger.info("-k- %s" % kriging_candidate[1])
                candidate = old_best

            logger.info("***    hypercube:")
            simulation_candidates = centered_latin_hypercube_I(candidate[0], schlinge, InputSet.lb, InputSet.ub, batch_size)
            simulation_candidates = self.run_add(simulation_candidates)
            simulation_candidate_is_better, simulation_candidate, num_better = self.candidates_better(candidate, simulation_candidates)
            if simulation_candidate_is_better:
                logger.info("+s+ %s (%s) better: %i" % (simulation_candidate[1], candidate[1], num_better))
                stats_innovation_simulation += 1
                candidate = simulation_candidate
            else:
                logger.info("-s- %s" % simulation_candidate[1])

            if not kriging_candidate_is_better and not simulation_candidate_is_better:
                schlinge -= schlinge_change
                schlinge = np.maximum(schlinge, np.absolute(candidate[0] - old_best[0]) / diameter)
                #schlinge = np.minimum(schlinge, [2] * len(schlinge))
                schlinge[schlinge < 0] = 0
                schlinge = np.maximum(np.absolute(self.simulations.best()[0] - old_best[0]) / initial_distance, schlinge)

            logger.info("    simul:    %10.8f (%10.8f)" % (candidate[1], (old_best[1] - candidate[1])))
            try:
                score = gp.score(simulation_candidates.inputs, simulation_candidates.metrics)
                logger.info("    score: %4.2g" % score)
            except ValueError:
                if len(simulation_candidates) > 1:
                    raise
            logger.info("    schlinge average %f" % np.mean(schlinge))

            #TODO pred = np.array([gp.predict(candidate[0]) for candidate in simulation_candidates], dtype=np.float64)
            #TODO logger.info("    mean prediction accuracy %f" % np.mean(np.absolute((simulation_candidates[0] - pred) / simulation_candidates[1])))
            if self.simulations.best()[RESULT] < success:
                self.save_result()
                return self.simulations.best_dict(), self.test(self.simulations.best_dict(), 20)
            if (schlinge <= 0.001).all():
                logger.info("\n\n\ni  ----------- SCHLINGE RELEASED = 2 ---------------\n\n\n")
                schlinge.fill(2)
            key_pressed = get_key()
            if key_pressed == 'c' or key_pressed == 'i':
                logger.info("Schlinge %s" % str(schlinge))
                logger.info("innovation_simulation: %i" % stats_innovation_simulation)
                logger.info("innovation_kriging:    %i" % stats_innovation_kriging)
                logger.info("iterations             %i" % stats_iterations)
                logger.info("unique simulations     %i" % len(self.simulations))
                logger.info(self.simulations.best_dict())
                if key_pressed == 'c':
                    self.save_result()
                    return self.simulations.best_dict(), self.test(self.simulations.best_dict(), 20)
            if key_pressed == 't':
                logger.info(json.dumps(self.test(self.simulations.best_dict(), 20), indent=20))
            log_data = {
                'iteration': stats_iterations,
                'average_kriging': float(kriging_candidates.average()),
                'best_kriging':  float(kriging_candidates.best()[RESULT]),
                'average_current_simulation': float(simulation_candidates.average()),
                'best_simulation_candidate': float(simulation_candidates.best()[RESULT]),
                'total_average': float(self.simulations.average()),
                'best': float(self.simulations.best()[RESULT])
            }
            log_data.update(self.test(self.simulations.best_dict(), 20))
            logger.info(self.test(self.simulations.best_dict(), 20))
            log_values.upsert(log_data, ['iteration'])
            self.run_local(self.simulations.best_dict(), 1)
            stats_iterations += 1

    def save_result(self):
        with open('%s.json' % self.db_name, 'wb') as fp:
            json.dump(self.simulations.best_dict(), fp)

    def candidates_better(self, old_best, candidates):
        best = deepcopy(old_best)
        num_better = 0
        for input, metric in candidates:
            if self.simulations.is_new(input):
                if metric < best[1]:
                    best = input
                if metric < old_best[1]:
                    num_better += 1
        if num_better == 0:
            return False, old_best, num_better
        else:
            return True, best, num_better


    def run_add(self, input):
        """ runs one input; returns simulation """
        raw_output = self.remote_saudifirms.run_D2D(input, self.repetitions)
        new_simulations = SimulationSet()
        for row in raw_output:
            input = row['parameters']
            output = row['result']
            new = self.simulations.insert(input, output)
            new_simulations.insert(input, output)
            if new:
                self.db.insert({'input': json.dumps(input), 'output': json.dumps(output)})
        return new_simulations

    def run_local(self, input, repetitions=1):
        """ runs one input; returns simulation """
        print(" (local)")
        self.local_saudifirms.vent([input])


    def run_best(self):
        self.run_local(self.simulations.best_dict())

    def run_input(self, weight=0.5):
        self.run_local(InputSet.weight_point(weight))


    def test(self, input, repetitions):
        """ runs one input; returns simulation """
        raw_output = self.remote_saudifirms.run_D2D([input], repetitions)
        for row in raw_output:
            input = row['parameters']
            output = row['result']
            self.simulations.insert(input, output)
        output = defaultdict(lambda: defaultdict(int))

        for row in raw_output:
            for category, key in SimulationSet.output_keys:
                output[category][key] += (1 / repetitions) * row['result'][category][key]
        return flatten(output, '')


def flatten(d, parent_key=''):
    items = []
    for k, v in d.items():
        new_key = parent_key + '_' + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)