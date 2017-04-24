from __future__ import division

import pandas
import numpy as np
import yaml

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_activity(pdata, ax):
    for bo in set(pdata['network_parameters_biasoffset']):
        xdata = pdata.loc[pdata['network_parameters_biasoffset'] == bo]['temperature_values'] # noqa
        ydata = pdata.loc[pdata['network_parameters_biasoffset'] == bo]['mean']
        yerr = pdata.loc[pdata['network_parameters_biasoffset'] == bo]['std']
        ax.errorbar(xdata, ydata, yerr, fmt='x', label=str(bo))
        ax.axhline(2500. / (1. + np.exp(-bo)))


def plot_susceptibility(pdata, ax, mean):
    for bo in set(pdata['network_parameters_biasoffset']):
        xdata = pdata.loc[pdata['network_parameters_biasoffset'] == bo]['temperature_values'] # noqa
        ydata = pdata.loc[pdata['network_parameters_biasoffset'] == bo]['mean']
        target_activity = 2. * mean / (1. + np.exp(-bo))
        # find relative activity & calculate susceptibility
        ydata = abs(ydata - mean) / (target_activity - mean)
        yerr = pdata.loc[pdata['network_parameters_biasoffset'] == bo]['std']
        yerr /= (target_activity - mean)
        ax.errorbar(xdata, ydata, yerr, fmt='x', label=str(bo))


def plot_cw_run(collected_data_file):
    data = [d['analysis'] for d in yaml.load(open(collected_data_file, 'r'))
                                            if d['analysis'] is not None]
    for dd in data:
        dd['temperature_values'] = dd['temperature_values'][0]

    pdata = pandas.DataFrame(data)

    for synapseType in set(pdata['Config_synapseType']):
        for bf in set(pdata['network_parameters_biasfactor']):
            for update in set(pdata['Config_networkUpdateScheme']):
                fig = plt.figure()
                ax = fig.add_subplot(111)

                plot_activity(pdata.loc[
                    (pdata['Config_synapseType'] == synapseType) &
                    (pdata['network_parameters_biasfactor'] == bf) &
                    (pdata['Config_networkUpdateScheme'] == update)
                        ], ax)
                ax.set_xscale('log')
                ax.set_title(synapseType)
                ax.set_xlabel('Temperature')
                ax.set_ylabel('Activity')
                ax.legend()

                plt.savefig('cw_act_{synapseType}_{bf}_{update}.pdf'.format(
                    synapseType=synapseType, bf=bf, update=update))

                fig = plt.figure()
                ax = fig.add_subplot(111)

                plot_susceptibility(pdata.loc[
                    (pdata['Config_synapseType'] == synapseType) &
                    (pdata['network_parameters_biasfactor'] == bf) &
                    (pdata['Config_networkUpdateScheme'] == update)
                        ], ax, mean=1250.)
                ax.set_xscale('log')
                ax.set_title(synapseType)
                ax.set_xlabel('Temperature')
                ax.set_ylabel('Susceptibility')
                ax.legend()

                plt.savefig('cw_sus_{synapseType}_{bf}_{update}.pdf'.format(
                    synapseType=synapseType, bf=bf, update=update))
                plt.close('all')

if __name__ == '__main__':
    import sys
    plot_cw_run(sys.argv[1])
