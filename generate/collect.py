"""This module provides functionality for (analysed) data aggregation.

All functions operate on a folder level and either look for
analysis_output or output files.
In case of not finding those files an appropriate error is raised.

TODO: Multicore support
"""

import os
from collections import deque
import yaml
import numpy as np

import misc



def _get_template(folder):
    d = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    template = d['sim_folder_template']
    return template


def singlefile(folders, targetfolder, targetfile):
    misc.ensure_folder_exists(targetfolder)
    outfile = os.path.join(targetfolder, targetfile)
    output = {}
    for folder in folders:
        key = tuple(folder.replace(os.sep, '_').split('_'))
        with open(os.path.join(folder, 'analysis_output'), 'r') as f:
            value = f.read()
        output[key] = value

    template = _get_template(folder)
    with open(os.path.join(targetfolder, targetfile), 'w') as f:
        yaml.dump({'template': template, 'data': output}, f)


if __name__ == '__main__':
    import doctest
    print(doctest.testmod())

