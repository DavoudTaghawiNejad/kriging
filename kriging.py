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
from collections import defaultdict, MutableMapping, OrderedDict
import logging


logger = logging.getLogger('kriging')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('kriging.log')
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter_stream = logging.Formatter('%(asctime)s %(lineno)03d\t%(message)s', datefmt='%H:%M:%S')
formatter_file = logging.Formatter('%(asctime)s\t%(message)s', datefmt='%m-%d %H:%M:%S')
fh.setFormatter(formatter_file)
ch.setFormatter(formatter_stream)
logger.addHandler(fh)
logger.addHandler(ch)

dont_transform = lambda self, x: x

class Kriging:
    def __init__(self, parameters, target, repetitions, db_name, transform=dont_transform, local_simulations=False):
        print("v. 0.3")
        fixed_parameters, lower_limits, upper_limits, dtypes = split(parameters)
        SimulationSet.setup(dtypes, target, transform)
        InputSet.setup(lower_limits, upper_limits, dtypes, fixed_parameters)
        self.repetitions = repetitions
        self.remote_saudifirms = RemoteSaudiFirms(task=5007, result=5008)
        self.local_saudifirms = RemoteSaudiFirms(task=5567, result=5568)

        self._db = dataset.connect("sqlite:///%s.sqlite3" % db_name)
        parameters = json.dumps(sorted(fixed_parameters.items()))
        hash = sha224(parameters).hexdigest()[:7]
        overview = self._db['overview']
        overview.insert({'hash': hash, 'json_string': parameters})
        self.db = self._db[hash]
        self.db_name = db_name
        self.local_simulations = local_simulations

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
            print("create simulation candidates")
            simulation_candidates = centered_latin_hypercube_I(middle_point, np.ones_like(middle_point), InputSet.lb, InputSet.ub, initial_runs)
            print("run %i simulations" % len(simulation_candidates))
            self.run_add(simulation_candidates)
        print("done loading/initializing")

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
            best_old = self.simulations.best()
            kriging_candidates = kriger(self.simulations, InputSet, schlinge, batch_size, best_old[RESULT], gp)
            kriging_candidates = self.run_add(kriging_candidates)
            best_kriging_candidate = kriging_candidates.best()
            if best_kriging_candidate[RESULT] < best_old[RESULT]:
                logger.info("+k+ %s (%s) better: %i" % (best_kriging_candidate[RESULT], best_old[RESULT], kriging_candidates.candidaties_better(best_old)))
                stats_innovation_kriging += 1
                candidate = best_kriging_candidate
                kriging_candidate_is_better = True
            else:
                logger.info("-k- (%s) %s" % (best_kriging_candidate[RESULT], best_old[RESULT]))
                candidate = best_old
                kriging_candidate_is_better = False

            logger.info("***    hypercube:")
            simulation_candidates = centered_latin_hypercube_I(candidate[0], schlinge, InputSet.lb, InputSet.ub, batch_size)
            simulation_candidates = self.run_add(simulation_candidates)
            best_simulation_candidate = simulation_candidates.best()
            if best_simulation_candidate[RESULT] < candidate[RESULT]:
                logger.info("+s+ %s (%s) better: %i" % (
                    best_simulation_candidate[1], candidate[1], simulation_candidates.candidaties_better(candidate)))
                stats_innovation_simulation += 1
                simulation_candidate_is_better = True
            else:
                logger.info("-s- (%s) %s" % (best_simulation_candidate[RESULT], candidate[RESULT]))
                simulation_candidate_is_better = False

            if not kriging_candidate_is_better and not simulation_candidate_is_better:
                self.simulations.filter(schlinge)
                schlinge = schlinge * (1 - schlinge_change)
                schlinge = np.maximum(schlinge, np.absolute(candidate[0] - best_old[0]) / diameter)
                #schlinge = np.minimum(schlinge, [2] * len(schlinge))
                schlinge[schlinge < 0] = 0
                schlinge = np.maximum(np.absolute(self.simulations.best()[0] - best_old[0]) / initial_distance, schlinge)
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
                logger.info("\n\n\ni  ----------- SCHLINGE RELEASED ---------------\n\n\n")
                schlinge.fill(schlinge_change * 5)
                schlinge_change = schlinge_change / 2
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
            log_data = {
                'iteration': stats_iterations,
                'average_kriging': float(kriging_candidates.average()),
                'best_kriging':  float(kriging_candidates.best()[RESULT]),
                'average_current_simulation': float(simulation_candidates.average()),
                'best_simulation_candidate': float(simulation_candidates.best()[RESULT]),
                'total_average': float(self.simulations.average()),
                'best': float(self.simulations.best()[RESULT])
            }
            best_output, best_complete = self.test(self.simulations.best_dict(), 20)
            log_data.update(best_complete)
            log_data.update(flatten(self.simulations.best_var_dict(), 'input'))
            log_data = OrderedDict(sorted(log_data.items()))
            logger.info("input:")
            logger.info(sorted(flatten(self.simulations.best_var_dict()).items()))
            logger.info("output:")
            logger.info(sorted(best_output.items()))
            log_values.upsert(log_data, ['iteration'])
            if self.local_simulations:
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
                self.db.insert({u'input': json.dumps(input), u'output': json.dumps(output)})
        return new_simulations

    def run_local(self, input, repetitions=1):
        """ runs one input; returns simulation """
        print(" (local)")
        self.local_saudifirms.vent([input])


    def run_best(self):
        self.run_local(self.simulations.best_dict())

    def run_input(self, weight=0.5):
        self.run_local(InputSet.weight_point(weight))


    def test(self, input, repetitions, all=False):
        """ runs one input; returns simulation """
        raw_output = self.remote_saudifirms.run_D2D([input], repetitions)
        for row in raw_output:
            input = row['parameters']
            output = row['result']
            self.simulations.insert(input, output)
        actual_repetitions = len(raw_output)
        output_complete = defaultdict(lambda: defaultdict(int))
        for row in raw_output:
            output = row['result']
            for category in output:
                if isinstance(output[category], dict):
                    for key in output[category]:
                        output_complete[category][key] += (1 / actual_repetitions) * output[category][key]

        output_target_only = defaultdict(lambda: defaultdict(int))
        for row in raw_output:
            output = row['result']
            for category, key in SimulationSet.output_keys:
                output_target_only[category][key] += (1 / actual_repetitions) * output[category][key]
        return flatten(output_target_only, ''), flatten(output_complete, 'output')


def flatten(d, parent_key=''):
    items = []
    for k, v in d.items():
        new_key = parent_key + '_' + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)
