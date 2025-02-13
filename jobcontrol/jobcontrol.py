#! /usr/bin/env python

"""This module provides a simple task scheduler

"""
from __future__ import division, print_function
import subprocess
import os
import yaml
import sys
import datetime
import errno
import shutil

import utils
import cluster.bwuni
import cluster.heidelberg

jobfolder = os.getenv('JOB_FOLDER', os.path.expanduser('~/.jobfolder'))
utils.ensure_exist(jobfolder)
jobconfigfile = os.path.join(jobfolder, 'config.yaml')
# TODO: fix empty config
try:
    config = yaml.load(open(jobconfigfile, 'r'))
except IOError as e:
    if e.errno == errno.ENOENT:
        config = {'maxcpuhours': .5, 'ncpus': 1, 'slurmmode': 'local'}
        yaml.dump(config, open(jobconfigfile, 'w'))
    else:
        raise
# config specification:
#   maxhours    number of hours a job must not exceed
#   ncpus       number of cpus a job may allocate
#   slurmmode   local, bwuni, heidelberg
jobstage  = os.path.join(jobfolder, 'stage')
utils.ensure_exist(jobstage)
jobsubmmited = os.path.join(jobfolder, 'submitted')
utils.ensure_exist(jobsubmmited)
jobtasklists = os.path.join(jobfolder, 'tasklists')
utils.ensure_exist(jobtasklists)
donetasksfolder = os.path.join(jobfolder, 'donetasks')
utils.ensure_exist(donetasksfolder)


# job specification
# a time estimate and a bash-script containing all the information


def action_reset(args):
    i = 0
    for filename in os.listdir(jobsubmmited):
        if filename.endswith('.success'):
            basename = os.path.join(jobsubmmited, filename.split('.')[0])
            endings = ['run', '.start', '.finish', '.success']
            i += 1
            for end in endings:
                filepath = basename + end
                if not os.path.exists(filepath):
                    print("Didn't find {}, something "
                            "weird happened".format(filepath))
                else:
                    os.remove(filepath)
            os.remove(basename)
    print("Removed {} completed jobs".format(i))
    if args[0] == 'hard':
        for filename in os.listdir(jobsubmmited):
            if not (filename.endswith('.start') or
                    filename.endswith('.finish') or
                    filename.endswith('.success') or
                    filename.endswith('out') or
                    filename.endswith('run')):
                shutil.move(os.path.join(jobsubmmited, filename), jobstage)
            elif not filename.endswith('out'):
                os.remove(os.path.join(jobsubmmited, filename))
        for dirpath, dirnames, filenames in os.walk(jobtasklists):
            for filename in filenames:
                os.remove(os.path.join(dirpath, filename))


def action_config(args):
    if len(args) == 0:
        print(config)
        print("JOB_FOLDER", jobfolder)
    else:
        key = args[0].split('.')
        if len(args) == 1:
            print("Current value of {} is {}".format(args[0],
                                                utils.get_value(config, *key)))
        elif len(args) == 2:
            utils.update_dict(config, args[1], *key)
            with open(jobconfigfile, 'w') as configfile:
                configfile.write(yaml.dump(config))
            print("New value of {} is {}".format(args[0],
                                                utils.get_value(config, *key)))


def _package_jobs_to_tasks():
    cpusecseta = int(config['ncpus']) * float(config['maxcpuhours']) * 3600.
    tasks = []

    filenames = os.listdir(jobstage)
    print("Found {} jobs to execute.".format(len(filenames)))

    currenteta = 0.
    currenttask = []
    for i, f in enumerate(filenames):
        if i % 10000 == 0:
            print("{} {}/{} done".format(datetime.datetime.now(),
                                                i, len(filenames)))

        eta = float(f.split('_')[1])

        currenttask.append(f)
        currenteta += eta
        if currenteta > cpusecseta:
            tasks.append((currenttask, currenteta))
            currenttask = []
            currenteta = 0.

    if len(currenttask) > 0:
        tasks.append((currenttask, currenteta))
    print("Packaged them to {} tasks.".format(len(tasks)))

    return tasks


def _submit_task(task):
    """

    task: tuple with
            - list of staged files
            - eta
    """
    unique_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    taskfilename = os.path.join(jobtasklists, unique_name)
    with open(taskfilename, 'w') as f:
        for jobfile in task[0]:
            shutil.move(os.path.join(jobstage, jobfile), jobsubmmited)
            #  shutil.copy(os.path.join(jobstage, jobfile), jobsubmmited)
            f.write(os.path.join(jobsubmmited,
                                 os.path.split(jobfile)[1]) + '\n')
    return taskfilename


def action_execute(args):
    tasks = _package_jobs_to_tasks()
    taskfilenames = [_submit_task(task) for task in tasks]

    if config['slurmmode'] == 'local':
        for f in os.listdir(jobsubmmited):
            if not f.endswith('started') and not f.endswith('finished'):
                # may restart aready running tasks use with care.
                if not os.path.exists(f + 'finished'):
                    taskfilenames.prepend(os.path.join(jobsubmmited, f))
                    print("Added {} as an failed task".format(f))
        os.environ['SLURM_NPROCS'] = '1'
        for taskfilename in taskfilenames:
            # print(taskfilename)
            subprocess.call([os.path.join(
                                os.path.split(os.path.realpath(__file__))[0],
                                'execute_taskfile.py'), taskfilename])
    elif config['slurmmode'] == 'bwuni':
        # resubmit tasks
        # taskfilenames = cluster.bwuni.clean_taskfolder(jobtasklists) +
        #                                     taskfilenames
        for taskfilename in taskfilenames:
            cluster.bwuni.submit_task(config, taskfilename)
    elif config['slurmmode'] == 'heidelberg':
        for taskfilename in taskfilenames:
            cluster.heidelberg.submit_task(config, taskfilename)


def action_add(args):
    unique_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    try:
        with open(args['script'], 'r') as original:
            data = original.read()
    except IOError as e:
        if e.errno == errno.ENOENT:
            print("{} does not exists. Please specify an existing "
                            "script.".format(args['script']))
            return

    cwd = args['cwd']
    if not os.path.isdir(cwd):
        raise OSError(errno.ENOTDIR, "The specified working directory does "
                            "not exist. Didn't add {}".format(args['script']))
    eta = args['eta']
    try:
        eta = str(int(float(eta) + 1.))
    except ValueError:
        raise ValueError("Eta must be specified in seconds.")

    with open(os.path.join(jobstage, unique_name + '_' + eta), 'w') as staged:
        staged.write(str(eta) + '\n' + cwd + '\n' + data)


def parse_args_and_execute(argv=sys.argv):
    argv = [arg.decode('utf-8') for arg in argv]

    try:
        head = argv[1]
        tail = argv[2:]
    except IndexError:
        print("Find help with 'jobcontrol.py h'")
        return

    if head in ('a', 'add'):
        fn = action_add
        args = {'script': tail[0], 'cwd': tail[1], 'eta': float(tail[2])}

    elif head in ('e', 'execute'):
        fn = action_execute
        args = {}

    elif head in ('c', 'config'):
        fn = action_config
        args = tail

    elif head in ('r', 'reset'):
        fn = action_reset
        args = tail

    else:
        print("""This should be a helpful message.""")
        return

    fn(args)


if __name__ == '__main__':
    parse_args_and_execute(sys.argv)
