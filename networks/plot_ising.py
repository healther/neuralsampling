from __future__ import division

import pandas
import yaml
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def borders(points):
    out = np.zeros(len(points) + 1)
    out[1:-1] = (points[1:] + points[:-1]) / 2.
    out[0] = 2 * points[0] - out[1]
    out[-1] = 2 * points[-1] - out[-2]
    return out


def plot_ising(pdata):
    weights     = np.array(sorted(set(pdata['network_parameters_weight'])))
    biasfactors = np.array(sorted(set(pdata['network_parameters_biasfactor'])))

    plot_weights     = borders(weights)
    plot_biasfactors = borders(biasfactors)

    activities = np.zeros((len(weights), len(biasfactors)))
    for pd in pdata.iterrows():
        i, = np.where(weights == pd[1]['network_parameters_weight'])
        j, = np.where(biasfactors == pd[1]['network_parameters_biasfactor'])
        activities[i, j] = pd[1]['mean']

    fig = plt.figure()
    ax = fig.add_subplot(111)
    cax = ax.pcolor(plot_weights, plot_biasfactors, activities.T,
        vmin=0., vmax=8100., edgecolors='k')
    fig.colorbar(cax)
    print(activities)


def plot_ising_run(collected_data_file, plot_npoints=1000):
    orig_data = yaml.load(open(collected_data_file, 'r'))

    interesting_keys = ['network_parameters_biasfactor',
                        'network_parameters_weight',
                        'network_parameters_rseed']
    analysis_keys = ['mean', 'std']
    data = []

    for dd in orig_data:
        if dd['analysis'] is None:
            continue
        outdict = {}
        analysisdict = dd['analysis']
        for k in interesting_keys:
            outdict[k] = dd[k]
        for k in analysis_keys:
            outdict[k] = analysisdict[k]
        data.append(outdict)

    pdata = pandas.DataFrame(data)
    for rseed in set(pdata['network_parameters_rseed']):
        plot_ising(pdata.loc[(pdata['network_parameters_rseed'] == rseed)])


if __name__ == '__main__':
    import sys
    plot_ising_run(sys.argv[1])
