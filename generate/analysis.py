from __future__ import division, print_function

import sys
from copy import deepcopy
from collections import defaultdict, Counter
from itertools import islice, product
import numpy as np
import yaml


def frequencies_in_file(filename, skiprows=3, updates=[1000,10000,100000]):
    r"""Returns the histogram of the lines in filename skipping skiprows

    Input:
        filename    string  filename of the file to analyse
        skiprows    int     number of rows at the begining of the file to skip
        updates     list    list of ints of update numbers after which an outdict should be produced
    Output:
        outdicts    list    list of a Counter of the line frequencies between the i-1-th and i-th entry in updates
    
    >>> with open('testfile.tmp', 'w') as f:
    ...     f.write('000\n010\n000\n100')
    >>> frequencies_in_file('testfile.tmp', 0, [1,2,5])
    [Counter({'000\n': 1}), Counter({'100': 1, '000\n': 1, '010\n': 1})]
    """

    output = []
    dupdates = [u1-u2 for u1, u2 in zip(updates[1:], updates[:-1])]

    with open(filename, 'r') as f:
        for _ in xrange(skiprows):
            f.readline()
        for nu in dupdates:
            lines_gen = islice(f, nu)
            output.append(Counter(lines_gen))

    return output


def get_weights_biases_from_config(configfilename):
    d = yaml.load(open(configfilename, 'r'))

    return np.array(d['weight']), np.array(d['bias'])


def get_state_from_string(statestring):
    """Takes binary line of output and returns a list of ints

    Input:
        statestring     string  
    Output:
        outlist         list

    >>> get_state_from_string('1110')
    [1, 1, 1, 0]
    >>> get_state_from_string('1110 ')
    [1, 1, 1, 0]
    """
    return [int(s) for s in statestring.strip()]


def calculate_dkl(ptheo, fsampl):
    """Calculates the relative entropy when encoding fsampl with the optimal encoding of ptheo

    Input:
        ptheo   list    theoretical probabilities for all states
        fsample list    frequencies for all sampled states
    Output:
        dkl     float   Kullback Leibler divergence

    >>> calculate_dkl([0.5,0.25,0.25], [2,1,1])
    (0.0, 4)
    >>> calculate_dkl([0.5,0.25,0.25], [5,2,3])
    (0.010067756775344432, 10)"""
    totn = np.sum(fsampl)
    return np.sum(f/totn * np.log(f/totn/p) for p,f in zip(ptheo, fsampl) if f!=0), totn


def energy_for_network(w,b, states=None):
    if states==None:
        states = [z for z in product([0,1], repeat=len(w))]
    return [ -.5*np.dot(z, np.dot(w, z))-np.dot(b,z) for z in states]



def compare_sampling(outputfilename, configfilename, updates=[int(n) for n in np.logspace(3,8,11)]):
    w, b = get_weights_biases_from_config(configfilename)

    freq_dicts = frequencies_in_file(outputfilename, updates=updates)
    all_keys = list(set(k for fd in freq_dicts for k in fd.keys() ))

    states = np.array([ get_state_from_string(k) 
                    for k in all_keys])
    energies = energy_for_network(w,b, states)
    Z = np.sum(np.exp(-e) for e in energies)
    probabilities = [np.exp(-e)/Z for e in energies]

    frequencies = [freq_dicts[0].get(k, 0) for k in all_keys]
    dkl, totn = calculate_dkl(probabilities, frequencies)
    dkls = [dkl]
    updates = [totn]

    for fd in freq_dicts[1:]:
        frequencies = [f+fd.get(k, 0) 
                            for f,k in zip(frequencies, all_keys)]
        dkl, totn = calculate_dkl(probabilities, frequencies)
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

