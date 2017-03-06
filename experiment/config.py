### TBD: separation of functionality analysis/misc/collect/single problems
import copy
import yaml
import uuid


def find_key_from_identifier(dict_to_expand, identifier):
    """Return a list of keys to all leaves of dict_to_expand that value are identifier.

    >>> d = { 1: 'blub', 2: {3: 'blub', 4: 'hello'}}
    >>> find_key_from_identifier(d, 'blub')
    [[1], [2, 3]]
    """
    keypositions = []
    for k,v in dict_to_expand.iteritems():
        if v==identifier:
            keypositions.append([k])
        elif isinstance(v, dict):
            subkey_positions = find_key_from_identifier(v, identifier)
            for sk in subkey_positions:
                keypositions.append([k] + sk)
        elif isinstance(v, list):
            for i, x in enumerate(v):
                if x==identifier:
                    keypositions.append([k] + [i])

    return keypositions


def update_dict(dic, value, key, *keys):
    """Set dic[k0][k1]...[kn] = value for keys=[k0, k1, ..., kn].

    >>> d = { 1: 'blub', 2: {3: 'blub', 4: 'hello'}}
    >>> keys = find_key_from_identifier(d, 'blub')
    >>> update_dict(d, 'ch', *keys[0])
    >>> d
    {1: 'ch', 2: {3: 'blub', 4: 'hello'}}
    >>> update_dict(d, 'ch', *keys[1])
    >>> d
    {1: 'ch', 2: {3: 'ch', 4: 'hello'}}
    """
    if keys:
        update_dict(dic[key], value, *keys)
    else:
        dic[key] = value


def expanddict(dict_to_expand, expansions):
    """Return a list of copies of dict_to_expand with a kartesian product of all expansions.

    Input:
        dict_to_expand: dictionary with values to replace
        expansions: dictionary of {"identifier": [values]} tuples

    Output:
        expanded_dicts: list of dictionaries with all expansions due to the kartesian product of the modifier values

    >>> d = { 1: 'blub', 2: {3: 'blub', 4: 'hello'}}
    >>> e = {'blub': ['a', 'b'], 'hello': [11, 12]}
    >>> expanddict(d, e)
    [{1: 'a', 2: {3: 'a', 4: 11}}, {1: 'b', 2: {3: 'b', 4: 11}}, {1: 'a', 2: {3: 'a', 4: 12}}, {1: 'b', 2: {3: 'b', 4: 12}}]
    """
    expanded_dicts = [dict_to_expand]
    for ident, values in expansions.iteritems():
        keypositions = find_key_from_identifier(dict_to_expand, ident)
        tmp = []
        for d in expanded_dicts:
            for v in values:
                for kp in keypositions:
                    update_dict(d, v, *kp)
                tmp.append(copy.deepcopy(d))
        expanded_dicts = tmp
    return expanded_dicts


def get_weights_biases_from_configfile(filename):
    d = yaml.load(open(filename, 'r'))
    return d['weight'], d['bias']



if __name__ == "__main__":
    import doctest
    print(doctest.testmod())


