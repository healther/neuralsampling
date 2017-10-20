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


def get_activity_from_pdata(pdata):
    weights     = np.array(sorted(set(pdata['network_parameters_weight'])))
    biasfactors = np.array(sorted(set(pdata['network_parameters_biasfactor'])))

    plot_weights     = 1./borders(weights)
    plot_biasfactors = -borders(biasfactors)

    activities = -1 * np.ones((len(weights), len(biasfactors)))
    for pd in pdata.iterrows():
        i, = np.where(weights == pd[1]['network_parameters_weight'])
        j, = np.where(biasfactors == pd[1]['network_parameters_biasfactor'])
        activities[i, j] = pd[1]['actmean']

    activities = np.ma.masked_where(activities==-1, activities)

    return plot_weights, plot_biasfactors, activities


def plot_ising(pdatas, title):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for pdata in pdatas:
        plot_weights, plot_biasfactors, activities = get_activity_from_pdata(pdata)
        cax = ax.pcolor(plot_weights, plot_biasfactors, activities.T,
            vmin=0.4, vmax=0.6, edgecolors='k')
    fig.colorbar(cax)
    ax.set_title(title)
    ax.set_xlabel('BM weight')
    ax.set_ylabel('biasfactor')

    plt.savefig('z_meanact_{}.pdf'.format(title))


def get_pdatas(files, interesting_keys, analysis_keys):
    pdatas = []
    for fname in files:
        origdata = yaml.load(open(fname, 'r'))
        data = []
        for dd in origdata:
            if dd['analysis'] is None:
                continue
            outdict = {}
            analysisdict = dd['analysis']
            for k in interesting_keys:
                outdict[k] = dd[k]
            for k in analysis_keys:
                outdict[k] = analysisdict[k]
            data.append(outdict)
        pdatas.append(pandas.DataFrame(data))

    return pdatas


def plot_ising_runs(filepattern):
    interesting_keys = ['network_parameters_biasfactor',
                        'network_parameters_weight',
                        'network_parameters_rseed',
                        'Config_synapseType',]
    analysis_keys = ['actmean']
    pdatas = get_pdatas(filepattern, interesting_keys, analysis_keys)

    for rseed in set(pdatas[0]['network_parameters_rseed']):
        useddata = [pdata.loc[pdata['network_parameters_rseed']==rseed]
                                                        for pdata in pdatas]
        if len(set(useddata[0]['Config_synapseType'])) != 1:
            raise ValueError("I do not plot different synapse types")
        title = set(useddata[0]['Config_synapseType']).pop()+ '_' + str(rseed)
        plot_ising(useddata, title)


def plot_ising_run(collected_data_file):
    orig_data = yaml.load(open(collected_data_file, 'r'))

    interesting_keys = ['network_parameters_biasfactor',
                        'network_parameters_weight',
                        'network_parameters_rseed',
                        'Config_synapseType',]
    analysis_keys = ['actmean', 'actstd']
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
    if len(set(pdata['Config_synapseType'])) != 1:
        raise ValueError('Can only deal with one synapse type')
    for rseed in set(pdata['network_parameters_rseed']):
        plot_ising([pdata.loc[(pdata['network_parameters_rseed'] == rseed)]],
                pdata['Config_synapseType']+'_'+str(rseed))


if __name__ == '__main__':
    import sys
    plot_ising_runs(sys.argv[1:])
