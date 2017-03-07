import os


def ensure_exist(folder):
    try:
        os.makedirs(folder)
    except OSError:
        if not os.path.isdir(folder):
            raise


def get_value(dic, key, *keys):
    if keys:
        return get_value(dic[key], *keys)
    else:
        return dic[key]


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


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)
