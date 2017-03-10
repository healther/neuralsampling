"""This module implements the Ising model for neural networks."""
from __future__ import division

import os
import yaml

import numpy as np


TIMECONSTANT = 1000E-9
# helper functions


def _biases_from_weights(wlist):
    bias = []

    nid = wlist[0][0]
    weightsum = 0.
    for wline in wlist:
        if nid != wline[0]:
            bias.append(-weightsum * .5)
            weightsum = wline[2]
            nid = wline[0]
        else:
            weightsum += wline[2]
    else:
        bias.append(-weightsum * .5)

    return np.array(bias)


def _create_nn_unit_weights(linearsize=10, dimension=2):
    # returns list of lists for weights and ndarray for bias
    weights = []
    for nid in range(linearsize**dimension):
        connlist = [(nid + o) % (linearsize**(d + 1)) +
                    int(nid / linearsize**(d + 1)) * linearsize**(d + 1)
                    for d in range(dimension)
                    for o in [linearsize**d, -linearsize**d]
                    ]
        for connid in connlist:
            weights.append([nid, connid, 1.])

    return weights


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

    wlist = _create_nn_unit_weights(linearsize=linearsize,
                                            dimension=dimension)

    states = np.random.random(size=linearsize**dimension) < meanactivity
    states = states.astype(int)
    states[states == 1] = onestatetau
    states[states == 0] = zerostatetau

    # scale weights and noise if applicable
    weights = weight * np.array([wline[2] for wline in wlist])
    if weightnoise != 0.:
        weights *= np.random.normal(loc=1., scale=weightnoise,
                                        size=weights.shape)
    for i, w in enumerate(weights):
        wlist[i][2] = float(w)

    # generate appropriate bias and add noise if applicable
    b = _biases_from_weights(wlist)
    if biasnoise != 0.:
        b *= np.random.normal(loc=1., scale=biasnoise, size=b.shape)
    b *= biasfactor
    b += biasoffset

    return wlist, b.tolist(), states.tolist()


def analysis_mean(outfile, **kwargs):
    print(outfile)
    with open(outfile, 'r') as f:
        next(f)
        activities = [int(line) for line in f]
    mean, std = float(np.mean(activities)), float(np.std(activities))
    nsamples = len(activities)

    with open(os.path.join(os.path.split(outfile)[0], 'analysis'), 'w') as f:
        f.write(yaml.dump({'nsamples': nsamples, 'mean': mean, 'std': std}))


if __name__ == "__main__":
    import doctest
    print(doctest.testmod())
