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
        self.results = []

    def insert(self, input, output):
        self.inputs.append(encode(input, SimulationSet.input_keys))
        self.results.append(self.metric(output))

    def metric(self, output):
        output = encode(output, SimulationSet.output_keys)
        return sum(((SimulationSet.target - output) / SimulationSet.target) ** 2)

    def best(self):
        index = np.argmin(self.results)
        input = self.inputs[index]
        result = self.results[index]
        assert not(np.isnan(input).any())
        return input, result

    def __len__(self):
        return len(self.inputs)

def encode(what, keys):
    return [what[category][key] for category, key in keys]
