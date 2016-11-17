
import yaml
import os
import subprocess
import sys
import multiprocessing as mp
import datetime
import numpy as np

import config
import misc
import weights

moab_stub = """#!/bin/bash
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

python generate/control.py {job_file}
"""


def experiment(dictionary, bgenerate=True, generate_folder='tmp', brun=False):
    print("{}: Extracting onetime information".format(datetime.datetime.now()))
    replacements = dictionary.pop("replacements")
    sim_folder_template = dictionary.pop("sim_folder_template")
    executable_configuration = dictionary.pop("exec_conf")
    dictionary.pop('type')

    ### generate folders
    print("{}: Expanding input dictionary according to {} rules".format(datetime.datetime.now(), len(replacements)))
    if bgenerate:
        print("    Generating {} simulation files".format(np.prod([len(r) for k, r in replacements.iteritems()])))
    folders = []
    for ed in config.expanddict(dictionary, replacements):
        d = misc.flatten_dictionary(ed)
        folder = sim_folder_template.format(**d)
        if bgenerate:
            misc.ensure_folder_exists(folder)

            ed['outfile'] = os.path.join(folder, 'output')
            ed['path'] = folder
            ed['type'] = 'Simulation'

            with open(folder+os.sep+'sim.yaml', 'w') as f:
                yaml.dump(ed, f)

        folders.append(folder)

    ### generate run files
    if bgenerate:
        n_sims_per_job = executable_configuration["n_sims_per_job"]
        n_job_files = int(len(folders)/n_sims_per_job) + 1
        print("{}: Generating {} slurm-jobfiles for {} simulations".format(datetime.datetime.now(), n_job_files, len(folders)))

        # unique base name
        current_time = datetime.datetime.now()
        moab_files = []
        misc.ensure_folder_exists(generate_folder)
        for i in range(n_job_files):
            job_file = generate_folder + os.sep + str(current_time).strip() + \
                    '{}.yaml'.format(i).replace(" ", "_")
            job_dictionary = {'type': "Run", 'sim_files': [os.path.join(sf, 'sim.yaml')
                    for sf in folders[i*n_sims_per_job:(i+1)*n_sims_per_job]]}
            with open(job_file, 'w') as f:
                yaml.dump(job_dictionary, f)

            moab_file = job_file[:-5] + '.moab'
            executable_configuration["job_file"] = job_file
            with open(moab_file, 'w') as f:
                f.write(moab_stub.format(**executable_configuration))
            moab_files.append(moab_file)

    if brun:
        print("{}: Spawning slurm jobs".format(datetime.datetime.now()))
        for moab_file in moab_files:
            subprocess.call(["msub", moab_file])

def run(dictionary):
    nproc = int(os.getenv('SLURM_NPROCS', '1'))
    pool = mp.Pool(nproc)
    pool.map(simulation, dictionary["sim_files"])
    pool.close()
    pool.join()

def simulation(dictionary_file, check=False):
    dictionary = yaml.load(open(dictionary_file, 'r'))
    if check:
        raise NotImplementedError("TODO: Implement a sanity check for input files")

    run_dictionary = make_rundictionary(dictionary)
    run_file_name = os.path.join(dictionary["path"], 'run.yaml')
    with open(run_file_name, 'w') as f:
        yaml.dump(run_dictionary, f)

    subprocess.call( ["bin/neuralsampler", run_file_name ])


def make_rundictionary(dictionary):
    run_dictionary = {}
    run_dictionary["Config"] = dictionary["Config"]
    run_dictionary["outfile"] = dictionary["outfile"]
    weight, bias, initialstate = weights.generate(dictionary["Network"])
    run_dictionary["weight"] = weight
    run_dictionary["bias"] = bias
    run_dictionary["initialstate"] = initialstate

    return run_dictionary


if __name__=="__main__":
    try:
        d = yaml.load(open(sys.argv[1], 'r'))
        if d["type"] == "Experiment":
            conf = d.pop("generate_config")
            experiment(d, **conf)
        elif d["type"] == "Run":
            run(d)
        elif d["type"] == "Simulation":
            simulation(sys.argv[1])
        else:
            raise NotImplementedError()
    except NotImplementedError:
        print("Don't know what to do with {}. Must contain node 'type', with value [Experiment|Run|Simulation]".format(sys.argv[1]))



