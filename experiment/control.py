"""Provide C&C capabilities for ../bin/neuralsampler .

Basic workflow:
    ### TODO
"""

import yaml
import os
import subprocess
import sys
import datetime
import time

import utils


def _get_folders(ex_dicts, sim_folder_template):
    """Helper function providing the simulation folder from the template."""
    folders = [sim_folder_template.format(**d)
                    for d in map(utils.flatten_dictionary, ex_dicts)]
    return folders


def _write_configs(ex_dicts, folders):
    """Helper function writing the sim.yaml config files."""
    for ed, folder in zip(ex_dicts, folders):
        utils.ensure_exists(folder)
        ed['path'] = folder
        with open(os.path.join(folder, 'sim.yaml'), 'w') as f:
            yaml.dump(ed, f)


def _generate_job(folder, envfile, binary_location, files_to_remove, eta):
    stub = """
cd {folder}
source {envscript}
{cwd}/control.py expand {folder}
{binaryLocation} {folder}/run.yaml
{cwd}/control.py analysis {folder}

rm {files_to_remove}
    """
    content = stub.format(envscript=envfile, cwd=os.path.realpath(__file__),
                binaryLocation=binary_location, folder=folder,
                files_to_remove=files_to_remove)
    with open(folder + os.sep + 'job', 'w') as f:
        f.write(content)


def _submit_job(folder):
    eta = utils.eta(folder + os.sep + 'sim.yaml')
    subprocess.call(['jobcontrol', 'a', folder + os.sep + 'job', folder, eta])


def _sanity_check(config):
    if not os.path.exists(config.get['binary_location']):
        raise OSError(
            "Executable {} not found".format(config.get['binary_location']))
    if not os.path.exists(config.get['envfile']):
        raise OSError(
            "Environment file {} not found".format(config.get['envfile']))


def run_experiment(experimentfile):
    print("{}: Starting experiment".format(datetime.datetime.now()))
    dictionary = yaml.load(open(experimentfile, 'r'))

    replacements = dictionary.pop('replacements', {})
    basedir = dictionary.get('name', 'simulations')
    sim_folder_template = utils.generate_folder_template(replacements,
                                                            dictionary,
                                                            base=basedir)

    experiment_config = dictionary.pop('experiment_config')
    write_configs = experiment_config.get('write_configs', False)
    generate_jobs = experiment_config.get('generate_jobs', False)
    submit_jobs = experiment_config.get('submit_jobs', False)
    envfile = experiment_config.get('envfile', '')
    binary_location = experiment_config.get('binary_location', '')
    files_to_remove = experiment_config.get('filesToRemove', '')

    _sanity_check(experiment_config)

    # expand dictionaries
    ex_dicts = utils.expanddict(dictionary, replacements)

    # generate skeletons
    t0 = time.time()
    folders = _get_folders(ex_dicts, sim_folder_template)
    if write_configs:
        _write_configs(ex_dicts, folders)
    elapsed_time = time.time() - t0
    print("{}: Generated {} simulations in {} "
        "seconds.".format(datetime.datetime.now(), len(folders), elapsed_time))

    if generate_jobs:
        for folder in folders:
            _generate_job(folder, envfile, binary_location, files_to_remove)

    if submit_jobs:
        for folder in folders:
            _submit_job(folder)


def expand(folder):
    simdict = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    rundict = {}
    rundict['Config'] = simdict['Config']

    create_function = utils.get_function_from_name(
                                        simdict['problem']['problemFunction'])
    W, b, i = create_function(**simdict['problem']['parameters'])
    rundict['weight']       = W
    rundict['bias']         = b
    rundict['initialstate'] = i
    # extend for other input, e.g. external currents, temperature etc.
    # once implemented in neuralsampler
    rundict['outfile'] = os.path.join(folder, 'output')

    yaml.dump(rundict, open(os.path.join(folder, 'run.yaml'), 'w'))


def analysis(folder):
    simdict = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    analysis_function = utils.get_function_from_name(
                                    simdict['analysis']['analysisFunction'])
    analysis_function(**simdict['analysis']['parameters'])


if __name__ == "__main__":
    if len(sys.argv) == 1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv) == 2:
        run_experiment(experimentfile=sys.argv[1])
    elif len(sys.argv) == 3:
        if sys.argv[1] == 'expand':
            expand(folder=sys.argv[2])
        if sys.argv[1] == 'analysis':
            analysis(folder=sys.argv[2])
    else:
        print("Don't know what to do.")
    print(sys.argv)
