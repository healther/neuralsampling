import collections
import os
import yaml

def flatten_dictionary(d, parent_key='', sep='_'):
    """Returns a flat dictionary with concatenated keys for a nested dictionary d

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
    try:
        os.makedirs(folder)
    except OSError as e:
        if e.errno!=17:
            raise


def collect_results_caller(args):
    """Wrapper for multiprocessing pool calls"""
    collect_results(**args)


def collect_results(folders, analysis_function, collected_file):
    """Calls analysis_function on all folders and dumps results into collected_file"""
    collected = {}
    for f in folders:
        collected.update(analysis_function( f ))

    with open(collected_file, 'w') as f:
        yaml.dump(collected, f)


def statestring_from_int(stateint, n_neurons):
    """Returns the string of {0,1} of length n_neurons corresponding to stateint

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
    """
    return "{0:0{width}b}".format(stateint, width=n_neurons)


def statelist_from_int(stateint, n_neurons):
    """Returns the binary list of length n_neurons corresponding to stateint

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
    """
    return [int(s) for s in "{0:0{width}b}".format(stateint, width=n_neurons)]

if __name__ == "__main__":
    import doctest
    print(doctest.testmod())

