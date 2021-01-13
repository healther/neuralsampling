from __future__ import division

import pandas
import yaml
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def logistic(u, alpha, u05):
    return 1. / (1. + np.exp(-(u - u05) / alpha))


def plot_calibration_run(collected_data_file, plot_npoints=1000):
    orig_data = yaml.load(open(collected_data_file, 'r'))

    mincur = orig_data[0]['analysis']['network']['parameters']['bmin']
    maxcur = orig_data[0]['analysis']['network']['parameters']['bmax']
    npoints = orig_data[0]['analysis']['network']['parameters']['npoints']
    extcur = np.linspace(mincur, maxcur, npoints)

    interesting_keys = ['alpha', 'u05', 'activities']
    data = []

    for dd in orig_data:
        if dd['analysis'] is None:
            continue
        outdict = {}
        analysisdict = dd['analysis']
        for k, v in dd.iteritems():
            if k != 'analysis':
                outdict[k] = v
            for ik in interesting_keys:
                outdict[ik] = analysisdict[ik]
        outdict['externalCurrent'] = extcur
        data.append(outdict)

    curs = np.linspace(mincur, maxcur, plot_npoints)

    for pd in data:
        fig = plt.figure()
        ax = fig.add_subplot(211)
        ax.plot(pd['externalCurrent'], pd['activities'], 'x', label='data')
        ax.plot(curs, logistic(curs, pd['alpha'], pd['u05']),
                                label='fit_analysis')
        print(pd['Config_neuronType'], pd['Config_tausyn'],
                                pd['alpha'], pd['u05'])
        ax.set_xlabel('external Current')
        ax.set_ylabel('activity')
        ax.set_title('NT: {} tau: {}'.format(
            pd['Config_neuronType'], pd['Config_tausyn']))
        ax.legend()

        ax = fig.add_subplot(212)
        ax.plot(pd['externalCurrent'],
            pd['activities'] -
            logistic(pd['externalCurrent'], pd['alpha'], pd['u05']), 'x')

        print(pd['Config_neuronType'], pd['Config_tausyn'],
                                pd['alpha'], pd['u05'])
        ax.set_xlabel('external Current')
        ax.set_ylabel('residual')

        plt.savefig('activation_{}_{}.pdf'.format(
                        pd['Config_neuronType'], pd['Config_tausyn']))

        plt.close('all')

    pdata = pandas.DataFrame(data)
    view_log = pdata.loc[(pdata['Config_neuronType'] == 'log')]
    view_erf = pdata.loc[(pdata['Config_neuronType'] == 'erf')]

    print(view_log['Config_tausyn'])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(view_log['Config_tausyn'], view_log['alpha'], 'x', label='log')
    ax.plot(view_erf['Config_tausyn'], view_erf['alpha'], 'x', label='erf')
    ax.legend()
    ax.set_xscale('log')
    ax.set_xlabel('tau')
    ax.set_ylabel('alpha')
    plt.savefig('alpha.pdf')

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(view_log['Config_tausyn'],
            [u + np.log(tau) for u, tau in zip(view_log['u05'],
            view_log['Config_tausyn'])], 'x', label='log')
    ax.plot(view_erf['Config_tausyn'],
            [u + np.log(tau) for u, tau in zip(view_erf['u05'],
            view_erf['Config_tausyn'])], 'x', label='erf')
    ax.legend()
    ax.set_xscale('log')
    ax.set_xlabel('tau')
    ax.set_ylabel('u05')
    plt.savefig('u05.pdf')
    return data

if __name__ == '__main__':
    import sys
    plot_calibration_run(sys.argv[1])
