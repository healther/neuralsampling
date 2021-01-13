from __future__ import division

import pandas
import yaml

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_activity(pdata, ax):
    xvalues = list(pdata['Is'])[0]
    activities = list(pdata['As'])
    upper_yvalues = [a[0][0] for a in activities[0]]
    lower_yvalues = [a[1][0] for a in activities[0]]
    ax.plot(xvalues, upper_yvalues)
    ax.plot(xvalues, lower_yvalues)


def plot_hysterese_run(collected_data_file):
    data = [d['analysis'] for d in yaml.load(open(collected_data_file, 'r'))
                                            if d['analysis'] is not None]
    for dd in data:
        dd.update(dd.pop('simdict'))

    pdata = pandas.DataFrame(data)

    for synapseType in set(pdata['Config_synapseType']):
        for bf in set(pdata['network_parameters_biasfactor']):
            # if bf != 1.0:
            #     continue
            for weight in set(pdata['network_parameters_weight']):
                if weight != 1.9:
                    continue
                try:
                    fig = plt.figure()
                    ax = fig.add_subplot(111)

                    plot_activity(pdata.loc[
                        (pdata['Config_synapseType'] == synapseType) &
                        (pdata['network_parameters_biasfactor'] == bf) &
                        (pdata['network_parameters_weight'] == weight)
                            ], ax)

                    ax.set_title(synapseType)
                    ax.set_xlabel('Iext')
                    ax.set_ylabel('Activity')

                    plt.savefig('hysterese_act_{synapseType}_{bf}_{weight}.pdf'.format( # noqa
                        synapseType=synapseType, bf=bf, weight=weight))

                    plt.close('all')
                except:
                    print(synapseType, weight, bf)

if __name__ == '__main__':
    import sys
    plot_hysterese_run(sys.argv[1])
