"""This module implements the Ising model for neural networks."""
from __future__ import division

import os
import yaml

import numpy as np


TIMECONSTANT = 20E-8
# helper functions


def _biases_from_weights(weights, biasfactor=1., biasoffset=0.):
    return -biasfactor * np.sum(weights, axis=-1) / 2. + biasoffset


def _create_nn_unit_weights_biases(linearsize=10, dimension=2):
    weights = np.zeros((linearsize**dimension, linearsize**dimension))
    for nid in range(linearsize**dimension):
        connlist = [(nid + o) % (linearsize**(d + 1)) +
                    int(nid / linearsize**(d + 1)) * linearsize**(d + 1)
                    for d in range(dimension)
                    for o in [linearsize**d, -linearsize**d]
                    ]
        weights[nid, connlist] = 1.
    biases = _biases_from_weights(weights)

    return weights, biases


# public facing functions


def create(linearsize, dimension, connection_paramters,
            bias_parameters, initail_state_parameters):
    pass


def analysis(**analysis_parameters):
    pass


def eta(config):
    linearsize = config['network']['parameters']['linearsize']
    dimension = config['network']['parameters']['dimension']
    nupdates = config['Config']['nupdates']

    return str(linearsize**dimension * nupdates * TIMECONSTANT)


def create_nn_singleinitial(linearsize, dimension, weight, meanactivity,
            zerostatetau, onestatetau, rseed,
            weightnoise=0., biasnoise=0., biasfactor=1., biasoffset=0.):
    np.random.seed(rseed)

    W, b = _create_nn_unit_weights_biases(linearsize=linearsize,
                                            dimension=dimension)
    states = np.random.random(size=linearsize**dimension) < meanactivity
    states = states.astype(int)
    states[states == 1] = onestatetau
    states[states == 0] = zerostatetau

    if weightnoise != 0.:
        W *= np.random.normal(loc=1., scale=biasnoise, size=W.shape)
    if biasnoise != 0.:
        b *= np.random.normal(loc=1., scale=biasnoise, size=b.shape)
    b *= biasfactor
    b += biasoffset

    return W.tolist(), b.tolist(), states.tolist()


def analysis_mean(outfile):
    with open(outfile, 'r') as f:
        activities = [int(line) for line in f]
    mean, std = float(np.mean(activities)), float(np.std(activities))
    nsamples = len(activities)

    with open(os.path.join(os.path.realpath(outfile)[0], 'output'), 'w') as f:
        f.write(yaml.dump({'nsamples': nsamples, 'mean': mean, 'std': std}))


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
