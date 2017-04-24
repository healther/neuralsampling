import matplotlib.pyplot as plt
import yaml
import numpy as np
import os
import sys

from matplotlib.backends.backend_pdf import PdfPages


def isinlist(id_list, list_of_lists):
    for i, li in zip(id_list, list_of_lists):
        if i not in li:
            return False
    return True


def reduce_data(collected_file_name, restrictions, order):
    d = yaml.load(open(collected_file_name, 'r'))

    reduced_data = []
    for k, v in d.iteritems():
        if isinlist(k, restrictions):
            # reduced_dict[k] = v
            dataline = []
            for o in order:
                if o[0] == 'key':
                    dataline.append(k[o[1]])
                elif o[0] == 'value':
                    dataline.append(v[o[1]])
            reduced_data.append(dataline)

    return reduced_data


def scatter_plot(collected_file_name,
        restrictions, order, bundleind, bundels,
        xlabel, ylabel, xid, yid,
        plotname, plotfolder):

    reduced_data = reduce_data(collected_file_name)
    xdata = len(bundels) * []
    ydata = len(bundels) * []

    for rd in reduced_dict.iteritems():
        xdata[bundels.index(rd[bundelind])].append(rd[xid])
        ydata[bundels.index(rd[bundelind])].append(rd[yid])

    with PdfPages(os.path.join(plotfolder, plotname)) as pdf:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for b in bundels:
            ax.scatter(xdata, ydata, label=str(b))
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        plt.savefig(pdf, format='pdf')


def colormap(collected_file_name,
        restrictions, order,
        xlabel, ylabel, zlabel, xid, yid, zid,
        plotname='pp.pdf', plotfolder='plots'):
    """Plots a 2d colormap

    Input:
        collected_file_name     string  name of the yaml file with keys
                                            _-seperated arguments and values
                                            as means and std
        xlabel                  string  key that should be plotted on the
                                            xlabel
        ylabel                  string  key that should be plotted on the
                                            ylabel
        zlabel                  string  key that should select the color of
                                            the patch
        restrictions            dict    dictionary of {argument: iterable} with
                                            iterable containing all applicable
                                            values for argument
        plotname                string  filename of the output pdf file
        plotfolder              string  folder in which to put the output
    Output:
        fig, ax
    """

    reduced_data = reduce_data(collected_file_name, restrictions, order)

    xvalues = []
    yvalues = []
    zvalues = []

    for rd in reduced_data:
        xvalues.append(rd[xid])
        yvalues.append(rd[yid])
        zvalues.append(rd[zid])

    unique_x = sorted(list(set(xvalues)))
    unique_y = sorted(list(set(yvalues)))
    n_slices = len(unique_x) * len(unique_y)

    if n_slices < len(zvalues):
        zvals = n_slices * [0.]
        zfreqs = n_slices * [0]

        for x, y, z in zip(xvalues, yvalues):
            ind = len(unique_x) * unique_y.index(y) + unique_x.index(x)
            zvals[int] += z
            zfreqs[int] += 1

        for i in range(len(zvals)):
            zvals[i] = zvals[i] / zfreqs[i]

    zresults = np.zeros((len(unique_x), len(unique_y)))
    for x, y, z in zip(xvalues, yvalues, zvals):
        zresults[unique_x.index(x), unique_y.index(y)] = z

    with PdfPages(os.path.join(plotfolder, plotname)) as pdf:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        cax = ax.pcolor(zresults)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        cbar = fig.colorbar(cax, label=zlabel)
        plt.savefig(pdf, format='pdf')

    return fig, ax

if __name__ == '__main__':
    if len(sys.argv) == 1:
        import doctest
        print(doctest.testmod())
