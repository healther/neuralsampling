"""bwuni submission"""
import time
import subprocess

from jobcontrol import jobtasklists

stub = """#!/bin/bash

#MSUB -l nodes=1:ppn={ncpus}
#MSUB -l walltime={eta}

jobexecute {tasklistfile}

rm {tasklistfile}
"""


def submit_job(config, tasklistfile):
    """

    Input:
        config:     dict with the configuration of jobcontrol
        tasks:        tuple with
                            list of jobfiles to be executed
                            eta in seconds of the jobfiles
    """

    ncpus = config['ncpus']
    eta = config['maxhours']

    content = stub.format(ncpus=ncpus, eta=eta, tasklistfile=tasklistfile)
    with open(jobtasklists + '.moab', 'w') as f:
        f.write(content)

    # ensure that the filesystem is up to date
    time.sleep(1.)

    subprocess.call(['msub', jobtasklists + '.moab'])
