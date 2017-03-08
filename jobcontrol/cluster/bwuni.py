"""bwuni submission"""
import time
import subprocess

from .. import jobcontrol
from .. import utils

stub = """#!/bin/bash

#MSUB -l nodes=1:ppn={ncpus}
#MSUB -l walltime={eta}

{jobcontrolfolder}/execute_taskfile.py {tasklistfile}
{jobcontrolfolder}/check_taskfile.py {tasklistfile}

rm {tasklistfile}
"""


def submit_job(config, tasklistfile):
    """

    Input:
        config:     dict with the configuration of jobcontrol
        tasks:        tuple with
                            list of taskfiles to be executed
                            eta in seconds of the taskfiles
    """

    ncpus = config['ncpus']
    eta = config['maxhours']
    jobcontrolfolder = utils.get_parentdirectory(__file__)

    content = stub.format(ncpus=ncpus, eta=eta, tasklistfile=tasklistfile,
                            jobcontrolfolder=jobcontrolfolder)
    with open(jobcontrol.jobtasklists + '.moab', 'w') as f:
        f.write(content)

    # ensure that the filesystem is up to date
    time.sleep(1.)

    subprocess.call(['msub', jobcontrol.jobtasklists + '.moab'])
