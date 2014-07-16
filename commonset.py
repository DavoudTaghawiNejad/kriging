from __future__ import division


def get_two_hierarchies_of_keys(hirarchical_dictionary):
    return tuple([(top, down) for top in hirarchical_dictionary.keys() for down in hirarchical_dictionary[top]])