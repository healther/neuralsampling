"""This module implements the different cluster platforms as classes.

Currently implemented are:
    - Local         for running the experiment locally
    - BwUni         for submitting jobs to the BWUniCluster

Implementations of additinal platforms have to at least override all
methods of ClusterBase. Consult the ClusterBase class for the intended
usage.
Further functionality should be implemented as private functions in
order to keep the experiment execution cluster agnostic.
"""
from __future__ import division, print_function
import abc
import multiprocessing as mp
import subprocess
import functools
import os
import uuid
import yaml
import sys
import time
import datetime

import misc
import control

class SlurmError(Exception):
    """Indicate an error with the slurm functions."""

    pass


class ClusterBase():
    """Implement the interface for cluster classes."""

    def __init__(self):
        """Initialise cluster instance.

        If applicable take environment configurations as parameters.
        """
        pass

    def run_jobs(self, folders, function_name, parameters={}):
        """Run function on all folders.

        Input:
            folders         list    list of folders of simulations to run
            function_name   string  module.function needs to be available for
                                    an import and take a single folder as the
                                    first argument, all further (optional)
                                    arguments can be provided in parameters
            parameters      dict    optional arguments for function
        """
        pass

    def wait_for_finish(self):
        """Wait for jobs to finish.

        Only important for distributed systems.
        """
        pass

    def ensure_success(self, retries):
        """Check for success of the jobs.

        Input:
            retries     int     number of attempts to reissue simulations

        Should provide an automatic restart of failed simulations.
        But must report which simulations have failed. Use discression
        to handle a reasonable amount of failures on the fly and reduce
        user intervention to a minimum.
        """
        pass


class Local(ClusterBase):
    """Process on local machine."""

    def __init__(self, n_cpus=1):
        """Process on local machine on n_cpus cores.

        Input:
            n_cpus  int     number of cpus to use on the local machine
        """
        self.use_n_cpus = n_cpus

    def run_jobs(self, folders, function_name, parameters={}):
        """Override ClusterBase check there for information."""
        self.function_name = function_name
        self.parameters = parameters
        module_name, fct_name = function_name.split('.')
        base_fct = getattr(__import__(module_name), fct_name)
        fct = functools.partial(base_fct, **parameters)
        self.folders = folders
        self.ret_values = []
        if self.use_n_cpus is 1:
            self.ret_values = []
            for folder in folders:
                ret_value = fct(folder)
                self.ret_values.append(ret_value)
        else:
            pool = mp.Pool(use_n_cpus)
            self.ret_values = pool.map(fct, folders)
            pool.close()
            pool.join()

    def wait_for_finish(self):
        """Override ClusterBase check there for information."""
        pass

    def ensure_success(self, retries=2):
        """Override ClusterBase check there for information."""
        failed_folders = [folder for folder, ret_value
                            in zip(self.folders, self.ret_values)
                            if not ret_value==0]
        for _ in range(retries):
            if failed_folders == []:
                return True
            self.run_jobs(failed_folders, self.function_name, self.parameters)
            self.wait_for_finish()
            failed_folders = [folder for folder, ret_value
                            in zip(self.folders, self.ret_values)
                            if not ret_value==0]
        else:
            return False


bwjobfile_content = """#!/bin/bash
#MSUB -V
#MSUB -l nodes={nodes}:ppn={processors_per_node}
#MSUB -l walltime={walltime}

source load_env.sh

echo {job_file}
python generate/cluster.py bwuni {job_file}.yaml {function_name} {parameterfilename}"""


