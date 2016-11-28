
import os
from collections import deque
import numpy as np


def collect_mean_std_mean(folder, skip_header=2, max_rows=10000, outfile='output'):
    """Returns the mean and the std of the activities of the simulation in folder

    expects line n to contain the number of active neurons at timestep n

    Input:
        folder      string  folder of the simulation
        skip_header int     number of lines to skip at the beginning of the file
        max_rows    int     number of lines to consider for the mean and std
        outfile     string  file in folder that contains the output

    Output:
        dict        dict    key:    splitted folder
                            value:  dictionary with 'mean' and 'std' keys"""
    d = np.genfromtxt(os.path.join(folder, outfile), dtype=np.int32,
            skip_header=skip_header, max_rows=max_rows)
    v = {"mean": float(d.mean()), "std": float(d.std())}

    return {folder.split(os.sep)[-1].split("_"): v}


def collect_mean_std_state(folder, skip_header=2, max_rows=10000, outfile='output'):
    """Returns the mean and the std of the activities of the simulation in folder

    expects line n to contain a binary representation of the networkstate at timestep n

    Input:
        folder      string  folder of the simulation
        skip_header int     number of lines to skip at the beginning of the file
        max_rows    int     number of lines to consider for the mean and std
        outfile     string  file in folder that contains the output

    Output:
        dict        dict    key:    splitted folder
                            value:  dictionary with 'mean' and 'std' keys"""
    d = np.genfromtxt(os.path.join(folder, outfile), dtype=np.bool,
            delimiter=1, skip_header=skip_header, max_rows=max_rows)
    d = d.sum(axis=-1)
    v = {"mean": float(d.mean()), "std": float(d.std())}

    return {folder.split(os.sep)[-1].split("_"): v}


def collect_mean_std_spikes(folder, tau, skip_header=2, max_rows=10000, outfile='output'):
    """Returns the mean and the std of the activities of the simulation in folder

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
                            value:  dictionary with 'mean' and 'std' keys"""
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


if __name__ == '__main__':
    import doctest
    print(doctest.testmod())

