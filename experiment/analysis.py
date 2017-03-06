"""This module provides analysis functionality for neuralsampler output.

## TODO: write_ former public and working on folders
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
import collections
import itertools as it
import os
import numpy as np
import yaml

import misc
import config
import control

DEBUG = False

def write_state_distribution(folder, skiprows=3, updates=[1000,10000,100000,1000000]):
    """Write the state frequency distribution in analysis_output.

    Input:
        folder      string      folder on which to operate
        skiprows    int         number of rows at the beginning of the file to skip
        updates     list        list of ints of update numbers after which an outdict should be produced
    Output:
        success     int         1 if an exception occured 0 otherwise
    """
    try:
        freq_dicts = frequencies_in_file(os.path.join(folder, 'output'),
                            skiprows=skiprows, updates=updates)
        outputfilename = os.path.join(folder, 'analysis_output')
        with open(outputfilename, 'w') as f:
            yaml.dump(freq_dicts, f)
        return 0
    except:
        if DEBUG:
            raise
        return 1


def frequencies_in_file(filename, skiprows=3, updates=[1000,10000,100000]):
    r"""Return the histogram of the lines in filename skipping skiprows.

    Input:
        filename    string  filename of the file to analyse
        skiprows    int     number of rows at the begining of the file to skip
        updates     list    list of ints of update numbers after which an outdict should be produced
    Output:
        outdicts    dict    TODO: correct #dictionary of a Counter of the line frequencies between the i-1-th and i-th entry in updates

    >>> with open('testfile.tmp', 'w') as f:
    ...     f.write('000\n010\n000\n100')
    >>> frequencies_in_file('testfile.tmp', 0, [1,3,5])
    {1: {'000': 1}, 3: {'010': 1, '000': 1}, 4: {'100': 1}}
    """
    output = []
    dupdates = [updates[0]] + [u1-u2 for u1, u2 in zip(updates[1:], updates[:-1])]

    with open(filename, 'r') as f:
        for _ in xrange(skiprows):
            f.readline()
        for nu in dupdates:
            lines_gen = it.islice(f, nu)
            output.append(collections.Counter(l.strip() for l in lines_gen))

    used_line_number = sum(sum(o.values()) for o in output)
    for i, o in enumerate(output):
        if len(o)==0:
            updates[i-1] = used_line_number
            output[i] = output[i-1]
    updates[-1] = used_line_number
    out = {n: dict(o) for n, o in zip(updates, output)}
    return out


def write_timeaverage(folder, outputtype='mean', skip_header=3, max_rows=1000000, tau=100):
    try:
        average_dict = timeaverage_activity(os.path.join(folder, 'output'),
            outputtype, skip_header, max_rows, tau)
        outputfilename = os.path.join(folder, 'analysis_output')
        with open(outputfilename, 'w') as f:
            yaml.dump(average_dict, f)
        return 0
    except:
        if DEBUG:
            raise
        return 1


def timeaverage_activity(filename, outputtype='mean', skip_header=3, max_rows=1000000, tau=100):
    r"""Return the mean and the std of the activities of the simulation in folder.

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

    >>> with open('testfile.tmp', 'w') as f:
    ...     f.write('5\n8\n13\n9\n7')
    >>> timeaverage_activity('testfile.tmp', 'mean', 0, 5, None)
    {('',): {'std': 2.6532998322843198, 'mean': 8.4}}
    >>> with open('testfile.tmp', 'w') as f:
    ...     f.write('0010\n0111\n1111\n0000\n1100')
    >>> timeaverage_activity('testfile.tmp', 'binary', 0, 5, None)
    {('',): {'std': 1.4142135623730951, 'mean': 2.0}}
    >>> with open('testfile.tmp', 'w') as f:
    ...     f.write('1 4\n5 9 2 3\n13 15 21 4\n7 31 8 2\n14 12 11 5')
    >>> timeaverage_activity('testfile.tmp', 'spikes', 0, 5, 2)
    {('',): {'std': 2.449489742783178, 'mean': 5.0}}
    """
    if outputtype=='mean':
        d = np.genfromtxt(filename, dtype=np.int32,
            skip_header=skip_header, max_rows=max_rows)
    elif outputtype=='binary':
        d = np.genfromtxt(filename, dtype=int,
            delimiter=1, skip_header=skip_header, max_rows=max_rows)
        d = d.sum(axis=-1)
    elif outputtype=='spikes':
        d = []
        with open(filename, 'r') as f:
            for _ in range(skip_header):
                f.readline()
            que = collections.deque([], tau)
            for _ in range(tau):
                que.append(len([f.readline().split()]))
            for i, line in enumerate(f):
                d.append(sum(que))
                que.append(len(line.split()))
                if i>max_rows:
                    break
        d = np.array(d)
    else:
        raise ValueError("outputtype must be one of 'mean', 'binary', 'spikes'!")
    out = {"mean": float(d.mean()), "std": float(d.std())}
    return out


def write_dkl_development(folder, skiprows=3, updates=[int(n) for n in np.logspace(3,8,11)]):
    try:
        outfilename = os.path.join(folder, 'output')
        dkl_dict = dkl_development(outfilename, skiprows, updates)

        with open(os.path.join(folder, 'analysis_output'), 'w') as f:
            yaml.dump(dkl_dict, f)
        return 0
    except:
        if DEBUG:
            raise
        return 1


def dkl_development(filename, skiprows=3, updates=[int(n) for n in np.logspace(3,8,11)]):
    freq_dicts = frequencies_in_file(filename,
                            skiprows=skiprows, updates=updates)

    frequencies = []
    nupdates = []
    for k in sorted(freq_dicts.keys()):
        frequencies.append(collections.Counter(freq_dicts[k]))
        nupdates.append(k)
    for i in range(len(frequencies)-1):
        frequencies[i+1] += frequencies[i]

    n = len(frequencies[0].keys()[0])
    keys = [misc.get_statestring(z, n) for z in it.product([0,1], repeat=n)]
    frequencies = [[f[k] for k in keys] for f in frequencies]
    folder = os.path.dirname(filename)
    runfilename = os.path.join(folder, 'run.yaml')
    try:
        runyaml = yaml.load(open(runfilename,'r'))
    except IOError as e:
        if e.errno==2:
            # file was deleted after simulation, need to recreate
            control.dump_runfile(folder)
            runyaml = yaml.load(open(runfilename,'r'))
        else:
            raise e

    W, b = config.get_weights_biases_from_configfile(runfilename)
    ptheo = misc.probabilities_from_energies(misc.energies_for_network(W, b))

    dkls = [float(misc.calculate_dkl(ptheo, fsamp)) for fsamp in frequencies]
    return {'nupdates': nupdates, 'dkls': dkls}


def _compare_sampling(outputfilename, configfilename, updates=[int(n) for n in np.logspace(3,8,11)]):
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

