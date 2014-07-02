__author__ = 'taghawi'
from commonset import get_two_hierarchies_of_keys
import numpy as np

class SimulationSet:
    @staticmethod
    def setup(dtypes, target):
        SimulationSet.input_keys = get_two_hierarchies_of_keys(dtypes)
        SimulationSet.output_keys = get_two_hierarchies_of_keys(target)
        SimulationSet.target = encode(target, SimulationSet.output_keys)

    def __init__(self):
        self.inputs = []
        self.metrics = []

    def insert(self, input, output):
        input = encode(input, SimulationSet.input_keys)
        for i in range(len(self.inputs)):
            if (self.inputs[i] == input).all():
                self.metrics[i] = (self.metrics[i] + self.metric(output)) / 2
                return
        self.inputs.append(input)
        self.metrics.append(self.metric(output))

    def __getitem__(self, item):
        """
        returns a json-dictionary with simulation parameters
        :param item: number
        :return: json with simulation input
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

    def best(self):
        index = np.argmin(self.metrics)
        input = self.inputs[index]
        result = self.metrics[index]
        assert not(np.isnan(input).any())
        return input, result

    def __len__(self):
        return len(self.inputs)




def encode(what, keys):
    return np.array([what[category][key] for category, key in keys])