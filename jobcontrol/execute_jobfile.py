#! /usr/bin/env python

import multiprocessing as mp
import subprocess
import os
import sys
import datetime
import time

import utils


def readd(jobfile):
    with open(jobfile, 'r') as f:
        content = f.readlines()
    print(jobfile, content)
    eta = content[0].strip()
    cwd = content[1].strip()
    content = content[2:]
    with open(jobfile + 'run', 'w') as f:
        f.write("".join(content))
    subprocess.call(['jobcontrol.py', 'a', jobfile, eta, cwd])


def execute(jobfile):
    utils.touch(jobfile + '.start')
    try:
        with open(jobfile, 'r') as f:
            content = f.readlines()
        print(jobfile, content)
        # eta = content[0].strip()
        cwd = content[1].strip()
        content = content[2:]
        with open(jobfile + 'run', 'w') as f:
            f.write("".join(content))

        time.sleep(.1)

        stdoutfile = open(os.devnull, 'wb')
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
with open(taskfile, 'r') as f:
    jobfiles = [line.strip() for line in f]

nproc = int(os.getenv('SLURM_NPROCS', '1'))
pool = mp.Pool(nproc)
pool.map(execute, jobfiles)
pool.close()
pool.join()
# execute(jobfiles[0])

readded = 0
for jobfile in jobfiles:
    if not os.path.exists(jobfile):
        print("Something bad happened, can't find {} anymore.".format(jobfile))
    elif not os.path.exists(jobfile + '.start'):
        print("Never started {} for some reason. Restaging".format(jobfile))
        readd(jobfile)
        readded += 1
    elif (os.path.exists(jobfile + '.start') and
            not os.path.exists(jobfile + '.finish')):
        print("{}, did not finish for some reason. "
                                    "Restaging".format(jobfile))
        readd(jobfile)
        readded += 1
    elif (os.path.exists(jobfile + '.start') and
            os.path.exists(jobfile + '.finish') and
            not os.path.exists(jobfile + '.success')):
        print("{}, did not succeed for some reason. "
                                    "Do not restage.".format(jobfile))
    else:
        print("Finished {} successfully (return code zero)".format(jobfile))
        os.remove(jobfile + '.start')
        os.remove(jobfile + '.finish')
        os.remove(jobfile + '.success')
        os.remove(jobfile + 'run')
        os.remove(jobfile)

os.remove(taskfile)
print("Readded {} out of {}.".format(readded, len(jobfiles)))
