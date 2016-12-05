"""This module provides misceallous but unspecific functionality.

All public functions should be sideeffect free.
"""
### TODO: Move sideeffect functions to different files
import collections
import os
import yaml

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


def ensure_folder_exists(folder):
    """Create folder if not yet existing."""
    try:
        os.makedirs(folder)
    except OSError as e:
        if e.errno!=17:
            raise


### State format transformations
def get_statelist(state, n_neurons):
    """Return list of {0,1}^n_neurons according to state.

    >>> get_statelist(2, 3)
    [0, 1, 0]
    >>> get_statelist('010', 3)
    [0, 1, 0]
    >>> get_statelist([0, 1, 0], 3)
    [0, 1, 0]
    >>> get_statelist(8, 3)
    Traceback (most recent call last):
    ...
    ValueError: State 8 out of bounds 7
    >>> get_statelist('01', 3)
    Traceback (most recent call last):
    ...
    ValueError: Wrong string length 2 requires 3
    >>> get_statelist([0, 1], 3)
    Traceback (most recent call last):
    ...
    ValueError: Wrong list length 2 requires 3
    """
    if isinstance(state, int):
        return statelist_from_int(state, n_neurons)
    elif isinstance(state, str):
        return statelist_from_string(state, n_neurons)
    elif isinstance(state, list):
        if len(state)==n_neurons:
            return state
        else:
            raise ValueError("Wrong list length {} requires {}".format(len(state), n_neurons))


def get_statestring(state, n_neurons):
    """Return string of {0,1}^n_neurons according to state.

    >>> get_statestring([0, 1, 0], 3)
    '010'
    >>> get_statestring(2, 3)
    '010'
    >>> get_statestring('010', 3)
    '010'
    """
    statelist = get_statelist(state, n_neurons)
    return ''.join(str(i) for i in statelist)


def statelist_from_string(state, n_neurons):
    """Return list of {0,1}^n_neurons according to state.

    >>> statelist_from_string('010', 3)
    [0, 1, 0]
    >>> statelist_from_string('01', 3)
    Traceback (most recent call last):
    ...
    ValueError: Wrong string length 2 requires 3
    """
    if len(state)!=n_neurons:
        raise ValueError("Wrong string length {} requires {}".format(len(state), n_neurons))
    return [int(s) for s in state]


def statestring_from_int(stateint, n_neurons):
    """Return the string of {0,1} of length n_neurons corresponding to stateint.

    Input:
        stateint    int     integer representation of the state
        n_neurons   int     number of neurons in the system

    Output:
        statestring string  list of n_{0,1} according to stateint

    >>> statestring_from_int(0, 5)
    '00000'
    >>> statestring_from_int(31,5)
    '11111'
    >>> statestring_from_int(27, 5)
    '11011'
    >>> statestring_from_int(8, 3)
    Traceback (most recent call last):
    ...
    ValueError: State 8 out of bounds 7
    """
    if stateint >= 2**n_neurons:
        raise ValueError("State {} out of bounds {}".format(stateint, 2**n_neurons-1))
    return "{0:0{width}b}".format(stateint, width=n_neurons)


def statelist_from_int(stateint, n_neurons):
    """Return the binary list of length n_neurons corresponding to stateint.

    Input:
        stateint    int     integer representation of the state
        n_neurons   int     number of neurons in the system

    Output:
        statelist   list    list of n_neurons {0,1} according to stateint

    >>> statelist_from_int(0, 5)
    [0, 0, 0, 0, 0]
    >>> statelist_from_int(31,5)
    [1, 1, 1, 1, 1]
    >>> statelist_from_int(27, 5)
    [1, 1, 0, 1, 1]
    >>> statelist_from_int(8, 3)
    Traceback (most recent call last):
    ...
    ValueError: State 8 out of bounds 7
    """
    if stateint >= 2**n_neurons:
        raise ValueError("State {} out of bounds {}".format(stateint, 2**n_neurons-1))
    return [int(s) for s in "{0:0{width}b}".format(stateint, width=n_neurons)]

if __name__ == "__main__":
    import doctest
    print(doctest.testmod())

