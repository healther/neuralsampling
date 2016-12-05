
import matplotlib.pyplot as plt
import yaml
import numpy as np
import os
import sys

from matplotlib.backends.backend_pdf import PdfPages


def colormap(collected_file_name, xlabel, ylabel, zlabel, restrictions, plotname='pp.pdf', plotfolder='plots'):
    """Plots a 2d colormap

    Input:
        collected_file_name     string  name of the yaml file with keys
                                            _-seperated arguments and values as means and std
        xlabel                  string  key that should be plotted on the xlabel
        ylabel                  string  key that should be plotted on the ylabel
        zlabel                  string  key that should select the color of the patch
        restrictions            dict    dictionary of {argument: iterable} with
                                            iterable containing all applicable values for argument
        plotname                string  filename of the output pdf file
        plotfolder              string  folder in which to put the output
    Output:
        fig, ax
    """
    d = yaml.load(open(collected_file_name, 'r'))

    print(len(d))

    xvalues = []
    yvalues = []
    zvalues = []

    for k,v in d.iteritems():
        _, _, randomtype, tau, w, updaterandomseed, initialactivity, initialrandomseed = k.split('_')
        kdict = {'randomtype': randomtype, 'tau': int(tau), 'weight': float(w),
                    'updaterandomseed': int(updaterandomseed),
                    'initialactivity': float(initialactivity), 'initialrandomseed': int(initialrandomseed)}
        try:
            if np.prod([kdict[kk] in vv for kk,vv in restrictions.iteritems()]):
                xvalues.append(kdict[xlabel])
                yvalues.append(kdict[ylabel])
                zvalues.append(v['mean'])
        except TypeError as e:
            print("Restrictions must be a dictionary of {argument: iterable} with iterable containing all valid values for the argument.")
            raise

    unique_x = list(set(xvalues))
    unique_y = list(set(yvalues))
    if len(unique_x)*len(unique_y)!=len(zvalues):
        xys = []
        zs = []

        for x, y, z in zip(xvalues, yvalues, zvalues):
            if (x,y) in xys:
                ind = xys.index((x,y))
                zs[ind].append(z)
            else:
                xys.append((x,y))
                zs.append([z])

        xvalues = [x for x, y in xys]
        yvalues = [y for x, y in xys]
        zvalues = [np.mean(z) for z in zs]
        print(len(zs[0]))

        zresults = np.zeros((len(unique_x), len(unique_y)))
        for x, y, z in zip(xvalues, yvalues, zvalues):
            zresults[unique_x.index(x), unique_y.index(y)] = z


    with PdfPages(os.path.join(plotfolder, plotname)) as pdf:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_xscale('log')
        # cax = ax.scatter(xvalues, yvalues, c=zvalues, s=100, marker='s')
        # cbar = fig.colorbar(cax)
        cax = ax.pcolorfast([0]+unique_x, [0]+unique_z, zresults)
        cbar = fig.colorbar(cax)
        #X, Y = np.meshgrid(unique_x, unique_y)
        #Z = [ [ zvalues[xys.index((xx,yy))] for xx, yy in zip(x,y)  ] for x,y in zip(X,Y) ]
        #ax.contour( X, Y, Z)
        plt.savefig(pdf, format='pdf')

    return fig, ax

if __name__ == '__main__':
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())
