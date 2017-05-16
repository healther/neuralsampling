from __future__ import division, print_function

import sys
import collections


def flatten_dictionary(d, parent_key='', sep='_'):
    """Return a flat dictionary with concatenated keys for a nested dictionary d.

    >>> d = { 'a': {'aa': 1, 'ab': {'aba': 11}}, 'b': 2, 'c': {'cc': 3}}
    >>> flatten_dictionary(d)
    {'a_aa': 1, 'b': 2, 'c_cc': 3, 'a_ab_aba': 11}

    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dictionary(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_simparameters_from_template(foldertemplate):
    entries = foldertemplate.split('}_{')
    entries[0] = entries[0].split('{')[1]   # strip basefolder
    entries[-1] = entries[-1][:-1]          # strip final }

    return entries


def double_index_to_single(x, i, n_cities):
    """Transform double index (city, position) in single index.

    >>> double_index_to_single(0, 0, 5)
    0
    >>> double_index_to_single(1, 0, 5)
    5
    >>> double_index_to_single(1, 1, 5)
    6
    >>> double_index_to_single(6, 1, 4)
    9
    >>> double_index_to_single(6, 7, 5)
    7
    """
    return ((x % n_cities) * n_cities + (i % n_cities))


def single_index_to_double(n, n_cities):
    """Transform single index i to double index (city, position).

    >>> single_index_to_double(7, 5)
    (1, 2)
    >>> single_index_to_double(17, 4)
    (0, 1)
    """
    return int(n / n_cities) % n_cities, n % n_cities


def full_matrix_to_sparse_list(weights):
    wlist = []
    for i, wline in enumerate(weights):
        for j, w in enumerate(wline):
            if w != 0:
                wlist.append([i, j, w])
    return wlist


if __name__ == '__main__':
    if len(sys.argv) == 1:
        import doctest
        print(doctest.testmod())
