import os
import numpy as np


def collect_mean_std_mean(folder):
    #d = np.loadtxt(os.path.join(folder, 'output'), skiprows=1)
    d = np.genfromtxt(os.path.join(folder, 'output'), dtype=np.int32, skip_header=1, max_rows=10000)
    v = {"mean": float(d.mean()), "std": float(d.std())}

    return {folder.split(os.sep)[-1]: v}



def collect_mean_std_state(folder):
    d = np.genfromtxt(os.path.join(folder, 'output'), dtype=np.bool, delimiter=1, skip_header=1)
    d = d.sum(axis=-1)
    k = tuple( folder.split(os.sep)[-1].split("_") )
    v = {"mean": float(d.mean()), "std": float(d.std())}

    return (k, v )



