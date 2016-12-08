"""Provide C&C capabilities for ../bin/neuralsampler .

Basic workflow:
    ### TODO
"""

### TODO: cleanup imported modules
import yaml
import os
import subprocess
import sys
import multiprocessing as mp
import datetime
import time
import numpy as np

import config
import misc
import analysis
import plot
import cluster


def run_experiment(dictionary):
    """Run the experiment specified in dictionary.

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
            # TODO: Implement a value = factor * othervalue feature!!!
            # TODO: Remove _ from parameter names or change connector in dict-flattening!!!

    """
    ### TODO: Improve documentation
    ### separate configuration entries
    print("{}: Starting experiment".format(datetime.datetime.now()))

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
    t0 = time.time()
    if write_configs:
        folders = _get_folders(ex_dicts, sim_folder_template)
        _write_configs(ex_dicts, folders)
    else:
        folders = _get_folders(ex_dicts, sim_folder_template)
    elapsed_time = time.time() - t0
    print("{}: Generated {} simulations in {} seconds.".format(datetime.datetime.now(), len(folders), elapsed_time))

    if execute:
        print("{}: execute".format(datetime.datetime.now()))
        sim_processor = _generate_processor(**sim_parameters)
        sim_processor.run_jobs(folders, **dictionary['simulate'])
        if dictionary["wait"]:
            sim_processor.wait_for_finish()
            if not sim_processor.ensure_success():
                print("Not all jobs succeeded.")

    if run_analysis:
        print("{}: analysis".format(datetime.datetime.now()))
        ana_processor = _generate_processor(**ana_parameters)
        ana_processor.run_jobs(folders, **dictionary['analysis'])
        if dictionary["wait"]:
            ana_processor.wait_for_finish()
            if not ana_processor.ensure_success():
                print("Not all jobs succeeded.")

    if collect_results:
        print("{}: collect".format(datetime.datetime.now()))
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


def _write_configs(ex_dicts, folders):
    """Helper function writing the sim.yaml config files."""
    for ed, folder in zip(ex_dicts, folders):
        misc.ensure_folder_exists(folder)
        ed['path'] = folder
        ed['type'] = 'Simulation'
        with open(os.path.join(folder, 'sim.yaml'), 'w') as f:
            yaml.dump(ed, f)


def _get_folders(ex_dicts, sim_folder_template):
    """Helper function providing the simulation folder from the template."""
    folders = [sim_folder_template.format(**d)
                    for d in map(misc.flatten_dictionary, ex_dicts)]
    return folders


def get_function_from_name(function_name):
    """Return the callable function_name=module.function ."""
    # TODO: Move to misc
    m = __import__(function_name.split('.')[0])
    func = getattr(m, function_name.split('.')[1])
    return func


def dump_runfile(folder):
    simyaml = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    create_sim_function = get_function_from_name(simyaml['network']['name'])
    W, b, i = create_sim_function(**simyaml['network']['parameters'])
    simyaml['weight'] = W
    simyaml['bias'] = b
    simyaml['initialstate'] = i
    simyaml['outfile'] = os.path.join(folder, 'output')
    yaml.dump(simyaml, open(os.path.join(folder, 'run.yaml'), 'w'))


def simulate(folder, check_output=False):
    """Execute simulation in folder.

    Expands folder/sim.yaml into folder/run.yaml by calling the
    sim.yaml[network][name] function with sim.yaml[network][parameters]
    Which needs to return the network configuration (W,b,i)

    Returns the return value of bin/neuralsampler.

    TODO: make check_output available through BwUni cluster
    """
    if check_output:
        if os.path.exists(os.path.join(folder, 'output')):
            return 0
    dump_runfile(folder)
    DEVNULL = open(os.devnull, 'wb')
    ret_value = subprocess.call(['bin/neuralsampler',
                                os.path.join(folder, 'run.yaml')],
                                stdout=DEVNULL)
    return ret_value


if __name__=="__main__":
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv)==2:
        d = yaml.load(open(sys.argv[1], 'r'))
        run_experiment(dictionary=d)
    elif len(sys.argv)==3:
        if sys.argv[1]=='run':
            simulate(folder=sys.argv[2])
    else:
        print("Don't know what to do.")



