from __future__ import division
import numpy as np
from collections import defaultdict
from commonset import get_two_hierarchies_of_keys


class InputSet(object):
    """ stores inputs, avoids duplicates, returns them as dictionaries.
    Also provides lb, ub and dtype

    """
    @staticmethod
    def setup(lower_bound, upper_bound, dtypes, fixed_input):
        lb_keys = get_two_hierarchies_of_keys(lower_bound)
        ub_keys = get_two_hierarchies_of_keys(upper_bound)
        dt_keys = get_two_hierarchies_of_keys(dtypes)
        assert lb_keys == ub_keys == dt_keys
        InputSet.keys = lb_keys
        InputSet.lb = encode(lower_bound)
        InputSet.ub = encode(upper_bound)
        InputSet.dtypes = encode(dtypes)
        InputSet.fixed_input = fixed_input
        distance = InputSet.ub - InputSet.lb
        assert (distance > 0).all(), "lower- and upper-bound overlap"
        assert (distance < float("Inf")).all()

    def __init__(self):
        self.inputs = []

    def insert(self, input):
        """
        inserts an array into the data
        :param input: ndarray
        :
        """
        assert isinstance(input, np.ndarray)
        input = InputSet.respect_bounds(input)
        if not self.is_in_data(input):
            self.inputs.append(input)

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
        return combine(InputSet.fixed_input, d, self.keys)


    def is_in_data(self, what):
        assert isinstance(what, np.ndarray), type(what)
        for d in self.inputs:
            if np.array_equal(d, what):
                return True
        return False

    @staticmethod
    def respect_bounds(x):
        for i in range(len(x)):
            l = InputSet.lb[i]
            u = InputSet.ub[i]
            assert l < u, l - u
            if x[i] < l:
                x[i] = l
            if x[i] > u:
                x[i] = u
        return x

    @staticmethod
    def middle_point():
        """ inserts the middle point of the hyperplain as an entry """
        return InputSet.ub - InputSet.lb

    def __len__(self):
        return len(self.inputs)


def encode(what):
    return np.array([what[category][key] for category, key in InputSet.keys])

def combine(A, B, Bkeys):
    combined = defaultdict(dict)
    combined.update(A)
    for category, key in Bkeys:
        combined[category][key] = B[category][key]
    return combined