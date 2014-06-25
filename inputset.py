__author__ = 'taghawi'
import numpy as np
from collections import defaultdict

class InputSet:
    """ stores inputs, avoids duplicates, returns them as dictionaries.
    Also provides lb, ub and dtype

    """
    def __init__(self, lower_bound, upper_bound, dtypes, fixed_input):
        lb_keys = get_two_hierarchies_of_keys(lower_bound)
        ub_keys = get_two_hierarchies_of_keys(upper_bound)
        dt_keys = get_two_hierarchies_of_keys(dtypes)
        assert lb_keys == ub_keys == dt_keys
        self.keys = lb_keys
        sulf.lb = self.encode(lower_bound)
        self.ub = self.encode(upper_bound)
        self.dtypes = self.encode(dtypes)
        self.data = []


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
            d[category][key] = self.dtypes[category,key](self.data[item][i])
            i += 1
        return d

    def encode(self, what):
        return [what[category][key] for category, key in self.keys]

    def is_in_data(self, what):
        assert isinstance(input, np.ndarray)
        for d in self.data:
            if np.array_equal(d, what):
                return True
        return False


def get_two_hierarchies_of_keys(hirarchical_dictionary):
    return tuple([(top, down) for top in hirarchical_dictionary.keys() for down in hirarchical_dictionary[top]])







