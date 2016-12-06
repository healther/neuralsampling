"""This module implements the Ising model for neural networks."""
from __future__ import division


import numpy as np
import yaml
import sys


def _biases_from_weights(weights, biasfactor=1., biasoffset=0.):
    return -biasfactor*np.sum(weights, axis=-1)/2. + biasoffset


def create_NN(linearsize=10, dimension=2, weight=1., ic_mean=0.5, tau=100, ic_rseed=42424242):
    """Return the nearest neighbor connected weight matrix.

    Input:
        linearsize:     int
        dimension:      int
        weight:         float

    >>> create_NN(3, 1, 1.)
    ([[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]], [-1.0, -1.0, -1.0], [12, 80, 19])
    >>> create_NN(3, 2, 1.)
    ([[0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0], [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0], [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0]], [-2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0], [12, 80, 19, 128, 11, 56, 159, 38, 164])
    """
    weights = np.zeros((linearsize**dimension, linearsize**dimension))
    for nid in range(linearsize**dimension):
        connlist = [(nid+o) % (linearsize**(d+1)) +
                    int(nid/linearsize**(d+1))*linearsize**(d+1)
                    for d in range(dimension)
                    for o in [linearsize**d, -linearsize**d]
                    ]
        weights[nid, connlist] = weight
    biases = _biases_from_weights(weights)
    np.random.seed(ic_rseed)
    ic_low = 0
    if ic_mean!=0.:
        ic_high = tau/ic_mean
    else:
        ic_high = tau
    initial_conditions = np.random.uniform(ic_low, ic_high, len(biases)).astype(int)
    return weights.tolist(), biases.tolist(), initial_conditions.tolist()


def create_NN_noisy(linearsize=10, dimension=2, weight=1., ic_mean=0.5, tau=100, ic_rseed=42424242,
        bias_noise=.1, weight_noise=.1, noise_rseed=42424242):
    W, b, i = create_NN(linearsize, dimension, weight, ic_mean, tau, ic_rseed)
    np.random.seed(noise_rseed)
    W = np.array(W)
    W *= np.random.normal(loc=1., scale=weight_noise, size=W.shape)
    b = np.array(b)
    b *= np.random.normal(loc=1., scale=bias_noise, size=b.shape)
    return W.tolist(), b.tolist(), i


def create_NN_biasfactor(linearsize=10, dimension=2, weight=1., ic_mean=0.5, tau=100, ic_rseed=42424242,
        bias_factor=1.):
    W, b, i = create_NN(linearsize, dimension, weight, ic_mean, tau, ic_rseed)
    b = np.array(b)*bias_factor
    return W, b.tolist(), i


if __name__=="__main__":
    import doctest
    print(doctest.testmod())

