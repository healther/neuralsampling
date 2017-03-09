"""Provide C&C capabilities for ../bin/neuralsampler .

Basic workflow:
    ### TODO
"""

import yaml
import os
import inspect
import subprocess
import sys
import datetime
import time

import utils

currentdir = os.path.dirname(os.path.abspath(
                                inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
os.environ['JOBCONTROLEXE'] = os.path.join(
                        parentdir,
                        "jobcontrol",
                        "jobcontrol.py")


def _get_folders(ex_dicts, sim_folder_template):
    """Helper function providing the simulation folder from the template."""
    folders = [sim_folder_template.format(**d)
                    for d in map(utils.flatten_dictionary, ex_dicts)]
    return folders


def _write_configs(ex_dicts, folders):
    """Helper function writing the sim.yaml config files."""
    for ed, folder in zip(ex_dicts, folders):
        utils.ensure_exist(folder)
        ed['path'] = folder
        with open(os.path.join(folder, 'sim.yaml'), 'w') as f:
            yaml.dump(ed, f)


def _generate_job(folder, envfile, binary_location, files_to_remove):
    stub = """
cd {folder}
source {envscript}
python {cwd}/control.py expand {folder}
{binaryLocation} {folder}/run.yaml
python {cwd}/control.py analysis {folder}

/usr/bin/rm {files_to_remove}
    """
    content = stub.format(envscript=envfile,
                cwd=os.path.split(os.path.realpath(__file__))[0],
                binaryLocation=binary_location, folder=os.path.abspath(folder),
                files_to_remove=" ".join(files_to_remove))
    with open(folder + os.sep + 'job', 'w') as f:
        f.write(content)


def _submit_job(folder):
    sim_config = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    eta_function = utils.get_function_from_name(
                            sim_config['network']['etaFunction'])
    eta = eta_function(sim_config)
    subprocess.call(
        [os.environ['JOBCONTROLEXE'],
            'a', os.path.join(folder, 'job'), folder, eta])


def _execute_jobs():
    subprocess.call(
        [os.environ['JOBCONTROLEXE'], 'e'])


def _sanity_check(config):
    binaryLocation = config.get('binaryLocation', 'somenonexistingfile')
    envfileLocation = config.get('envfileLocation', 'somenonexistingfile')
    if not os.path.exists(binaryLocation):
        raise OSError("Executable {} not found".format(binaryLocation))
    if not os.path.exists(envfileLocation):
        raise OSError("Environment file {} not found".format(envfileLocation))


def run_experiment(experimentfile):
    print("{}: Starting experiment".format(datetime.datetime.now()))
    dictionary = yaml.load(open(experimentfile, 'r'))

    replacements = dictionary.pop('replacements', {})
    experimentname = dictionary.get('experimentName', '')

    experiment_config = dictionary.pop('experimentConfig')
    write_configs = experiment_config.get('writeConfigs', False)
    generate_jobs = experiment_config.get('generateJobs', False)
    submit_jobs = experiment_config.get('submitJobs', False)
    execute_jobs = experiment_config.get('executeJobs', False)
    envfile = experiment_config.get('envfileLocation', '')
    binary_location = experiment_config.get('binaryLocation', '')
    files_to_remove = experiment_config.get('filesToRemove', '')

    sim_folder_template = utils.generate_folder_template(
                    replacements, dictionary, 'simulations', experimentname)

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

    if execute_jobs:
        _execute_jobs()


def expand(folder):
    simdict = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    rundict = {}
    rundict['Config'] = simdict['Config']

    create_function = utils.get_function_from_name(
                                        simdict['network']['problemName'])
    W, b, i = create_function(**simdict['network']['parameters'])
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
