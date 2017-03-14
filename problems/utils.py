from __future__ import print_function

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

