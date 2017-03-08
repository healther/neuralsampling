import sys
import os
import subprocess


def restage_jobfile(jobfile):
    with open(jobfile, 'r') as f:
        content = f.readlines()
    # restore only original content
    eta = content[0].strip()
    cwd = content[1].strip()
    content = content[2:]
    # recreate original file
    with open(jobfile + 'run', 'w') as f:
        f.write("".join(content))
    # add original file to staged jobs
    subprocess.call(['jobcontrol.py', 'a', jobfile, eta, cwd])


taskfile = sys.argv[1]

with open(taskfile, 'r') as f:
    jobfiles = [line.strip() for line in f]

readded = 0
for jobfile in jobfiles:
    if not os.path.exists(jobfile):
        print("Something bad happened, can't find {} anymore.".format(jobfile))
    elif not os.path.exists(jobfile + '.start'):
        print("Never started {} for some reason. Restaging".format(jobfile))
        restage_jobfile(jobfile)
        readded += 1
    elif (os.path.exists(jobfile + '.start') and
            not os.path.exists(jobfile + '.finish')):
        print("{}, did not finish for some reason. "
                                    "Restaging".format(jobfile))
        restage_jobfile(jobfile)
        readded += 1
    elif (os.path.exists(jobfile + '.start') and
            os.path.exists(jobfile + '.finish') and
            not os.path.exists(jobfile + '.success')):
        print("{}, did not succeed for some reason. "
                                    "Do not restage.".format(jobfile))
    else:
        print("Finished {} successfully (return code zero)".format(jobfile))
        os.remove(jobfile + '.start')
        os.remove(jobfile + '.finish')
        os.remove(jobfile + '.success')
        os.remove(jobfile + 'run')
        os.remove(jobfile)

os.remove(taskfile)
print("Readded {} out of {}.".format(readded, len(jobfiles)))
