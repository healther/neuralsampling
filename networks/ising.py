"""This module implements the Ising model for neural networks."""
from __future__ import division

import os
import yaml
import itertools as it
import numpy as np
import scipy.stats

TIMECONSTANT = 150E-9
# helper functions


def _biases_from_weights(wlist):
    bias = []

    nid = wlist[0][0]
    weightsum = 0.
    for wline in wlist:
        if nid != wline[0]:
            bias.append(-weightsum * .5)
            weightsum = wline[2]
            nid = wline[0]
        else:
            weightsum += wline[2]
    else:
        bias.append(-weightsum * .5)

    return np.array(bias)


def _create_nn_unit_weights(linearsize=10, dimension=2):
    # returns list of lists for weights and ndarray for bias
    weights = []
    for nid in range(linearsize**dimension):
        connlist = [(nid + o) % (linearsize**(d + 1)) +
                    int(nid / linearsize**(d + 1)) * linearsize**(d + 1)
                    for d in range(dimension)
                    for o in [linearsize**d, -linearsize**d]
                    ]
        for connid in connlist:
            weights.append([nid, connid, 1.])

    return weights


# public facing functions


def create(linearsize, dimension, connection_paramters,
            bias_parameters, initail_state_parameters):
    pass


def analysis(**analysis_parameters):
    pass


def eta(config):
    linearsize = config['network']['parameters']['linearsize']
    dimension = config['network']['parameters']['dimension']
    nupdates = config['Config']['nupdates']

    return str(linearsize**dimension * nupdates * TIMECONSTANT)


def create_nn_singleinitial(linearsize, dimension, weight, meanactivity,
            zerostatetau, onestatetau, rseed,
            weightnoise=0., biasnoise=0., biasfactor=1., biasoffset=0.):
    np.random.seed(rseed)

    wlist = _create_nn_unit_weights(linearsize=linearsize,
                                            dimension=dimension)

    states = np.random.random(size=linearsize**dimension) < meanactivity
    states = states.astype(int)
    onestateids = states == 1
    zerostateids = states == 0
    states[onestateids] = onestatetau
    states[zerostateids] = zerostatetau

    # scale weights and noise if applicable
    weights = weight * np.array([wline[2] for wline in wlist])
    if weightnoise != 0.:
        weights *= np.random.normal(loc=1., scale=weightnoise,
                                        size=weights.shape)
    for i, w in enumerate(weights):
        wlist[i][2] = float(w)

    # generate appropriate bias and add noise if applicable
    b = _biases_from_weights(wlist)
    if biasnoise != 0.:
        b *= np.random.normal(loc=1., scale=biasnoise, size=b.shape)
    b *= biasfactor
    b += biasoffset

    return wlist, b.tolist(), states.tolist()


def get_mean_from_stateline(stateline):
    """Return the mean activity of the network based on the binary states."""
    mean = sum(int(s) for s in stateline)
    return mean


def get_energy_from_stateline(stateline):
    """Not implemented!"""
    return -1.


def get_mean_from_spikes(spikeline):
    """Returns the number of spikes in spikeline"""
    return len(spikeline.split())


def get_energy_from_spikes(spikeline):
    """Not implemented!"""
    return -1.


def get_mean_from_mean(spikeline):
    """Returns the number of spikes in spikeline"""
    return int(spikeline)


def get_energy_from_mean(spikeline):
    """Not implemented!"""
    return -1.


def get_mean_from_meanenergy(spikeline):
    """Returns the number of spikes in spikeline"""
    return int(spikeline.split()[0])


def get_energy_from_meanenergy(spikeline):
    """Not implemented!"""
    return float(spikeline.split()[1])


