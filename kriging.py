__author__ = 'taghawi'
from simulationset import SimulationSet
from inputset import InputSet
import inputset
from keypress import Keypress
from remotesaudifirms import RemoteSaudiFirms
from kriging_model import kriger
import numpy as np
from copy import deepcopy
from hypercube import hypercube
from sklearn import gaussian_process
import json
import dataset
from hashlib import sha224



class Kriging:
    def __init__(self, lower_limits, upper_limits, dtypes, fixed_parameters, target, initial_runs, repetitions, db_name):
        SimulationSet.setup(dtypes, target)
        InputSet.setup(lower_limits, upper_limits, dtypes, fixed_parameters)
        self.repetitions = repetitions
        self.remote_saudifirms = RemoteSaudiFirms()

        self._db = dataset.connect("sqlite:///%s.sqlite3" % db_name)
        parameters = json.dumps(fixed_parameters)
        hash = sha224(parameters).hexdigest()[:7]
        overview = self._db['overview']
        overview.insert({'hash': hash, 'json_string': parameters})
        self.db = self._db[hash]


        self.simulations = SimulationSet()
        for row in self.db:
            try:
                input = json.loads(row['input'])
                output = json.loads(row['output'])
            except TypeError:
                print row['output']
            self.simulations.insert(input, output)
        print("loaded %i" % len(self.simulations))

        if len(self.simulations) < initial_runs:
            middle_point = InputSet.middle_point()
            simulation_candidates = hypercube(middle_point, np.ones_like(middle_point), InputSet.lb, InputSet.ub, initial_runs)
            self.run_add(simulation_candidates)

    def print_dict(self):
        inputset = InputSet()
        inputset.insert(InputSet.middle_point())
        print(dict(inputset[0]))

    def kriging(self, sweep_intervals='', batch_size=28, success=0.01):
        gp = gaussian_process.GaussianProcess()
        get_key = Keypress()
        sweep_intervals = inputset.encode(sweep_intervals)
        diameter = (InputSet.ub - InputSet.lb) / 2
        initial_distance = InputSet.ub - InputSet.lb
        schlinge = np.empty_like(InputSet.ub)
        schlinge.fill(2.0)
        stats_innovation_kriging = 0
        stats_innovation_simulation = 0
        stats_iterations = 0
        while True:
            print("")
            print("iteration: %i total simulations: %i" % (stats_iterations, len(self.simulations)))
            old_best = self.simulations.best()
            kriging_candidates = kriger(self.simulations, InputSet, sweep_intervals, schlinge, batch_size, gp)
            kriging_candidates = self.run_add(kriging_candidates)
            kriging_candidate_is_better, kriging_candidate, num_better = self.candidates_better(old_best, kriging_candidates)
            if kriging_candidate_is_better:
                print("+k+ %s (%s) better: %i" % (kriging_candidate[1], old_best[1], num_better))
                stats_innovation_kriging += 1
                candidate = kriging_candidate
            else:
                print("-k- %s" % kriging_candidate[1])
                candidate = old_best

            print("***    hypercube:")
            simulation_candidates = hypercube(candidate[0], schlinge, InputSet.lb, InputSet.ub, batch_size)
            simulation_candidates = self.run_add(simulation_candidates)
            simulation_candidate_is_better, simulation_candidate, num_better = self.candidates_better(candidate, simulation_candidates)
            if simulation_candidate_is_better:
                print("+s+ %s (%s) better: %i" % (simulation_candidate[1], candidate[1], num_better))
                stats_innovation_simulation += 1
                candidate = simulation_candidate
            else:
                print("-s- %s" % simulation_candidate[1])

            if not kriging_candidate_is_better and not simulation_candidate_is_better:
                schlinge -= 0.05
                schlinge = np.maximum(schlinge, np.absolute(candidate[0] - old_best[0]) / diameter)
                #schlinge = np.minimum(schlinge, [2] * len(schlinge))
                schlinge[schlinge < 0] = 0
                schlinge = np.maximum(np.absolute(self.simulations.best()[0] - old_best[0]) / initial_distance, schlinge)

            print("    simul:    %10.8f (%10.8f)" % (candidate[1], (old_best[1] - candidate[1])))
            try:
                score = gp.score(simulation_candidates.inputs, simulation_candidates.metrics)
                print("    score: %4.2g" % score)
            except ValueError:
                if len(simulation_candidates) > 1:
                    raise
            print("    schlinge average %f" % np.mean(schlinge))

            #TODO pred = np.array([gp.predict(candidate[0]) for candidate in simulation_candidates], dtype=np.float64)
            #TODO print("    mean prediction accuracy %f" % np.mean(np.absolute((simulation_candidates[0] - pred) / simulation_candidates[1])))
            stats_iterations += 1
            if self.simulations.best()[1] < success:
                break
            if (schlinge <= 0.001).all():
                print("\n\n\ni  ----------- SCHLINGE RELEASED = 2 ---------------\n\n\n")
                schlinge.fill(2)
            key_pressed = get_key()
            if key_pressed == 'c' or key_pressed == 'i':
                print("Schlinge %s" % str(schlinge))
                print("innovation_simulation: %i" % stats_innovation_simulation)
                print("innovation_kriging:    %i" % stats_innovation_kriging)
                print("iterations             %i" % stats_iterations)
                print("unique simulations     %i" % len(self.simulations))
                print(self.simulations.best_dict())
                if key_pressed == 'c':
                    return self.simulations.best()

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
            self.simulations.insert(input, output)
            new_simulations.insert(input, output)
            self.db.insert({'input': json.dumps(input), 'output': json.dumps(output)})
        return new_simulations

