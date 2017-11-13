"""Provide C&C capabilities for ../bin/neuralsampler .

Basic workflow:
    ### TODO
"""
from __future__ import print_function, division

import yaml
import os
import inspect
import subprocess
import datetime
import time
import shutil
import multiprocessing as mp
import sys

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
set -x
cd "{folder}" &&
set +x
source {envscript} &&
set -x
python {cwd}/control.py -m expand "{folder}" &&
{binaryLocation} "{folder}/run.yaml" &&
python {cwd}/control.py -m analysis "{folder}" &&
/usr/bin/touch "{folder}/success"

/usr/bin/rm -f {files_to_remove}
    """
    content = stub.format(envscript=envfile,
                cwd=os.path.split(os.path.realpath(__file__))[0],
                binaryLocation=binary_location, folder=os.path.abspath(folder),
                files_to_remove=" ".join(files_to_remove))
    with open(folder + os.sep + 'job', 'w') as f:
        f.write(content)


def _submit_jobs(folders, eta, submit_jobs):
    p = mp.Pool(submit_jobs)
    p.map(_submit_job, [{'folder': f, 'eta': eta} for f in folders])
    p.close()
    p.join()


def _submit_job(argdict):
    folder = argdict['folder']
    eta    = argdict['eta']
    if eta is 'None':
        sim_config = yaml.load(open(os.path.join(folder, 'sim.yaml'), 'r'))
        eta_function = utils.get_function_from_name(
                                sim_config['network']['etaFunction'])
        eta = eta_function(sim_config)
    eta = str(eta)
    exe = os.environ['JOBCONTROLEXE']
    jobfile = os.path.join(folder, 'job')
    subprocess.call([exe, 'a', jobfile, folder, eta])
    # ensure that jobfiles are named differently


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


def run_experiment(experimentfile, write_configs, generate_jobs, submit_jobs,
        submit_failed_jobs, execute_jobs, collect_jobs):
    print("{}: Starting experiment".format(datetime.datetime.now()))
    dictionary = yaml.load(open(experimentfile, 'r'))

    replacements = dictionary.pop('replacements', {})
    rules = dictionary.pop('rules', {})
    experimentname = dictionary.get('experimentName', '')

    experiment_config = dictionary.pop('experimentConfig')
    envfile = experiment_config.get('envfileLocation', '')
    binary_location = experiment_config.get('binaryLocation', '')
    files_to_remove = experiment_config.get('filesToRemove', '')
    eta = experiment_config.get('eta', 'None')

    # save experimentfile if we are submitting jobs
    if generate_jobs or write_configs:
        trackingFileName = os.path.join('simulations', '01_runs',
                                        experimentname)
        if os.path.isfile(trackingFileName):
            response = raw_input("{} already exists. Do you want to override "
                                 "it? [y/n/a]  ".format(trackingFileName))
            if response is "y":
                shutil.copy(experimentfile, trackingFileName)
            elif response is "n":
                pass
            else:
                print("Aborting")
                exit()
        else:
            shutil.copy(experimentfile, trackingFileName)

    #    experiment_iteration_name =
    #           utils.append_iteration_of_experiment(experimentname)
    #    shutil.copy(experimentfile, os.path.join('simulations',
    #                               '01_runs', experiment_iteration_name))

    sim_folder_template = utils.generate_folder_template(
                    replacements, dictionary, 'simulations', experimentname)

    dictionary['folderTemplate'] = sim_folder_template

    # _sanity_check(experiment_config)

    # expand dictionaries
    ex_dicts = [ex_dict
                    for ex_dict in utils.expanddict(dictionary, replacements)
                    if utils.apply_rules(ex_dict, rules)]

    # generate skeletons
    t0 = time.time()
    folders = _get_folders(ex_dicts, sim_folder_template)

    print("{}: Generating {} simulations".format(
                                        datetime.datetime.now(), len(folders)))
    missing_folders = []
    if write_configs:
        _write_configs(ex_dicts, folders)
    else:
        for i, folder in enumerate(folders):
            print("Generating {: 3.1f}% complete".format(100.*i/len(folders)),
                end='\r')
            if not os.path.exists(os.path.join(folder, 'success')):
                missing_folders.append(folder)
    elapsed_time = time.time() - t0
    print("{}: Generated {} simulations in {} "
        "seconds.".format(datetime.datetime.now(), len(folders), elapsed_time))

    if generate_jobs:
        print("{}: Generating {} jobfiles".format(
            datetime.datetime.now(), len(folders)))
        for i, folder in enumerate(folders):
            print("Generating {: 3.1f}% complete".format(100.*i/len(folders)),
                end='\r')
            sys.stdout.flush()
            _generate_job(folder, envfile, binary_location, files_to_remove)
        print("{}: Generated {} jobfiles".format(
            datetime.datetime.now(), len(folders)))
    elif missing_folders:
        print("{}: Generating {} jobfiles for failed jobs".format(
            datetime.datetime.now(), len(missing_folders)))
        for i, folder in enumerate(missing_folders):
            print("Generating {: 3.1f}% complete"
                  "".format(100.*i/len(missing_folders)), end='\r')
            sys.stdout.flush()
            _generate_job(folder, envfile, binary_location, files_to_remove)
        print("{}: Generated {} jobfiles".format(
            datetime.datetime.now(), len(missing_folders)))

        time.sleep(1.)

    if submit_jobs:
        print("{}: Submitting {} jobfiles".format(
            datetime.datetime.now(), len(folders)))
        _submit_jobs(folders, eta, submit_jobs)
        print("{}: Submitted {} jobfiles".format(
            datetime.datetime.now(), len(folders)))

        time.sleep(1.)

    if submit_failed_jobs and missing_folders:
        print("{}: Submitting {} jobfiles".format(
            datetime.datetime.now(), len(missing_folders)))
        _submit_jobs(missing_folders, eta, submit_failed_jobs)
        print("{}: Submitted {} jobfiles".format(
            datetime.datetime.now(), len(missing_folders)))

        time.sleep(1.)

    if execute_jobs:
        print("{}: Executing jobs".format(datetime.datetime.now()))
        _execute_jobs()
        print("{}: Executed jobs".format(datetime.datetime.now()))

        time.sleep(5.)  # ensure that all subprocesses have finished

    if collect_jobs is not False:
        print("{}: Collecting results".format(datetime.datetime.now()))
        get_simparameters_from_template = utils.get_function_from_name(
                                    'utils.get_simparameters_from_template')
        collect = []
        n_nones = 0
        for i, (simdict, folder) in enumerate(zip(ex_dicts, folders)):
            print("Collecting {: 3.1f}% complete".format(100*i/len(folders)),
                    end='\r')
            sys.stdout.flush()
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
                n_nones += 1

            collect.append(collectdict)

        with open(os.path.join('collect', experimentname), 'w') as f:
            yaml.dump(collect, f)
        print("{}: Collected {} results, {} missing".format(
            datetime.datetime.now(), len(folders) - n_nones, n_nones))

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
    if analysis_function == "nothing":
        return
    else:
        analysis_function(outfile=os.path.join(folder, 'output'),
            **simdict['analysis']['parameters'])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='CnC for neuralsampler.')
    parser.add_argument('path', type=str)
    parser.add_argument('--mode', '-m',
        choices=['execute', 'expand', 'analysis'], default='execute',
        help='specify the mode in which to run, choose from %(choices)s')
    parser.add_argument('--write-configs', '-w', dest='write_configs',
                    action='store_const', const=True, default=False,)
    parser.add_argument('--generate-jobs', '-g', dest='generate_jobs',
                    action='store_const', const=True, default=False,)
    parser.add_argument('--submit-jobs', '-s', dest='submit_jobs',
                    type=int, default=0)
    parser.add_argument('--submit-failed-jobs', '-f',
                    dest='submit_failed_jobs', type=int, default=0)
    parser.add_argument('--execute-jobs', '-e', dest='execute_jobs',
                    action='store_const', const=True, default=False,)
    parser.add_argument('--collect-jobs', '-c', dest='collect_jobs',
                    action='store_const', const=True, default=False,)

    args = parser.parse_args()
    print(args)
    if args.mode == 'execute':
        run_experiment(experimentfile=args.path,
            write_configs=args.write_configs, generate_jobs=args.generate_jobs,
            submit_jobs=args.submit_jobs,
            submit_failed_jobs=args.submit_failed_jobs,
            execute_jobs=args.execute_jobs, collect_jobs=args.collect_jobs)
    elif args.mode == 'expand':
        expand(folder=args.path)
    elif args.mode == 'analysis':
        analysis(folder=args.path)
    else:
        print("Don't know what to do.")
        print(parser.print_help())
