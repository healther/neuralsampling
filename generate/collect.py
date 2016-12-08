"""This module provides functionality for (analysed) data aggregation.

All functions operate on a folder level and either look for
analysis_output or output files.
In case of not finding those files an appropriate error is raised.

TODO: Multicore support
"""

import os
from collections import deque
import datetime
import yaml
import numpy as np

import misc



def _get_template(folder):
    """Return the folder template of the folderstring."""
    d = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    template = d['sim_folder_template']
    return template


def singlefile(folders, targetfolder, targetfile):
    """Collect the analysis results of all folders.

    Input:
        folders         list
        targetfolder    string  folder in which to output the collected results
        targetfile      string  name of the collected results

    Outputs:
        dict    - template: string
                - data:     collected analysis output {folder: folderdata}
    """
    misc.ensure_folder_exists(targetfolder)
    outfile = os.path.join(targetfolder, targetfile)
    output = {}
    template = None
    for i,folder in enumerate(folders):
        key = tuple(folder.replace(os.sep, '_').split('_'))
        try:
            value = yaml.load(open(os.path.join(folder, 'analysis_output'), 'r'))
            output.update(value)
            if template==None:
                template = _get_template(folder)
        except IOError as e:
            if e.errno==2:
                ## File not existing -> marking data as missing
                output[key] = None
            else:
                raise
        if i%1000==0:
            print("{} Collected: {5.1f}%".format(datetime.datetime.now(), i*100./len(folders)))

    with open(os.path.join(targetfolder, targetfile), 'w') as f:
        yaml.dump({'template': template, 'data': output}, f)


def collect_results_caller(args):
    """Wrapper for multiprocessing pool calls."""
    collect_results(**args)


def collect_results(folders, analysis_function, collected_file):
    """Call analysis_function on all folders and dumps results into collected_file."""
    collected = {}
    for f in folders:
        collected.update(analysis_function( f ))

    with open(collected_file, 'w') as f:
        yaml.dump(collected, f)



if __name__ == '__main__':
    import doctest
    print(doctest.testmod())

