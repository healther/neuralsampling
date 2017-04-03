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
import shutil

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
cd "{folder}" &&
source {envscript} &&
python {cwd}/control.py expand "{folder}" &&
{binaryLocation} "{folder}/run.yaml" &&
python {cwd}/control.py analysis "{folder}" &&
touch {cwd}/success

/usr/bin/rm -f {files_to_remove}
    """
    content = stub.format(envscript=envfile,
                cwd=os.path.split(os.path.realpath(__file__))[0],
                binaryLocation=binary_location, folder=os.path.abspath(folder),
                files_to_remove=" ".join(files_to_remove))
    with open(folder + os.sep + 'job', 'w') as f:
        f.write(content)


def _submit_job(folder, eta='None'):
    if eta is 'None':
        sim_config = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
        eta_function = utils.get_function_from_name(
                                sim_config['network']['etaFunction'])
        eta = eta_function(sim_config)
    eta = str(eta)
    exe = os.environ['JOBCONTROLEXE']
    jobfile = os.path.join(folder, 'job')
    subprocess.Popen([exe, 'a', jobfile, folder, eta])
    time.sleep(0.005)   # ensure that jobfiles are named differently


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
    shutil.copy(experimentfile, os.path.join('simulations', '01_runs', experimentname))

    experiment_config = dictionary.pop('experimentConfig')
    write_configs = experiment_config.get('writeConfigs', False)
    generate_jobs = experiment_config.get('generateJobs', False)
    submit_jobs = experiment_config.get('submitJobs', False)
    execute_jobs = experiment_config.get('executeJobs', False)
    collect_jobs = experiment_config.get('collectJobs', False)
    envfile = experiment_config.get('envfileLocation', '')
    binary_location = experiment_config.get('binaryLocation', '')
    files_to_remove = experiment_config.get('filesToRemove', '')
    eta = experiment_config.get('eta', 'None')

    sim_folder_template = utils.generate_folder_template(
                    replacements, dictionary, 'simulations', experimentname)

    dictionary['folderTemplate'] = sim_folder_template

    _sanity_check(experiment_config)

    # expand dictionaries
    ex_dicts = utils.expanddict(dictionary, replacements)

    # generate skeletons
    t0 = time.time()
    folders = _get_folders(ex_dicts, sim_folder_template)

    print("Generating {} simulations".format(len(folders)))
    if write_configs:
        _write_configs(ex_dicts, folders)
    else:
        missing_folders = []
        for folder in folders:
            if not os.path.exists(os.path.join(folder, 'success')):
                missing_folders.append(folder)
        folders = missing_folders
    elapsed_time = time.time() - t0
    print("{}: Generated {} simulations in {} "
        "seconds.".format(datetime.datetime.now(), len(folders), elapsed_time))

    if generate_jobs:
        print("{}: Generating {} jobfiles".format(
            datetime.datetime.now(), len(folders)))
        for folder in folders:
            _generate_job(folder, envfile, binary_location, files_to_remove)
        print("{}: Generated {} jobfiles".format(
            datetime.datetime.now(), len(folders)))

        time.sleep(1.)

    if submit_jobs:
        print("{}: Submitting {} jobfiles".format(
            datetime.datetime.now(), len(folders)))
        for i, folder in enumerate(folders):
            if i % 10000 == 0:
                print("{}: {}/{}".format(datetime.datetime.now(), i, len(folders)))
            _submit_job(folder, eta=eta)
        print("{}: Submitted {} jobfiles".format(
            datetime.datetime.now(), len(folders)))

        time.sleep(5.)

    if execute_jobs:
        print("{}: Executing jobs".format(datetime.datetime.now()))
        _execute_jobs()
        print("{}: Executed jobs".format(datetime.datetime.now()))

        time.sleep(3.)  # ensure that all subprocesses have finished

    if collect_jobs:
        print("{}: Collecting results".format(datetime.datetime.now()))
        get_simparameters_from_template = utils.get_function_from_name(
                                        'utils.get_simparameters_from_template')
        collect = []
        nNones = 0
        for simdict, folder in zip(ex_dicts, folders):
            collectdict = {}
            foldertemplate = simdict['folderTemplate']
            simparameterkeys = get_simparameters_from_template(foldertemplate)
            flatsimdict = utils.flatten_dictionary(simdict)
            for spkey in simparameterkeys:
                collectdict[spkey] = flatsimdict[spkey]

            try:
                with open(os.path.join(folder, 'analysis'), 'r') as f:
                    analysisdict = yaml.load(f)

                collectdict['analysis'] = analysisdict
            except:
                collectdict['analysis'] = None
                nNones += 1

            collect.append(collectdict)

        with open(os.path.join('collect', experimentname), 'w') as f:
            yaml.dump(collect, f)
        print("{}: Collected {} results, {} missing".format(
            datetime.datetime.now(), len(folders)-nNones, nNones))

        time.sleep(1.)


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
    rundict['temperature']  = simdict['temperature']
    rundict['externalCurrent'] = simdict['externalCurrent']
    rundict['outfile'] = os.path.join(folder, 'output')

    yaml.dump(rundict, open(os.path.join(folder, 'run.yaml'), 'w'))


def analysis(folder):
    simdict = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
    analysis_function = utils.get_function_from_name(
                                    simdict['analysis']['analysisFunction'])
    if analysis_function=="nothing":
        return
    analysis_function(outfile=os.path.join(folder, 'output'),
            **simdict['analysis']['parameters'])


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
