"""Provide C&C capabilities for ../bin/neuralsampler

Basic workflow:
    ### TODO
"""
import yaml
import os
import subprocess
import sys
import multiprocessing as mp
import datetime
import numpy as np

import config
import misc
import analysis
import plot
import cluster

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

echo {job_file}
python generate/control.py {job_file}
"""

def run_experiment(dictionary):
    """Run the experiment specified in dictionary

    Dictionary keys:
        exp_conf:   Configuration for this function,
           {'write_configs'  : True,
            'execute_sims'   : True,
            'run_analysis'   : True,
            'collect_results': True,}
        sim_folder_template: string
        network: ## TODO: specify API for problem description
           {'problemname' : string, # needs to be available as problem_problemname.py
            'parameters' : dict}
        execution:## TODO: specify API for execution environment
        analysis: ## TODO: specify API for problem analysis
        collect:  ## TODO: specify API for collect functionality
        replacements: {key: [values, ...], ...}


    """
    ### separate configuration entries
    replacements = dictionary.pop('replacements', {})
    sim_folder_template = dictionary.get('sim_folder_template')

    experiment_config = dictionary.pop('experiment_config')
    write_configs = experiment_config.get('write_configs', False)
    execute = experiment_config.get('execute_sims', False)
    run_analysis = experiment_config.get('run_analysis', False)
    collect_results = experiment_config.get('collect_results', False)
    plot = experiment_config.get('plot', False)

    sim_parameters = dictionary.pop('sim_parameters', {"target_system": "Local"})
    ana_parameters = dictionary.pop('ana_parameters', {"target_system": "Local"})
    col_parameters = dictionary.pop('col_parameters', {"target_system": "Local"})

    ### expand dictionaries
    ex_dicts = config.expanddict(dictionary, replacements)

    ### do actual work
    if write_configs:
        folders = _get_folders(ex_dicts, sim_folder_template)
        _write_configs(ex_dicts, folders)
    else:
        folders = _get_folders(ex_dicts, sim_folder_template)

    if execute:
        print("execute")
        sim_processor = _generate_processor(**sim_parameters)
        sim_processor.run_jobs(folders, **dictionary['simulate'])
        if dictionary["wait"]:
            sim_processor.wait_for_finish()
            sim_processor.ensure_success()

    if run_analysis:
        print("analysis")
        ana_processor = _generate_processor(**ana_parameters)
        ana_processor.run_jobs(folders, **dictionary['analysis'])
        if dictionary["wait"]:
            ana_processor.wait_for_finish()
            ana_processor.ensure_success()

    if collect_results:
        print("collect")
        if not dictionary['collect'].has_key('parameters'):
            dictionary['collect']['parameters'] = {'targetfolder': '.',
                            'targetfile': dictionary['experiment_name']}

        module_name, function_name = dictionary['collect']['function_name'].split('.')
        parameters = dictionary['collect']['parameters']

        if not parameters.has_key('targetfolder'):
            parameters['targetfolder'] = '.'
        if not parameters.has_key('targetfile'):
            parameters['targetfile'] = dictionary['experiment_name']

        function = getattr(__import__(module_name), function_name)
        function(folders, **parameters)



def _generate_processor(target_system='Local', system_parameters={}):
    if target_system=='Local':
        processor = cluster.Local(**system_parameters)
    elif target_system=='BwUni':
        processor = cluster.BwUni(**system_parameters)
    else:
        raise NotImplementedError("Please implement the cluster you want to use.")
    return processor


def _create_function(config_to_sim, execute_sim_function):
    config_to_sim_function = ''

    def function(folder):
        try:
            config_to_sim_function(folder)
        except BaseException as e:
            return 1
        try:
            execute_sim_function(folder)
        except BaseException as e:
            return 2
        return 0

    return function


def _write_configs(ex_dicts, folders):
    for ed, folder in zip(ex_dicts, folders):
        misc.ensure_folder_exists(folder)
        ed['path'] = folder
        ed['type'] = 'Simulation'
        with open(os.path.join(folder, 'sim.yaml'), 'w') as f:
            yaml.dump(ed, f)


def _get_folders(ex_dicts, sim_folder_template):
    folders = [sim_folder_template.format(**d)
                    for d in map(misc.flatten_dictionary, ex_dicts)]
    return folders


def get_function_from_name(transform_function_name):
    m = __import__(transform_function_name.split('.')[0])
    func = getattr(m, transform_function_name.split('.')[1])
    return func


def simulate(folder):
    simyaml = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    create_sim_function = get_function_from_name(simyaml['network']['name'])
    W, b, i = create_sim_function(**simyaml['network']['parameters'])
    simyaml['weight'] = W
    simyaml['bias'] = b
    simyaml['initialstate'] = i
    simyaml['outfile'] = os.path.join(folder, 'output')
    yaml.dump(simyaml, open(os.path.join(folder, 'run.yaml'), 'w'))
    DEVNULL = open(os.devnull, 'wb')
    ret_value = subprocess.call(['bin/neuralsampler',
                                os.path.join(folder, 'run.yaml')],
                                stdout=DEVNULL)
    return ret_value


def experiment(dictionary, bgenerate_sim=True, bgenerate_job=True, generate_folder='tmp', brun=True, bcollect=True, bplot=True):
    print("{}: Extracting onetime information".format(datetime.datetime.now()))
    replacements = dictionary.pop("replacements")
    sim_folder_template = dictionary.pop("sim_folder_template")
    executable_configuration = dictionary.pop("exec_conf")
    analysis_dictionary = dictionary.pop("analysis")
    dictionary.pop('type')

    ### generate folders
    print("{}: Expanding input dictionary according to {} rules".format(datetime.datetime.now(), len(replacements)))
    if bgenerate_sim:
        print("    Generating {} simulation files".format(np.prod([len(r) for k, r in replacements.iteritems()])))
    folders = []
    for ed in config.expanddict(dictionary, replacements):
        d = misc.flatten_dictionary(ed)
        folder = sim_folder_template.format(**d)
        if bgenerate_sim:
            misc.ensure_folder_exists(folder)

            ed['outfile'] = os.path.join(folder, 'output')
            ed['path'] = folder
            ed['type'] = 'Simulation'

            with open(folder+os.sep+'sim.yaml', 'w') as f:
                yaml.dump(ed, f)

        folders.append(folder)

    ### generate run files
    if bgenerate_job:
        n_sims_per_job = executable_configuration["n_sims_per_job"]
        n_job_files = int(len(folders)/n_sims_per_job) + 1
        print("{}: Generating {} slurm-jobfiles for {} simulations".format(datetime.datetime.now(), n_job_files, len(folders)))

        # unique base name
        current_time = datetime.datetime.now()
        moab_files = []
        misc.ensure_folder_exists(generate_folder)
        for i in range(n_job_files):
            job_file = generate_folder + os.sep + str(current_time).strip() + \
                    '{}.yaml'.format(i)
            job_file = job_file.replace(" ", "_")
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

    if bcollect:
        print("{}: Starting to collect data".format(datetime.datetime.now()))
        analysis_function = getattr(analysis, analysis_dictionary["collect_function"])

        args = []
        for i in range(len(folders)/1000 + 1):
            arg = {'folders': folders[i*1000:(i+1)*1000],
                    'analysis_function': analysis_function,
                    'collected_file': analysis_dictionary["outfile"]+"{:03d}".format(i),
                    }
            args.append(arg)

        pool = mp.Pool(8)
        pool.map(misc.collect_results_caller, args)
        pool.close()
        pool.join()

        collected = {}
        for a in args:
            d = yaml.load(open(a["collected_file"], 'r'))
            collected.update(d)

        with open(analysis_dictionary["outfile"], 'w') as f:
            yaml.dump(collected, f)

    if bplot:
        print("Plotting")
        for w in replacements["w"]:
            for rt in replacements["nu"]:
                plot.colormap(analysis_dictionary["outfile"], 'tau', 'initialactivity', 'mean',
                        restrictions={'weight': [w], 'randomtype': [rt]},
                        plotfolder= 'plots',
                        plotname='w{}_rt{}.pdf'.format(w, rt))


    print("{} Finshed".format(datetime.datetime.now()))


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
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv)==2:
        d = yaml.load(open(sys.argv[1], 'r'))
        run_experiment(dictionary=d)
    elif len(sys.argv)==3:
        simulate(folder=sys.argv[1], transform_function_name=sys.argv[2])
    else:
        print("Don't know what to do.")