def analysis_mean(outfile, burnin=0, subsampling=1, nupdates=None, plot=False,
                    **kwargs):
    folder = os.path.join(os.path.split(outfile)[0])

    # get simulation parameters
    with open(os.path.join(folder, 'sim.yaml'), 'r') as f:
        simdict = yaml.load(f)
    nneurons = simdict["network"]["parameters"]["linearsize"]**simdict["network"]["parameters"]["dimension"]    # noqa

    # get results
    temperatures = []
    externalcurrents = []
    activities = []
    energies = []

    with open(outfile, 'r') as f:
        # read configline
        # Outputformat OutputEnv Updatescheme Activationtype Interactiontype: 11000     # noqa
        # for translation see src/type.h
        configline = f.readline()
        segments = configline.split()[1:]
        parameternames = segments[:-1]
        parameters = {pn: int(p)
                        for pn, p in zip(parameternames, segments[-1])}

        if parameters['OutputEnv'] == 0:  # binary state output
            get_mean_activity = get_mean_from_stateline
            get_energy = get_energy_from_stateline
        elif parameters['OutputEnv'] == 1:  # SpikesOutput
            get_mean_activity = get_mean_from_spikes
            get_energy = get_energy_from_spikes
        elif parameters['OutputEnv'] == 2:  # SummarySpikes
            raise NotImplementedError("Mean analysis not available for"
                                        " SummarySpikes output")
        elif parameters['OutputEnv'] == 3:  # MeanActivity
            get_mean_activity = get_mean_from_mean
            get_energy = get_energy_from_mean
        elif parameters['OutputEnv'] == 4:  # MeanActivityEnergy
            get_mean_activity = get_mean_from_meanenergy
            get_energy = get_energy_from_meanenergy
        else:
            raise NotImplementedError("Unrecognized outputformat "
                                    "{}".format(parameters["OutputEnv"]))

        if parameters['OutputEnv'] != 2:
            f.next()
            f.next()

            for line in it.islice(f, burnin, nupdates + 4, subsampling):
                try:
                    if line.startswith('____End of simulation____'):
                        break
                    if parameters['OutputEnv']:
                        env, line = line.split(' --- ')
                        temperatures.append(float(env.split()[0]))
                        externalcurrents.append(float(env.split()[1]))
                    activities.append(get_mean_activity(line) / nneurons)
                    energies.append(get_energy(line) / nneurons)
                except ValueError:
                    # Note; this is a hack for the not detection of the end
                    # marker with subsampling, may fail anytime
                    # should not be necessary if nupdates is set correctly
                    break

    temperaturemean = float(np.mean(temperatures))
    temperaturestd = float(np.std(temperatures))
    currentmean = float(np.mean(externalcurrents))
    currentstd = float(np.std(externalcurrents))
    actmean = float(np.mean(activities))
    actstd = float(np.std(activities))
    energymean = float(np.mean(energies))
    energystd = float(np.std(energies))
    nsamples = len(activities)

    heatcapacity = float(scipy.stats.moment(energies, 2) -
                            scipy.stats.moment(energies, 1)**2)
    susceptibility = float(scipy.stats.moment(activities, 2) -
                            scipy.stats.moment(activities, 1)**2)
    binder = float(1. - scipy.stats.moment(activities, 4) / 3. /
                            scipy.stats.moment(activities, 2)**2)

    analysisdict = {'nsamples': nsamples,
        'temperaturemean': temperaturemean, 'temperaturestd': temperaturestd,
        'currentmean': currentmean, 'currentstd': currentstd,
        'actmean': actmean, 'actstd': actstd,
        'energymean': energymean, 'energystd': energystd,
        'heatcapacity': heatcapacity, 'susceptibility': susceptibility,
        'binder': binder,
                    }

    # foldertemplate = simdict['folderTemplate']
    # simparameterkeys = utils.get_simparameters_from_template(foldertemplate)
    # flatsimdict = utils.flatten_dictionary(simdict)
    # for spkey in simparameterkeys:
    #     analysisdict[spkey] = flatsimdict[spkey]
    analysisdict['simdict'] = simdict

    with open(os.path.join(folder, 'analysis'), 'w') as f:
        f.write(yaml.dump(analysisdict))

    if plot:
        import sys
        import inspect
# crazy hack to be able to import modules from the parent...
        currentdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        sys.path.insert(0, currentdir)
        from plotting import plot_timecourse
        plot_timecourse(folder, {"activities": activities,
                                 "energies": energies}, subsampling)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv) == 2:
        analysis_mean(sys.argv[1], burnin=int(sys.argv[2]),
            subsampling=int(sys.argv[3]), nupdates=int(sys.argv[4]), plot=True)
    elif len(sys.argv) == 5:
        analysis_mean(sys.argv[1], burnin=int(sys.argv[2]),
            subsampling=int(sys.argv[3]), nupdates=int(sys.argv[4]), plot=True)
    else:
        print("Don't know what to do")
