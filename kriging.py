__author__ = 'taghawi'
from simulationset import SimulationSet
from inputset import InputSet
from keypress import Keypress
from remotesaudifirms import RemoteSaudiFirms

class Kriging:
    def __init__(self, lower_limits, upper_limits, dtypes, fixed_parameters, target, initial_runs, repetitions):
        SimulationSet.setup(dtypes, target)
        InputSet.setup(lower_limits, upper_limits, dtypes, fixed_parameters)
        self.simulations = SimulationSet()
        self.repetitions = repetitions
        self.remote_saudifirms = RemoteSaudiFirms()
        input_set = InputSet()
        input_set.insert_middle_point()
        self.run_add(input_set, repetitions)



    def kriging(self, sweep_intervals='', batch_size=28, success=0.01):
        get_key = Keypress()
        stats_innovation_kriging = 0
        stats_innovation_simulation = 0
        iteration = 0
        while True:
            print("iteration: %i total simulations: %i" % (iteration, len(self.simulations)))
            old_best_input, old_best_metric = self.simulations.best()
            kriging_candidates, negative_values = self.brute_force_minimizer(sweep_intervals=sweep_intervals, schlinge=schlinge, num_return_best=batch_size)
            kriging_candidates = self.batch_model(kriging_candidates)
            kriging_candidate_is_better, kriging_candidate, num_better = self.candidates_better(old_best, kriging_candidates)
            if kriging_candidate_is_better:
                print("+k+ %s (%s) better: %i" % (kriging_candidate.vmetric(), old_best.vmetric(), num_better))
                stats_innovation_kriging += 1
                candidate = kriging_candidate
            else:
                print("-k- %s" % kriging_candidate.vmetric())
                candidate = old_best

            print("***    hypercube:")
            simulation_candidates = hypercube(candidate, schlinge, self.lb, self.ub, batch_size)
            simulation_candidates = self.batch_model_L2L(simulation_candidates)
            simulation_candidate_is_better, simulation_candidate, num_better = self.candidates_better(candidate, simulation_candidates)
            if simulation_candidate_is_better:
                print("+s+ %s (%s) better: %i" % (simulation_candidate.vmetric(), candidate.vmetric(), num_better))
                stats_innovation_simulation += 1
                candidate = simulation_candidate
            else:
                print("-s- %s" % simulation_candidate.vmetric())

            if not kriging_candidate_is_better and not simulation_candidate_is_better:
                schlinge -= 0.05
                assert len(schlinge) == 20  # ##
                assert len(candidate.input_a) == 20, candidate.input_a
                assert len(old_best.input_a) == 20
                assert len((candidate.input_a - old_best.input_a) / diameter) == 20
                schlinge = np.maximum(schlinge, np.absolute(candidate.input_a - old_best.input_a) / diameter)
                assert len(schlinge) == 20  # ##
                #schlinge = np.minimum(schlinge, [2] * len(schlinge))
                schlinge[schlinge < 0] = 0
                assert len(schlinge) == 20  # ##
                schlinge = np.maximum(np.absolute(self.best_x() - old_best.input_a) / initial_distance, schlinge)
                assert len(schlinge) == 20  # ##

            mprint("    simul:    %10.8f (%10.8f)" % (candidate.metric, (old_best.metric - candidate.metric)))
            try:
                score = self.gp.score(simulation_candidates.input_a, simulation_candidates.metric)
                mprint("    score: %4.2f" % score)
            except ValueError:
                if len(simulation_candidates.data) > 1:
                    raise
            except:
                mprint(simulationdata)
                mprint(schlinge / 4)
                raise
            pred = np.array([self.gp.predict(sim) for sim in simulation_candidates.input_a], dtype=np.float64)
            mprint("    mean prediction accuracy %f" % np.mean(np.absolute((simulation_candidates.input_a - pred) / simulation_candidates.metric)))
            stats_iterations += 1
            if self.best_y() < success:
                break
            if (schlinge <= 0.001).all():
                printpp()
                print("\n\n\ni  ----------- SCHLINGE RELEASED = 2 ---------------\n\n\n")
                printpp()
                schlinge.fill(2)
            keypressed = get_key()
            if keypressed == 'c' or keypressed == 'i':
                stats_result = self.best_y() ** 0.5
                print_stats(stats, self.data)
            if keypressed == 'c':
                return self.data.best_input_d(), stats




    def run_add(self, input, repetitions):
        """ runs one input; returns simulation """
        raw_output = self.remote_saudifirms.run_D2D([i for i in input] * self.repetitions)
        for row in raw_output:
            input = row['parameters']
            output = row['result']
            self.simulations.insert(input, output)
