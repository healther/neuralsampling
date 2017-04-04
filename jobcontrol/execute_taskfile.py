#! /usr/bin/env python

import multiprocessing as mp
import subprocess
import os
import sys
import datetime
import time

import utils


def execute_jobfile(jobfile):
    utils.touch(jobfile + '.start')
    try:
        with open(jobfile, 'r') as f:
            content = f.readlines()
        # strip added content from file
        # eta = content[0].strip()
        cwd = content[1].strip()
        content = content[2:]
        # recreate original file
        with open(jobfile + 'run', 'w') as f:
            f.write("".join(content))

        time.sleep(.1)

        print("".join(content))

        stdoutfile = open(jobfile + 'out', 'w')
        ret_value = subprocess.call(['bash', jobfile + 'run'], cwd=cwd,
                                     stdout=stdoutfile)
        utils.touch(jobfile + '.finish')
        if ret_value == 0:
            utils.touch(jobfile + '.success')
    except Exception as e:
        # FIXME: Improve error handling
        print("{} found exception {}".format(datetime.datetime.now(), e))
        utils.touch(jobfile + '.finish')


# read file with the task scripts
taskfile = sys.argv[1]
utils.touch(taskfile + 'started')
with open(taskfile, 'r') as f:
    jobfiles = [line.strip() for line in f]

nproc = int(os.getenv('SLURM_CPUS_ON_NODE', '1'))
pool = mp.Pool(nproc)
pool.map(execute_jobfile, jobfiles)
pool.close()
pool.join()
# for debug purposes use
# execute(jobfiles[0])
utils.touch(taskfile + 'finished')

directory = os.path.split(os.path.realpath(__file__))[0]
subprocess.call([os.path.join(directory, 'check_taskfile.py'), taskfile])
