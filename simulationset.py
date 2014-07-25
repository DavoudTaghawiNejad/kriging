from __future__ import division
from commonset import get_two_hierarchies_of_keys
import numpy as np
from collections import  defaultdict
from inputset import InputSet

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

    def insert(self, input, output):
        metric = self.metric(self.transform(output))
        input = encode(input, SimulationSet.input_keys)
        for i in range(len(self.inputs)):
            if (self.inputs[i] == input).all():
                self.metrics[i] = (self.metrics[i] + metric) / 2
                return False
        self.inputs.append(input)
        self.metrics.append(metric)
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
        assert not(np.isnan(input).any())
        return input, result

    def best_dict(self):
        input, result = self.best()
        d = defaultdict(dict)
        i = 0
        for category, key in SimulationSet.input_keys:
            d[category][key] = input[i]
            i += 1
        return combine(InputSet.fixed_input, d, SimulationSet.input_keys)

    def __len__(self):
        return len(self.inputs)


def encode(what, keys):
    return np.array([what[category][key] for category, key in keys])


def combine(A, B, Bkeys):
    combined = defaultdict(dict)
    combined.update(A)
    for category, key in Bkeys:
        combined[category][key] = B[category][key]
    return combined
