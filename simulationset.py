
from __future__ import division
from commonset import get_two_hierarchies_of_keys
import numpy as np
from collections import  defaultdict
from inputset import InputSet
import logging


logger = logging.getLogger('kriging.simulationset')

RESULT = 1

class SimulationSet:
    @staticmethod
    def setup(dtypes, target, transform):
        SimulationSet.input_keys = get_two_hierarchies_of_keys(dtypes)
        SimulationSet.output_keys = get_two_hierarchies_of_keys(target)
        SimulationSet.target = encode(target, SimulationSet.output_keys)
        SimulationSet.transform = transform

    def __init__(self):
        self.inputs = []
        self.metrics = []
        self.count = []

    def trf(self, output):
        self.transform(output)

    def insert(self, input, output):
        metric = self.metric(self.transform(output))
        input = encode(input, SimulationSet.input_keys)
        for i in range(len(self.inputs)):
            assert isinstance(input, np.ndarray), type(input)
            assert isinstance(self.inputs[i], np.ndarray), type(input)
            if np.array_equal(self.inputs[i], input):
                count = self.count[i]
                self.metrics[i] = (self.metrics[i] * count + metric) / (count + 1)
                self.count[i] += 1
                return False
        self.inputs.append(input)
        self.metrics.append(metric)
        self.count.append(1)
        assert len(self.inputs) == len(self.metrics) == len(self.count)
        return True

    def __getitem__(self, item):
        """
        returns a numpy-array with simulation parameters
        :param item: number
        :return: np.array with simulation input
        """
        return self.inputs[item], self.metrics[item]

    def is_new(self, input):
        """ tells whether an input is new"""
        assert isinstance(input, np.ndarray), type(input)
        for d in self.inputs:
            if np.array_equal(d, input):
                return False
        return True

    def metric(self, output):
        output = encode(output, SimulationSet.output_keys)
        return sum(((SimulationSet.target - output) / SimulationSet.target) ** 2)

    def average(self):
        try:
            return np.mean(self.metrics)
        except ValueError:
            return float("Inf")

    def best(self):
        try:
            index = np.argmin(self.metrics)
        except ValueError:
            return (np.zeros(len(SimulationSet.input_keys)), float("Inf"))
        input = self.inputs[index]
        result = self.metrics[index]
        return input, result

    def candidaties_better(self, old):
        return sum(np.array(self.metrics) > old[RESULT])

    def best_var_dict_result(self):
        input, result = self.best()
        d = defaultdict(dict)
        i = 0
        for category, key in SimulationSet.input_keys:
            d[category][key] = input[i]
            i += 1
        return d, result

    def best_var_dict(self):
        return self.best_var_dict_result()[0]

    def best_dict(self):
        return combine(InputSet.fixed_input, self.best_var_dict(), SimulationSet.input_keys)

    def __len__(self):
        return len(self.inputs)

    def half(self):
        middle = int(len(self.inputs) / 2)
        self.inputs = self.inputs[middle:]
        self.metrics = self.metrics[middle:]

    def filter(self, schlinge):

        best, _ = self.best()
        new_inputs = []
        new_metrics = []
        for input, metric in zip(self.inputs, self.metrics):
            if (best - schlinge < input).all() and (input < best + schlinge).all():
                new_inputs.append(input)
                new_metrics.append(metric)
        if len(new_metrics) > 1:
            logger.info("SimulationSet.filter for %i to %i:" % (len(self.metrics), len(new_metrics)))
            self.inputs = new_inputs
            self.metrics = new_metrics
        else:
            print("simulationset.filter XXXXXXXXXXXXXXXXXXXXXXXXXXX")


def encode(what, keys):
    return np.array([what[category][key] for category, key in keys])


def combine(A, B, Bkeys):
    combined = defaultdict(dict)
    combined.update(A)
    for category, key in Bkeys:
        combined[category][key] = B[category][key]
    return combined
