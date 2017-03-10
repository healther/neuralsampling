"""bwuni submission"""
import time
import subprocess

import glob
import os
import sys
import inspect
# crazy hack to be able to import modules from the parent...
currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import jobcontrol
import utils

stub = """#!/bin/bash

#MSUB -l nodes=1:ppn={ncpus}
#MSUB -l walltime={eta}

python {jobcontrolfolder}/execute_taskfile.py {tasklistfile} &&

/usr/bin/rm {tasklistfile}*
"""


def clean_taskfolder(submittedfolder):
    additional_tasks = []
    for f in os.listdir(submittedfolder):
        if 'moab' in f:
            if not f.endswith('moab'):
                taskname, jobid = f.split('.moab')
                jobinfo = subprocess.check_output(['checkjob', jobid])
                stateline = [line for line in jobinfo.split('\n')
                                            if 'State: ' in line]
                if not stateline[0].endswith('Running'):
                    additional_tasks.append(taskname)
                for ff in glob.glob(taskname+'*'):
                    os.remove(ff)
    return additional_tasks


def submit_task(config, tasklistfile):
    """

    Input:
        config:     dict with the configuration of jobcontrol
        tasks:        tuple with
                            list of taskfiles to be executed
                            eta in seconds of the taskfiles
    """

    ncpus = config['ncpus']
    eta = int(float(config['maxcpuhours'])*3600.)
    jobcontrolfolder = utils.get_parentdirectory(__file__)

    content = stub.format(ncpus=ncpus, eta=eta,
                            tasklistfile=tasklistfile,
                            jobcontrolfolder=jobcontrolfolder)
    moabfile = os.path.join(jobcontrol.jobtasklists, tasklistfile + '.moab')
    with open(moabfile, 'w') as f:
        f.write(content)

    # ensure that the filesystem is up to date
    time.sleep(1.)

    try:
        jobid = subprocess.check_output(['msub', moabfile])
    except subprocess.CalledProcessError as e:
        jobid = e.output
        raise

    utils.touch(moabfile + jobid.strip())
