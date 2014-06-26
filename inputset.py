__author__ = 'taghawi'
import numpy as np
from collections import defaultdict
from commonset import get_two_hierarchies_of_keys


class InputSet:
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
        InputSet.data = []


    def insert(self, input):
        """
        inserts an array into the data
        :param input: ndarray
        :
        """
        assert isinstance(input, np.ndarray)
        if not self.is_in_data(input):
            self.data.append(input)

    def __getitem__(self, item):
        """
        returns a json-dictionary with simulation parameters
        :param item: number
        :return: json with simulation input
        """
        d = defaultdict(dict)
        i = 0
        for category, key in self.keys:
            d[category][key] = self.dtypes[i](self.data[item][i])
            i += 1
        return combine(InputSet.fixed_input, d, self.keys)


    def is_in_data(self, what):
        assert isinstance(what, np.ndarray), type(what)
        for d in self.data:
            if np.array_equal(d, what):
                return True
        return False

    def respect_lb(self, x):
        """ sets every parameter to at least the lower bound"""
        assert isinstance(x, np.ndarray)
        return np.maximum(self.lb, x)

    def respect_ub(self, x):
        """ sets every parameter to at most the upper bound"""
        assert isinstance(x, np.ndarray)
        return np.minimum(self.ub, x)

    def respect_bounds(self, x):
        """ sets every parameter to at least the lower and at most the upper bound"""
        assert (self.lb <= self.ub).all()
        x = self.respect_lb(x)
        x = self.respect_ub(x)
        return x

    def insert_middle_point(self):
        """ inserts the middle point of the hyperplain as an entry """
        self.insert(InputSet.ub - InputSet.lb)


def encode(what):
    return np.array([what[category][key] for category, key in InputSet.keys])

def combine(A, B, Bkeys):
    combined = defaultdict(dict)
    combined.update(A)
    for category, key in Bkeys:
        combined[category][key] = B[category][key]
    return combined






