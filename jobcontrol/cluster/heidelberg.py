"""heidelberg submissions"""
import subprocess
import os
import inspect
import sys

# crazy hack to be able to import modules from the parent...
currentdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
# import jobcontrol
import utils


def submit_task(config, tasklistfile):
    """
        Input:
            config:     dict with the configuration of jobcontrol
            tasks:      tuple with
                            list of taskfiles to be executed
                            eta in seconds of the taskfiles
    """

    jobcontrolfolder = utils.get_parentdirectory(__file__)
    ncpus = config['ncpus']

    jobcommand = "python {jobcontrolfolder}/execute_taskfile.py {tasklistfile}"
    jobcommand = jobcommand.format(jobcontrolfolder=jobcontrolfolder,
                                    tasklistfile=tasklistfile)
    subprocess.check_output(['sbatch', '-c', ncpus, '-p', 'simulation',
                                '--wrap', jobcommand])