class BwUni(ClusterBase):
    """Process on BWUniCluster."""

    def __init__(self, n_sims_per_job, nodes, processors_per_node, walltime,
            max_queue_size, generate_folder, wait_time=120., basejobname=None,
            cleanjobfiles=False,):
        """Process on BWUniCluster using multiple processors and nodes.

        Input:
            n_sims_per_job          int     number of simulations per job file
            nodes                   int     number of nodes to use per job
            processors_per_node     int     number of processors per node
            walltime                string  time string of the time limit of a single job
            max_queue_size          int     max number of jobs to be queue at one time
            generate_folder         string  folder in which to put the jobfiles
            wait_time               float   number of seconds to wait before attempting the next try
            basejobname             string  basename of the generated jobfiles
        """
        self.n_sims_per_job = n_sims_per_job
        self.nodes = nodes
        self.processors_per_node = processors_per_node
        self.walltime = walltime
        self.max_queue_size = max_queue_size
        self.generate_folder = generate_folder
        self.wait_time = wait_time
        self.basejobname = basejobname
        self.cleanjobfiles = cleanjobfiles

        misc.ensure_folder_exists(self.generate_folder)

        self.queued_jobs = {}
        self.failed_jobs = {}

    def run_jobs(self, folders, function_name, parameters={}):
        """Override ClusterBase check there for information."""
        self.arguments = folders
        self.jobfiles = self._generate_jobfiles(folders, function_name, parameters)
        time.sleep(15.)
        self._queue_jobs(self.jobfiles)
        print(self.queued_jobs)

    def wait_for_finish(self):
        """Override ClusterBase check there for information."""
        t0 = time.time()
        for jobid, _ in self.queued_jobs.iteritems():
            state = self._get_jobstate(jobid)
            while state in ['Idle', 'Running']:
                print("Waiting since {:07.1f} seconds for job {} to finish".format(time.time()-t0, jobid))
                time.sleep(self.wait_time)
                state = self._get_jobstate(jobid)

    def ensure_success(self, retries=2):
        """Override ClusterBase check there for information."""
        failed_jobs = self._find_failed_jobs()
        for _ in range(retries):
            if len(failed_jobs)!=0:
                self.failed_jobs.update(failed_jobs)
                self._queue_jobs(failed_jobs.itervalues())
                time.sleep(self.wait_time)
                self.wait_for_finish()
                failed_jobs = self._find_failed_jobs()
                print(failed_jobs)
            else:
                bsuccess = True
                break
        else:
            bsuccess = False

        print("All jobs completed")
        if self.cleanjobfiles:
            print("Cleaning not-failed jobfiles")
            self._clean_jobfiles()
            if len(self.failed_jobs)!=0:
                print("The following jobs failed to report success:")
                print(self.failed_jobs)
        return bsuccess

    def _queue_jobs(self, jobfiles):
        """Add jobs to queue, obeying self.max_queue_size."""
        for jobfile in jobfiles:
            if self._find_queue_size() < self.max_queue_size:
                jobid = subprocess.check_output(['msub', jobfile]).strip()
                self.queued_jobs.update({jobid: jobfile})
            else:
                time.sleep(self.wait_time)

    def _find_queue_size(self, retries=10):
        """Return current number of queued (running or idle) jobs."""
        try:
            showq_output = subprocess.check_output(['showq']).split()
            for _ in range(retries):
                if showq_output[-3]=='Total':   # check if last line is according to expecations
                    return int(showq_output[-1])
                showq_output = subprocess.check_output(['showq']).split()
            else:
                raise SlurmError("No valid 'showq' output found. Found instead: {}".format(showq_output))
        except:
            raise
            ### TODO: raise original error too?
            raise SlurmError("'showq' command failed.")

    def _generate_jobfiles(self, folders, function_name, parameters={}):
        """Return list of jobfilenames."""
        if self.basejobname==None:
            self.basejobname = str(uuid.uuid1())
        parameterfilename = os.path.join(self.generate_folder, 'parameters_'+self.basejobname)
        with open(parameterfilename, 'w') as f:
            yaml.dump(parameters, f)

        n_job_files = int(len(folders)/self.n_sims_per_job)+1
        print("{}: Generating {} jobfiles for {} simulations.".format(datetime.datetime.now(), n_job_files, len(folders)))
        job_files = []
        for i in range(n_job_files):
            job_filename = os.path.join(self.generate_folder,
                                'job_{}_{:05d}'.format(self.basejobname, i))
            job_folderlist = folders[i*self.n_sims_per_job:(i+1)*self.n_sims_per_job]
            with open(job_filename+'.yaml', 'w') as f:
                yaml.dump(job_folderlist, f)
            moab_content = bwjobfile_content.format(nodes=self.nodes,
                                processors_per_node=self.processors_per_node,
                                walltime=self.walltime,
                                job_file=job_filename,
                                function_name=function_name,
                                parameterfilename=parameterfilename)
            with open(job_filename+'.moab', 'w') as f:
                f.write(moab_content)
            job_files.append(job_filename+'.moab')

        return job_files

    def _get_jobstate(self, jobid, attempt=0):
        """Return the state of jobid {Running, Idle, Removed, Completed}."""
        try:
            r = subprocess.check_output(['checkjob', jobid])
            state = r.split("State:")[1].split()[0]
            return state
        except:
            if attempt<10:
                time.sleep(self.wait_time)
                return self._get_jobstate(jobid, attempt=attempt+1)
            else:
                raise

    def _clean_jobfiles(self):
        """Remove all jobfiles, that did not fail."""
        for jobid, jobfile in self.queued_jobs.iteritems():
            if not self.failed_jobs.has_key(jobid):
                try:
                    os.remove('job_uc1_{}.out'.format(jobid))
                except OSError as e:
                    if e.errno==2:
                        print("job_uc1_{}.out was already missing.".format(jobid))
                    else:
                        raise
                os.remove(jobfile)
                os.remove(jobfile.replace('.moab', '.yaml'))

    def _find_failed_jobs(self):
        """Probe all queued_jobs's status."""
        ### TODO: encapsulate checkjob better
        failed_jobs = {}
        for jobid, jobfile in self.queued_jobs.iteritems():
            try:
                state = self._get_jobstate(jobid)
                if state=="Completed":
                    r = subprocess.check_output(['checkjob', jobid])
                    completion_code = r[r.find('Completion Code:'):].split()[2]
                    if completion_code is not '0':
                        failed_jobs.update({jobid: jobfile})
                elif state=="Removed":
                    failed_jobs.update({jobid: jobfile})
            except:
                raise
                raise SlurmError("'checkjob' failed for jobid {}".format(jobid))
        return failed_jobs


