"""This module implements the different cluster platforms as classes"""

import abc
import multiprocessing as mp
import subprocess
import functools

class SlurmError(Exception):
    pass


class ClusterBase():
    """Implement the interface for cluster classes"""
    def __init__(self):
        pass

    def run_jobs(self, folders, function):
        """Use to execute function on all folders."""
        pass

    def wait_for_finish(self):
        """Wait for asynchrone jobs to finish."""
        pass

    def ensure_success(self, retries):
        """Check for success of the jobs."""
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
        """Run function on all folders.

        Input:
            folders         list    list of folders of simulations to run
            function_name   string  module.function needs to take as argument a folder
            parameters      dict    parameters for function expect folder
        """
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
        """Does nothing."""
        pass

    def ensure_success(self, retries=2):
        """Check return values and retries if non-zero.

        Input:
            transform_function_name     string  module.transform_function
            retries                     int     maximal number of retries

        Output:
            success     bool
        """
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

module load yaml-cpp-0.5.3-gcc-6.2.0-2klkoil
module load bzip2-1.0.6-gcc-6.2.0-hzvvkma
module load ncurses-6.0-gcc-6.2.0-q7ibucr
module load zlib-1.2.8-gcc-6.2.0-sw5a7dc
module load openssl-1.0.2j-gcc-6.2.0-iuqx65o
module load readline-6.3-gcc-6.2.0-o2e7g36
module load sqlite-3.8.5-gcc-6.2.0-kd7qe6o
module load python-2.7.12-gcc-6.2.0-csrr54f
module load py-pyyaml-3.11-gcc-6.2.0-2kgymdu

echo {job_file}
python generate/cluster.py bwuni {job_file}.yaml {transform_function_name}"""


class BwUni(ClusterBase):
    def __init__(self, n_sims_per_job, nodes, processors_per_node, walltime,
            max_queue_size, generate_folder):
        self.n_sims_per_job = n_sims_per_job
        self.nodes = nodes
        self.processors_per_node = processors_per_node
        self.walltime = walltime
        self.max_queue_size = max_queue_size
        self.generate_folder = generate_folder

        self.queued_jobs = {}
        self.failed_jobs = {}

    def run_jobs(self, folders, function):
        self.arguments = folders
        self.jobfiles = self._generate_jobfiles(folders, function)
        self.queue_jobs(self.jobfiles)

    def queue_jobs(self, jobfiles):
        for jobfile in jobfiles:
            if self._find_queue_size() < self.max_queue_size:
                jobid = subprocess.check_output(['msub', jobfile]).strip()
                self.queued_jobs.update({jobid: jobfile})
            else:
                time.sleep(60.)


    def _find_queue_size(self, retries=10):
        try:
            showq_output = subprocess.check_output(['showq']).split()
            for _ in range(retries):
                if showq_output[-3:-1]==['Total', 'jobs']:
                    return int(showq_output[-1])
            else:
                raise SlurmError("No valid 'showq' output found.")
        except:
            ### raise original error too?
            raise SlurmError("'showq' command failed.")

    def _generate_jobfiles(self, folders, transform_function_name):
        n_job_files = int(len(folders)/self.n_sims_per_job)+1
        uid = uuid.uuid()
        job_files = []
        for i in range(n_job_files):
            job_filename = os.path.join(generate_folder, 'job_{}_{:05d}'.format(uid, i))
            job_folderlist = folders[i*self.n_sims_per_job:(i+1)*self.n_sims_per_job]
            with open(job_filename+'.yaml', 'w') as f:
                yaml.dump(job_folderlist, f)
            moab_content = bwjobfile_content.format(nodes=self.nodes,
                                processors_per_node=self.processors_per_node,
                                walltime=walltime,
                                jobfile=job_filename,
                                transform_function_name=transform_function_name)
            with open(job_filename+'.moab', 'w') as f:
                f.write(moab_content)
            job_files.append(job_filename+'.moab')

        return job_files

    def ensure_success(self, retries=2):
        failed_jobs = self._find_failed_jobs()
        for _ in range(retries):
            if failed_jobids != []:
                self.failed_jobs.update(failed_jobs)
                self.queue_jobs(failed_jobs.itervalues())
                failed_jobs = self._find_failed_jobs()
            else:
                return True
        else:
            return False

    def _find_failed_jobs(self):
        failed_jobs = {}
        for jobid, jobfile in self.queued_jobs.iteritems():
            try:
                r = subprocess.check_output(['checkjob', jobid])
                return_code = r[r.find('Completion Code:'):].split()[2]
                if return_code is not '0':
                    failed_jobs.update({jobid: jobfile})
            except:
                raise SlurmError("'checkjob' failed for jobid {}".format(jobid))
        return failed_jobs


def run_job_bwuni(folderfile, transform_function_name):
    sim_fct = functools.partial(control.simulate, transform_function_name=transform_function_name)
    folders = yaml.load(open(folderfile, 'r'))
    nproc = int(os.getenv('SLURM_NPROCS', '1'))
    pool = mp.Pool(nproc)
    ret_values = pool.map(sim_fct, folders)
    pool.close()
    pool.join()

    return [folder for folder, ret_value in zip(folders, ret_values)
                        if ret_value is not 0]


if "__main__"==__name__:
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv)==4:
        if sys.argv[1]=='bwuni':
            print(run_job_bwuni(folderfile=sys.argv[2],
                        transform_function_name=sys.argv[3]))