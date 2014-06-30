__author__ = 'taghawi'
import numpy as np
from collections import defaultdict
from inputset import InputSet, combine


class PredictedSet(InputSet):
    """ stores inputs, avoids duplicates, returns them as dictionaries.
    Also provides lb, ub and dtype

    """
    def __init__(self):
        self.inputs = []
        self.metrics = []

    def insert(self, input, metric):
        """
        inserts an array into the data
        :param input: ndarray
        :
        """
        assert isinstance(input, np.ndarray)
        input = InputSet.respect_bounds(input)
        if not self.is_in_data(input):
            self.inputs.append(input)
            self.metrics.append(metric)

    def __getitem__(self, item):
        """
        returns a json-dictionary with simulation parameters
        :param item: number
        :return: json with simulation input
        """
        d = defaultdict(dict)
        i = 0
        for category, key in self.keys:
            d[category][key] = self.dtypes[i](self.inputs[item][i])
            i += 1
        return combine(PredictedSet.fixed_input, d, self.keys), self.metrics[item]
