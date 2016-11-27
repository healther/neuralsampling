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
    collect_results(**args)


def collect_results(folders, analysis_function, collected_file):
    collected = {}
    for f in folders:
        collected.update(analysis_function( f ))

    with open(collected_file, 'w') as f:
        yaml.dump(collected, f)



if __name__ == "__main__":
    import doctest
    print(doctest.testmod())

