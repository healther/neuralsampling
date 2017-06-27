import os
import copy
import collections
import imp


class memorize(dict):
    def __init__(self, func):
        self.func = func

    def __call__(self, *args):
        return self[args]

    def __missing__(self, key):
        result = self[key] = self.func(*key)
        return result


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


def append_iteration_of_experiment(experimentname):
    maxiteration = 0
    for fname in os.listdir(os.path.join('simulations', '01_runs')):
        if not fname.startswith(experimentname):
            continue
        # find extension
        iteration = fname.split(experimentname)[1]
        # strip prepended _
        maxiteration = max(maxiteration, int(iteration.strip('_')))

    return experimentname + "_{:03d}".format(maxiteration + 1)


def get_simparameters_from_template(foldertemplate):
    entries = foldertemplate.split('}_{')
    entries[0] = entries[0].split('{')[1]   # strip basefolder
    entries[-1] = entries[-1][:-1]          # strip final }

    return entries


def find_key_from_identifier(dict_to_expand, identifier):
    """Return a list of keys to all leaves of dict_to_expand whose values are
            identifier.

    >>> d = { 1: 'blub', 2: {3: 'blub', 4: 'hello'}}
    >>> find_key_from_identifier(d, 'blub')
    [[1], [2, 3]]
    """
    keypositions = []
    for k, v in dict_to_expand.iteritems():
        if v == identifier:
            keypositions.append([k])
        elif isinstance(v, dict):
            subkey_positions = find_key_from_identifier(v, identifier)
            for sk in subkey_positions:
                keypositions.append([k] + sk)
        elif isinstance(v, list):
            for i, x in enumerate(v):
                if x == identifier:
                    keypositions.append([k] + [i])

    return keypositions


def getFromDict(dataDict, key, *keys):
    if keys:
        return getFromDict(dataDict[key], *keys)
    else:
        return dataDict[key]


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


def _getFactorKey(rule):
    try:
        factor = float(rule[1])
        key2 = rule[2]
        value2 = None
    except ValueError:
        factor = 1
        key2 = rule[1]
        if "_" in key2:
            value2 = None
        else:
            value2 = key2
            key2 = None
    return factor, key2, value2


def apply_rules(expanded_dict, rules={}):
    for key, rule in rules.iteritems():
        try:
            # factor of different value, rule looks like
            # Target1Key_Target2Key: [factor, Source1Key_Source2Key_Source3Key]
            factor = float(rule[0])
            source_key = rule[1]
            source_keys = source_key.split('_')
            oldvalue = getFromDict(expanded_dict, *source_keys)
            update_dict(expanded_dict, factor * oldvalue, *key.split('_'))
        except ValueError:
            if rule[0] == '<':
                # elimination rule, rule looks like
                # Target1Key_Target2Key: [<, [factor,] Source1Key_Source2Key_Source3Key]
                # or
                # Target1Key_Target2Key: [<, value]
                factor, key2, value2 = _getFactorKey(rule)
                value1 = getFromDict(expanded_dict, *key.split('_'))
                if value2 is None:
                    value2 = getFromDict(expanded_dict, *key2.split('_'))
                if not value1 < factor * value2:
                    return False
            elif rule[0] == '<=':
                factor, key2, value2 = _getFactorKey(rule)
                value1 = getFromDict(expanded_dict, *key.split('_'))
                if value2 is None:
                    value2 = getFromDict(expanded_dict, *key2.split('_'))
                if not value1 <= factor * value2:
                    return False
            elif rule[0] == '==':
                factor, key2, value2 = _getFactorKey(rule)
                value1 = getFromDict(expanded_dict, *key.split('_'))
                if value2 is None:
                    value2 = getFromDict(expanded_dict, *key2.split('_'))
                if not value1 == factor * value2:
                    return False
            elif rule[0] == '>=':
                factor, key2, value2 = _getFactorKey(rule)
                value1 = getFromDict(expanded_dict, *key.split('_'))
                if value2 is None:
                    value2 = getFromDict(expanded_dict, *key2.split('_'))
                if not value1 >= factor * value2:
                    return False
            elif rule[0] == '>':
                factor, key2, value2 = _getFactorKey(rule)
                value1 = getFromDict(expanded_dict, *key.split('_'))
                if value2 is None:
                    value2 = getFromDict(expanded_dict, *key2.split('_'))
                if not value1 > factor * value2:
                    return False
    return True


def expanddict(dict_to_expand, expansions):
    """Return a list of copies of dict_to_expand with a kartesian product of
             all expansions.

    Input:
        dict_to_expand: dictionary with values to replace
        expansions: dictionary of {"identifier": [values]} tuples

    Output:
        expanded_dicts: list of dictionaries with all expansions due to the
                            kartesian product of the modifier values

    >>> d = { 1: 'blub', 2: {3: 'blub', 4: 'hello'}}
    >>> e = {'blub': ['a', 'b'], 'hello': [11, 12]}
    >>> expanddict(d, e)
    [{1: 'a', 2: {3: 'a', 4: 11}}, {1: 'b', 2: {3: 'b', 4: 11}}, {1: 'a', 2: {3: 'a', 4: 12}}, {1: 'b', 2: {3: 'b', 4: 12}}] # noqa
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


def generate_folder_template(replacement_dictionary, expanding_dictonary,
            base='simulations', experimentname=''):
    entries = []
    for replacement_id in replacement_dictionary.keys():
        keys = find_key_from_identifier(
                    flatten_dictionary(expanding_dictonary), replacement_id)
        # keys is a list of lists, i.e. keys[0] contains the list of nested
        # keys at which we find the replacement_id, due to the flattening,
        # this key has only length 1.
        entry = '{' + keys[0][0] + '}'
        entries.append(entry)

    return os.path.join(base, experimentname, "_".join(entries))


def ensure_exist(folder):
    try:
        os.makedirs(folder)
    except OSError:
        if not os.path.isdir(folder):
            raise


@memorize
def get_function_from_name(function_identifier, folder='networks'):
    """Return the callable function_identifier=network.function ."""
    modulename, functionname = function_identifier.split('.')
    directory = os.path.split(os.path.realpath(__file__))[0]
    parentdirectory = os.path.join(directory, os.pardir)
    module = imp.load_source('network',
                os.path.join(parentdirectory, folder, modulename + '.py'))
    func = getattr(module, functionname)
    return func


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
