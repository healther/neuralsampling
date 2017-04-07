"""This module implements the calibration function."""
from __future__ import division

import os
import sys
import yaml

import numpy as np
from scipy.optimize import curve_fit
from collections import Counter


def sigma(u, u05=0., alpha=1.):
    return 1./(1.+np.exp(-alpha*(u-u05)))


def fit(outfile, **kwargs):
    folder = os.path.dirname(outfile)
    spikes = []
    with open(os.path.join(folder, 'output'), 'r') as f:
        next(f)
        next(f)
        for line in f:
            for sp in line.strip().split(' '):
                if sp != '':
                    spikes.append(int(sp))

    simdict = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    rundict = yaml.load(open(os.path.join(folder, 'run.yaml'), 'r'))
    tau = simdict['Config']['tauref']
    nsimupdates = simdict['Config']['nupdates']
    biases = rundict['bias']

    nspikes = Counter(spikes)
    activities = [nspikes.get(i, 0)*tau/nsimupdates for i in range(len(biases))]

    popt, pcov = curve_fit(sigma, biases, activities)

    analysisdict = {}
    analysisdict['nspikes'] = nspikes
    analysisdict['activities'] = activities
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
    ([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [-2.0, 0.0, 2.0], [0, 0, 0])
    """
    biases = np.linspace(bmin, bmax, npoints).astype(float)
    initial_conditions = (np.ones(npoints) * ic).astype(int)

    return [[0, 0, 0.]], biases.tolist(), initial_conditions.tolist()


if __name__ == '__main__':
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())
