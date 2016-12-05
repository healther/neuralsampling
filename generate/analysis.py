"""This module provides analysis functionality for neuralsampler output.

Public functions expect a folder as the only argument, expect an "output"
file with the output of the binary (see output format for further information)
and produce an "analysis_output" file containing the analysed results,
typically a dictionary or a list of dictionaries.
Should return 0 if and only if no exception had to be caught. It is
up to the function to decide whether that means attempting to perform
the complete anlaysis or fail after the first exception.

Private functions typically work on the "output" file itself or are
helper functions to those. Use with care and discression.
"""
from __future__ import division, print_function

import sys
from copy import deepcopy
from collections import defaultdict, Counter
from itertools import islice, product
import os
import numpy as np
import yaml


def state_distribution(folder, skiprows=3, updates=[1000,10000,100000,1000000]):
    """Write the state frequency distribution in analysis_output.

    Input:
        folder      string      folder on which to operate
        skiprows    int         number of rows at the beginning of the file to skip
        updates     list        list of ints of update numbers after which an outdict should be produced
    Output:
        success     int         1 if an exception occured 0 otherwise
    """
    try:
        freq_dicts = _frequencies_in_file(os.path.join(folder, 'output'),
                            skiprows=skiprows, updates=updates)
        outputfilename = os.path.join(folder, 'analysis_output')
        with open(outputfilename, 'w') as f:
            yaml.dump(freq_dicts, f)
        return 0
    except:
        raise
        return 1


def _frequencies_in_file(filename, skiprows=3, updates=[1000,10000,100000]):
    r"""Return the histogram of the lines in filename skipping skiprows.

    Input:
        filename    string  filename of the file to analyse
        skiprows    int     number of rows at the begining of the file to skip
        updates     list    list of ints of update numbers after which an outdict should be produced
    Output:
        outdicts    dict    TODO: correct #dictionary of a Counter of the line frequencies between the i-1-th and i-th entry in updates

    >>> with open('testfile.tmp', 'w') as f:
    ...     f.write('000\n010\n000\n100')
    >>> _frequencies_in_file('testfile.tmp', 0, [1,3,5])
    {1: {'000': 1}, 3: {'010': 1, '000': 1}, 4: {'100': 1}}
    """
    output = []
    dupdates = [updates[0]] + [u1-u2 for u1, u2 in zip(updates[1:], updates[:-1])]

    with open(filename, 'r') as f:
        for _ in xrange(skiprows):
            f.readline()
        for nu in dupdates:
            lines_gen = islice(f, nu)
            output.append(Counter(l.strip() for l in lines_gen))

    used_line_number = sum(sum(o.values()) for o in output)
    for i, o in enumerate(output):
        if len(o)==0:
            updates[i-1] = used_line_number
            output[i] = output[i-1]
    updates[-1] = used_line_number
    out = {n: dict(o) for n, o in zip(updates, output)}
    return out


def timeaverage_activity(folder, outputtype='mean', skip_header=3, max_rows=1000000, outfile='output', tau=100):
    """Return the mean and the std of the activities of the simulation in folder.

    expects line n to contain the number of active neurons at timestep n

    Input:
        folder      string  folder of the simulation
        outputtype  string  expected format of 'output' file ['mean', 'binary', 'spikes']
        skip_header int     number of lines to skip at the beginning of the file
        max_rows    int     number of lines to consider for the mean and std
        outfile     string  file in folder that contains the output
        tau         int     time of neuron to be 1, only used in 'spikes' mode

    Output:
        dict        dict    key:    splitted folder
                            value:  dictionary with 'mean' and 'std' keys
    """
    if outputtype=='mean':
        d = np.genfromtxt(os.path.join(folder, outfile), dtype=np.int32,
            skip_header=skip_header, max_rows=max_rows)
    elif outputtype=='binary':
        d = np.genfromtxt(os.path.join(folder, outfile), dtype=np.bool,
            delimiter=1, skip_header=skip_header, max_rows=max_rows)
        d = d.sum(axis=-1)
    elif outputtype=='spikes':
        d = []
        with open(os.path.join(folder, outfile), 'r') as f:
            for _ in range(skip_header):
                f.readline()
            que = deque([len(l.split()) for l in f[:tau]], tau)
            for line in f[:10000]:
                d.append(sum(que))
                que.append(len(line.split()))
    else:
        raise ValueError("outputtype must be one of 'mean', 'binary', 'spikes'!")
    v = {"mean": float(d.mean()), "std": float(d.std())}

    return {folder.split(os.sep)[-1].split("_"): v}


def collect_mean_std_state(folder, skip_header=2, max_rows=10000, outfile='output'):
    """Return the mean and the std of the activities of the simulation in folder.

    expects line n to contain a binary representation of the networkstate at timestep n

    Input:
        folder      string  folder of the simulation
        skip_header int     number of lines to skip at the beginning of the file
        max_rows    int     number of lines to consider for the mean and std
        outfile     string  file in folder that contains the output

    Output:
        dict        dict    key:    splitted folder
                            value:  dictionary with 'mean' and 'std' keys
    """
    d = np.genfromtxt(os.path.join(folder, outfile), dtype=np.bool,
            delimiter=1, skip_header=skip_header, max_rows=max_rows)
    d = d.sum(axis=-1)
    v = {"mean": float(d.mean()), "std": float(d.std())}

    return {folder.split(os.sep)[-1].split("_"): v}


