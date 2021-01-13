from __future__ import division

import numpy as np
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt # noqa


def plot_timecourse(folder, traces, time, seperate_axis=True):
    """

    Input:
        folder  string  path to folder of the simulation, output will be
                        placed there
        traces  dict    traces to plot
        time    int     if integer: subsampling step, i.e. entry
                        traces[key][i] = subsampling*i entry of trace
                array   if array: times for the traces
                dict    if dict: time[key] contains the times for traces[key]
        seperate_axis   if True, all traces are placed on each owns y-scale,
                        otherwise single y-axis

    Output:
        places a timecourse.pdf with all traces plotted on different axis
    """
    times = dict()
    if type(time) is int:
        times = {key: time*np.arange(0, len(traces[traces.keys()[0]]))
                            for key in traces.keys()}
    elif type(time) in [list, np.array]:
        times = {key: time for key in traces.keys()}
    elif type(time) is dict:
        times = times
    else:
        raise NotImplementedError("Don't understand time input, needs to "
                                    "be int, array or dict")
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel('Update step after burnin')
    if seperate_axis:
        axes = [ax] + [ax.twinx() for i in range(len(traces.keys())-1)]
    else:
        axes = [ax for i in range(len(traces.keys()))]
    for ax, color, key in zip(axes, colors, traces.keys()):
        ax.plot(times[key], traces[key], color=color, label=key)
        if seperate_axis:
            ax.set_ylabel(key)
        if key is "activities":
            ax.set_ylim(0., 1.)
    ax.legend()

    plt.savefig(os.path.join(folder, 'timecourse.pdf'))


if __name__ == "__main__":
    import sys
    folder = sys.argv[1]
    try:
        with open(folder + '/output', 'r') as f:
            f.readline()
            f.readline()
            f.readline()
            activities = []
            for line in f:
                activities.append(int(line.split()[-1])/8100.)
    except ValueError:
        pass
    plot_timecourse(folder, {'activities': activities}, 1)