def run_job_bwuni(folderfile, function_name, argument_file=None):
    """Wrapper for job_file execution of function_name on folders."""
    print("{} Started to apply {} on {}".format(datetime.datetime.now(), function_name, folderfile))
    if argument_file != None:
        parameters = yaml.load(open(argument_file, 'r'))
    else:
        parameters = {}

    base_fct = control.get_function_from_name(function_name)
    sim_fct = functools.partial(base_fct, **parameters)
    folders = yaml.load(open(folderfile, 'r'))
    nproc = int(os.getenv('SLURM_NPROCS', '1'))
    pool = mp.Pool(nproc)
    ret_values = pool.map(sim_fct, folders)
    pool.close()
    pool.join()
    #for f in folders:
    #    print(sim_fct(f))
    print("{} Finished to apply {} on {}".format(datetime.datetime.now(), function_name, folderfile))
    print(ret_values)
    return [folder for folder, ret_value in zip(folders, ret_values)
                        if ret_value is not 0]


if "__main__"==__name__:
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())

    elif len(sys.argv)==4:
        if sys.argv[1]=='bwuni':
            print(run_job_bwuni(folderfile=sys.argv[2],
                        function_name=sys.argv[3]))
    elif len(sys.argv)==5:
        if sys.argv[1]=='bwuni':
            print(run_job_bwuni(folderfile=sys.argv[2],
                        function_name=sys.argv[3],
                        argument_file=sys.argv[4]))
