"""This module implements the hysteresis analysis functions"""
from __future__ import division

import os
import yaml
import itertools as it
import numpy as np

import utils


def get_data(outfile, subsampling=1):
    Ts = []
    Is = []
    As = []
    with open(outfile, 'r') as f:
        next(f)
        next(f)
        for line in it.islice(f, 0, None, subsampling):
            T, I, A = line.split(' ')
            Ts.append(float(T))
            Is.append(float(I))
            As.append(int(A))

    return Ts, Is, As


def get_lists(Is, As, nIpoints):
    minI, maxI = min(Is) - .0001, max(Is) + .0001
    boundaryIs = np.linspace(minI, maxI, nIpoints + 1)
    listIs = [float(I) for I in (boundaryIs[1:] + boundaryIs[:-1]) / 2]
    listAs = [[] for _ in range(nIpoints)]
    try:
        for I, A in zip(Is, As):
            nid = next(i for i, bI in enumerate(boundaryIs) if bI >= I) - 1
            listAs[nid].append(A)
    except:
        print(I, A, nid, minI, maxI)
        print(boundaryIs[nid - 1])
        print(listAs[0])
        raise

    maxA = max(As)
    for i, As in enumerate(listAs):
        if max(As) - min(As) < .05 * maxA:
            listAs[i] = 2 * [(float(np.mean(As)), float(np.std(As)))]
        else:
            upperbranchAs = [a for a in As if a >  (max(As) + min(As)) / 2]
            lowerbranchAs = [a for a in As if a <= (max(As) + min(As)) / 2]
            listAs[i] = [(float(np.mean(upperbranchAs)),
                            float(np.std(upperbranchAs))),
                         (float(np.mean(lowerbranchAs)),
                            float(np.std(lowerbranchAs)))]

    return listIs, listAs, maxA


def get_area_from_lists(listAs, listIs):
    area = 0.
    for lAl, lIl, lAr, lIr in zip(listAs[:-1], listIs[:-1],
                                        listAs[1:], listIs[1:]):
        # activity difference on the left boundary
        hl = (lAl[0][0] - lAl[1][0])
        hr = (lAr[0][0] - lAr[1][0])
        # add trapezian area
        area += (lIr - lIl) * (hl + hr) / 2

    return area


def get_remanence_from_lists(listAs, listIs):
    # bin where 0 is
    nid = next(i for i, bI in enumerate(listIs) if bI > 0.) - 1
    upperl = listAs[nid][0][0]
    lowerl = listAs[nid][1][0]
    upperr = listAs[nid + 1][0][0]
    lowerr = listAs[nid + 1][1][0]
    Il = listIs[nid]
    Ir = listIs[nid + 1]

    mrup  = (upperr - upperl) * (Ir - 0.) / (Ir - Il) + upperl
    mrlow = (lowerr - lowerl) * (Ir - 0.) / (Ir - Il) + lowerl

    return (mrup, mrlow)


def get_coercivity_from_lists(listAs, listIs, maxA):
    updone = False
    lowdone = False
    Icoerclow = -10000.
    Icoercup = 10000.
    for i, As in enumerate(listAs):
        dI = listIs[i] - listIs[i - 1]
        if (As[0][0] > 0.5 * maxA) and not updone:
            rightA = As[0][0]
            leftA  = listAs[i - 1][0][0]
            Icoercup = dI * (rightA - 0.5) / (rightA - leftA) + listIs[i - 1]
            updone = True
        if (As[1][0] > 0.5 * maxA) and not lowdone:
            rightA = As[1][0]
            leftA  = listAs[i - 1][1][0]
            Icoerclow = dI * (rightA - 0.5) / (rightA - leftA) + listIs[i - 1]
            lowdone = True
    return (Icoerclow, Icoercup)


def get_simdict(outfile):
    with open(os.path.join(os.path.split(outfile)[0], 'sim.yaml'), 'r') as f:
        simdict = yaml.load(f)
    foldertemplate = simdict['folderTemplate']
    simparameterkeys = utils.get_simparameters_from_template(foldertemplate)
    flatsimdict = utils.flatten_dictionary(simdict)
    outdict = {}
    for spkey in simparameterkeys:
        outdict[spkey] = flatsimdict[spkey]

    return outdict


def hysteresis(outfile, nIpoints=100, subsampling=1, plot=False, **kwargs):
    if kwargs:
        print("Found unnecessary parameters, ignoring {}".format(kwargs))
    # get results
    Ts, Is, As = get_data(outfile, subsampling=subsampling)

    listIs, listAs, maxA = get_lists(Is, As, nIpoints)

    analysisdict = {'As': listAs, 'Is': listIs}
    analysisdict['area'] = get_area_from_lists(listAs, listIs)
    analysisdict['remanenz'] = get_remanence_from_lists(listAs, listIs)
    analysisdict['coercivity'] = get_coercivity_from_lists(listAs, listIs,
                                                                        maxA)
    analysisdict['simdict'] = get_simdict(outfile)

    with open(os.path.join(os.path.split(outfile)[0], 'analysis'), 'w') as f:
        f.write(yaml.dump(analysisdict))

    if plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        upperAsmean = [A[0][0] for A in listAs]
        upperAsstd = [A[0][1] for A in listAs]
        lowerAsmean = [A[1][0] for A in listAs]
        lowerAsstd = [A[1][1] for A in listAs]
        with open(os.path.join(os.path.split(outfile)[0],
                                    'hysteresis.pdf'), 'w') as pdf:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.errorbar(listIs, upperAsmean, upperAsstd, fmt='bx')
            ax.errorbar(listIs, lowerAsmean, lowerAsstd, fmt='bx')
            ax.set_title('Hysteresis Curve')
            ax.set_xlabel('External Current')
            ax.set_ylabel('Active neurons')
            plt.savefig(pdf, format='pdf')


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv) == 4:
        hysteresis(outfile=sys.argv[1], nIpoints=int(sys.argv[2]),
                        subsampling=int(sys.argv[3]), plot=True)
    else:
        print("Don't know what to do.")
        print(sys.argv)
