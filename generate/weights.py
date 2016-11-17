from __future__ import division


import numpy as np
import yaml
import sys




def generate_initialstate(num_sampler, mean_activity=0.5, tauref=100, rseed=42424242):
    """Returns a random initalstate with length num_sampler with an mean activity of mean_activity

    Input:
        num_sampler: int
        mean_activity: float
        tauref: int
        rseed: int
        dimension: int

    >>> generate_initialstate(10, 0.5, 100, 42424242)
    array([127,  73,  33, 198, 174,  12,  10,  83, 146, 183])
    """
    np.random.seed(rseed)
    high = tauref/mean_activity
    return np.random.randint( 0, int(high), num_sampler)


def generate_NN_connection_matrix(linearsize=10, dimension=2, weight=1.):
    """Returns the normed nearest neighbor connected weight matrix

    Input:
        linearsize: int
        dimension: int

    >>> generate_NN_connection_matrix(3, 1)
    array([[ 0.,  1.,  1.],
           [ 1.,  0.,  1.],
           [ 1.,  1.,  0.]])
    >>> generate_NN_connection_matrix(3, 2)
    array([[ 0.,  1.,  1.,  1.,  0.,  0.,  1.,  0.,  0.],
           [ 1.,  0.,  1.,  0.,  1.,  0.,  0.,  1.,  0.],
           [ 1.,  1.,  0.,  0.,  0.,  1.,  0.,  0.,  1.],
           [ 1.,  0.,  0.,  0.,  1.,  1.,  1.,  0.,  0.],
           [ 0.,  1.,  0.,  1.,  0.,  1.,  0.,  1.,  0.],
           [ 0.,  0.,  1.,  1.,  1.,  0.,  0.,  0.,  1.],
           [ 1.,  0.,  0.,  1.,  0.,  0.,  0.,  1.,  1.],
           [ 0.,  1.,  0.,  0.,  1.,  0.,  1.,  0.,  1.],
           [ 0.,  0.,  1.,  0.,  0.,  1.,  1.,  1.,  0.]])
    """
    weights = np.zeros((linearsize**dimension, linearsize**dimension))
    for nid in range(linearsize**dimension):
        connlist = [(nid+o) % (linearsize**(d+1)) +
                    int(nid/linearsize**(d+1))*linearsize**(d+1)
                    for d in range(dimension)
                    for o in [linearsize**d, -linearsize**d]
                    ]
        weights[nid, connlist] = weight
    return weights


def generate_bias(weights, factor=1., offset=0.):
    """Returns the bias vector for a given weight matrix, modified by factor and offset

    Input:
        weights: numpy 2d-array
        factor: float or numpy 1d-array with length len(weights)
        offset: float or numpy 1d-array with length len(weights)

    Output:
        bias = -.5 * factor * weights.sum(axis=-1) + offset

    >>> w = np.array([[0., 1., 1.], [1., 0., 1.], [0., 1., 1.]])
    >>> generate_bias(w)
    array([-1., -1., -1.])
    >>> generate_bias(w, 2.)
    array([-2., -2., -2.])
    >>> generate_bias(w, 1., .5)
    array([-0.5, -0.5, -0.5])
    >>> generate_bias(w, np.array([1.,2.,.5]), np.array([.5,.0,-.5]))
    array([-0.5, -2. , -1. ])
    """
    biases = -.5 * weights.sum(axis=-1)
    biases *= factor
    biases += offset
    return biases


def generate(dictionary):
    connection_function = globals()[dictionary["connection_function"]]
    initialstate_function = globals()[dictionary["initialstate_function"]]
    bias_function = globals()[dictionary["bias_function"]]

    weight = connection_function(**dictionary["connection"])
    bias = bias_function(weights=weight, **dictionary["bias"])
    initialstate = initialstate_function(num_sampler=len(weight), **dictionary["initialstate"])

    return weight.tolist(), bias.tolist(), initialstate.tolist()


if __name__=="__main__":
    import doctest
    doctest.testmod()

