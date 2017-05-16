"""This module implements dwave energy minimization."""
import os
import sys
import numpy as np
import inspect
from collections import Counter, defaultdict
import itertools as it
import yaml

# crazy hack to be able to import modules from the parent...
currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, currentdir)
import utils


def readinput(filename="size1/size1_rt0.44_0001.txt"):
    currentdir = os.path.dirname(
                    os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)

    idata = np.loadtxt(os.path.join(parentdir, 'dwavedata', filename))
    existing_indices = list(set(int(i) for i in idata[:,  0]))
    nsampler = len(existing_indices)
    spin_weights = np.zeros((nsampler, nsampler))
    spin_biases = np.zeros(nsampler)

    for i, j, k in idata:
        if i == j:
            ni = existing_indices.index(i)
            spin_biases[ni] = k
        else:
            ni = existing_indices.index(i)
            nj = existing_indices.index(j)

            spin_weights[ni, nj] = .5 * k
            spin_weights[nj, ni] = .5 * k

    weights = 4 * spin_weights
    biases = 2 * spin_biases - 2 * spin_weights.sum(axis=1)

    return weights, biases


def analysis_energies(outfile, subsampling=1, most_common=10, **kwargs):
    # get results
    states = defaultdict(int)
    with open(outfile, 'r') as f:
        next(f)
        for line in it.islice(f, 0, None, subsampling):
            states[line[:-1]] += 1
    most_common_states = Counter(states).most_common(most_common)

    # get simulation paramters
    with open(os.path.join(os.path.split(outfile)[0], 'run.yaml'), 'r') as f:
        rundict = yaml.load(f)
    weights = np.array(rundict['weights'])
    biases = np.array(rundict['biases'])

    energies = []
    for state in most_common_states:
        state_list = [int(i) for i in state]
        energies.append(get_energy_network(state_list, weights, biases))

    analysisdict = {'states': state_list, 'energies': energies}

    # get simulation paramters
    with open(os.path.join(os.path.split(outfile)[0], 'sim.yaml'), 'r') as f:
        simdict = yaml.load(f)
    foldertemplate = simdict['folderTemplate']
    simparameterkeys = utils.get_simparameters_from_template(foldertemplate)
    flatsimdict = utils.flatten_dictionary(simdict)
    for spkey in simparameterkeys:
        analysisdict[spkey] = flatsimdict[spkey]

    with open(os.path.join(os.path.split(outfile)[0], 'analysis'), 'w') as f:
        f.write(yaml.dump(analysisdict))


def get_energy_network(state, weights, biases):
    if isinstance(state, (int, long)):
        state = [int(x) for x in list('{0:0b}'.format(state))]
    state = (len(biases) - len(state)) * [0] + state
    state = np.array(state)
    return np.dot(biases, state) + np.dot(state, np.dot(weights, state))


def get_energy_file(state, size, nr):
    filename = 'size{:1d}/size{:1d}_rt0.44_{:04d}.txt'.format(size, size, nr)
    weights, biases = readinput(filename)
    if isinstance(state, (int, long)):
        state = [int(x) for x in list('{0:0b}'.format(state))]
    state = (len(biases) - len(state)) * [0] + state
    state = np.array(state)
    print(state)
    return np.dot(biases, state) + np.dot(state, np.dot(weights, state))


def create_dwave(size=1, nr=0, initialstate=10000):
    filename = 'size{:1d}/size{:1d}_rt0.44_{:04d}.txt'.format(size, size, nr)
    weights, biases = readinput(filename)

    initial_conditions = np.ones_like(biases, dtype=int) * initialstate

    return (
                utils.full_matrix_to_sparse_list(weights),
                biases.tolist(),
                initial_conditions.tolist()
            )


if __name__ == '__main__':
    if len(sys.argv) == 1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv) == 2:
        print(create_dwave(sys.argv[1]))
    elif len(sys.argv) == 4:
        print(get_energy_file(int(sys.argv[1]), int(sys.argv[2]),
                        int(sys.argv[3])))