def collect_mean_std_spikes(folder, tau, skip_header=2, max_rows=10000, outfile='output'):
    """Return the mean and the std of the activities of the simulation in folder.

    expects line n to contain space separated neuron_ids of the neurons that
        spiked in timestep n

    Input:
        folder      string  folder of the simulation
        tau         int     refractory time in timesteps
        skip_header int     number of lines to skip at the beginning of the file
        max_rows    int     number of lines to consider for the mean and std
        outfile     string  file in folder that contains the output

    Output:
        dict        dict    key:    splitted folder
                            value:  dictionary with 'mean' and 'std' keys
    """
    d = []
    with open(os.path.join(folder, outfile), 'r') as f:
        for _ in range(skip_header):
            f.readline()
        que = deque([len(l.split()) for l in f[:tau]], tau)
        for line in f[:10000]:
            d.append(sum(que))
            que.append(len(line.split()))
    v = {"mean": float(d.mean()), "std": float(d.std())}

    return {folder.split(os.sep)[-1].split("_"): v}


### distribution comparisons
def calculate_dkl(ptheo, fsampl, norm_theo=False):
    """Calculate the relative entropy when encoding fsampl with the optimal encoding of ptheo.

    Input:
        ptheo       list    theoretical probabilities for all states
        fsample     list    frequencies for all sampled states
        norm_theo   bool    if True ptheo /= sum(ptheo), default False
    Output:
        dkl     float   Kullback Leibler divergence

    >>> calculate_dkl([0.5,0.25,0.25], [2,1,1])
    0.0
    >>> calculate_dkl([0.5,0.25,0.25], [5,2,3])
    0.010067756775344432
    """
    if norm_theo:
        ptheo /= sum(ptheo)
    totn = np.sum(fsampl)
    return np.sum(f/totn * np.log(f/totn/p) for p,f in zip(ptheo, fsampl) if f!=0)


def energy_for_network(w,b, states=None):
    """Calculate the energy of the states, based on weights w and biases b.

    Input:
        w       ndarray     weights of the network
        b       ndarray     biases of the network
        states  list        list of states for which to calculate the energy, default None

    Output:
        energies    list    energy for each state in states, if states is None the energies
                            for all 2**n states

    >>> energy_for_network(np.array([[0.,1.],[1.,0.]]), np.array([-.5, .5]))
    [-0.0, -0.5, 0.5, -1.0]
    >>> energy_for_network(np.array([[0.,1.],[1.,0.]]), np.array([-.5, .5]), [[0,0],[1,1]])
    [-0.0, -1.0]
    """
    if states==None:
        states = [z for z in product([0,1], repeat=len(w))]
    return [ -.5*np.dot(z, np.dot(w, z))-np.dot(b,z) for z in states]


def get_minimal_energy_states(W, b):
    """Return a list of minmal energy states for BM (W, b).

    Input:
        W   array   weight matrix
        b   array   bias vector

    Output:
        minimal_states  list    list of the minimal energy states as ints

    >>> get_minimal_energy_states([[0., 1.], [1., 0.]], [-.5, .5])
    array([3])
    """
    e = energy_for_network(W, b)
    return np.nonzero(e==min(e))[0]


def probabilities_from_energies(energies):
    """Calculate the Boltzmann probabilities for the set of energies.

    Input:
        energies        list    list of energy of the single states

    Output:
        probabilities   list    list of the corresponding probabilities

    >>> probabilities_from_energies([0.,0.])
    [0.5, 0.5]
    >>> probabilities_from_energies([1.,1.])
    [0.5, 0.5]
    >>> probabilities_from_energies([0.,1.])
    [0.7310585786300049, 0.2689414213699951]
    >>> probabilities_from_energies([-1.,0.])
    [0.7310585786300049, 0.2689414213699951]
    """
    Z = np.sum(np.exp(-e) for e in energies)
    probabilities = [np.exp(-e)/Z for e in energies]
    return probabilities


def compare_sampling(outputfilename, configfilename, updates=[int(n) for n in np.logspace(3,8,11)]):
    """Return the "time"course of the DKL for the sampling results in outputfilename.

    Input:
        outputfilename  string  File that contains the output data in binary states
        configfilename  string  File that contains the configuration file for the simulation
        updates         list    List of updatesteps after which to calculate the DKL

    Output:
        updates         list    List of updatesteps after which the DKL was calculated
        dkls            list    List of DKLs between the sampled distribution and the theoretical one
    """
    w, b = get_weights_biases_from_config(configfilename)

    freq_dicts = frequencies_in_file(outputfilename, updates=updates)
    all_keys = list(set(k for fd in freq_dicts for k in fd.keys() ))

    states = np.array([ get_state_from_string(k)
                    for k in all_keys])
    energies = energy_for_network(w,b, states)
    probabilities = probabilities_from_energies(energies)

    frequencies = [freq_dicts[0].get(k, 0) for k in all_keys]
    dkl, totn = calculate_dkl(probabilities, frequencies)
    dkls = [dkl]
    updates = [totn]

    for fd in freq_dicts[1:]:
        frequencies = [f+fd.get(k, 0)
                            for f,k in zip(frequencies, all_keys)]
        totn = np.sum(frequencies)
        dkl = calculate_dkl(probabilities, frequencies)
        dkls.append(dkl)
        updates.append(totn)

    return updates, dkls



if __name__ == '__main__':
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv)==3:
        updates, dkls = compare_sampling(sys.argv[1], sys.argv[2])
        for u, d in zip(updates, dkls):
            print("N={:09d} DKL={:1.3e}".format(u,d))

