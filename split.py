from __future__ import division
from collections import defaultdict

def split(dictionary):
    fixed = defaultdict(dict)
    lower = defaultdict(dict)
    upper = defaultdict(dict)
    dtypes = defaultdict(dict)
    for category in dictionary:
        for key in dictionary[category]:
            try:
                lower[category][key], upper[category][key], dtypes[category][key] = dictionary[category][key]
            except TypeError:
                fixed[category][key] = dictionary[category][key]
    return fixed, lower, upper, dtypes

