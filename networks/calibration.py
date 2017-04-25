"""This module implements the calibration function."""
from __future__ import division

import os
import sys
import yaml

import numpy as np
from scipy.optimize import curve_fit
from collections import Counter


def sigma(u, u05=0., alpha=1.):
    return 1. / (1. + np.exp(-(u - u05) / alpha))


def fit(outfile, minact=0.05, maxact=0.95, **kwargs):
    folder = os.path.dirname(outfile)
    nspikes = Counter()
    with open(os.path.join(folder, 'output'), 'r') as f:
        next(f)  # strip status line
        for line in f:
            neuronid, neuron_nspikes = line.strip().split(' ')
            nspikes[int(neuronid)] = int(neuron_nspikes)

    simdict = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    rundict = yaml.load(open(os.path.join(folder, 'run.yaml'), 'r'))
    tau = simdict['Config']['tauref']
    nsimupdates = simdict['Config']['nupdates']
    biases = rundict['bias']

    activities = [nspikes.get(i, 0) * tau / nsimupdates
                            for i in range(len(biases))]

    analysisdict = {}
    analysisdict['nspikes'] = nspikes
    analysisdict['activities'] = activities

    biases = [b for b, a in zip(biases, activities)
                                        if ((a < maxact) and (a > minact))]
    activities = [a for a in activities if ((a < maxact) and (a > minact))]

    popt, pcov = curve_fit(sigma, biases, activities)

    analysisdict['alpha'] = float(popt[1])
    analysisdict['u05'] = float(popt[0])
    analysisdict.update(simdict)

    yaml.dump(analysisdict, open(os.path.join(folder, 'analysis'), 'w'))


def create(npoints, bmin, bmax, ic):
    """Create concrete Boltzmann machine.

    Input:
        npoints int     number of samplers
        bmin    float   minimal bias tested
        bmax    float   maximum bias tested
        ic      int     initial condition of all samplers

    samplers will be distributed uniformely on [bmin, bmax]
    >>> create(3, -2., 2., 0)
    ([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [-2.0, 0.0, 2.0], [0, 0, 0]) # noqa
    """
    biases = np.linspace(bmin, bmax, npoints).astype(float)
    initial_conditions = (np.ones(npoints) * ic).astype(int)

    return [[0, 0, 0.]], biases.tolist(), initial_conditions.tolist()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        import doctest
        print(doctest.testmod())
