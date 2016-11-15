from __future__ import division


import numpy as np
import yaml
import sys


def generate_networks(replacements, networkdict):
    

    generate_network(**ndict)


def generate_network(linearsize = 10, dimension = 1, initialstate = {'mean_activity':0.5, 'rseed':42424242},
        Configdict=yaml.load(open('dict.yaml', 'r'))["Config"]):
    outdict = {}
    outdict["Config"] = Configdict
    weights = generate_connection_matrix(linsize=linearsize, dimension=dimension)
    initialstate = generate_initialstate(len(weights), tauref=Configdict["tauref"], **initialstate)
    bias = generate_bias(weights)
    outdict["weight"] = weights.tolist()
    outdict["initialstate"] = initialstate.tolist()
    outdict["bias"] = bias.tolist()
    return outdict

def generate_initialstate(num_sampler, mean_activity=0.5, tauref=100, rseed=42424242):
    high = tauref/mean_activity
    return np.random.randint( 0, int(high), num_sampler)


def generate_connection_matrix(linsize=10, dimension=2):
    ### TODO: add decaying longrange connections
    weights = np.zeros((linsize**dimension, linsize**dimension))
    for nid in range(linsize**dimension):
        connlist = [(nid+o) % (linsize**(d+1)) +
                    int(nid/linsize**(d+1))*linsize**(d+1)
                    for d in range(dimension)
                    for o in [linsize**d, -linsize**d]
                    ]
        weights[nid, connlist] = 1.
    return weights


def generate_bias(weigths):
    biases = -.5 * weigths.sum(axis=-1)
    return biases



if __name__=="__main__":
    inputdict = yaml.load(open('dict.yaml', 'r'))
    outdict = generate_networks(**inputdict)

    with open('di.ya', 'w') as f:
        yaml.dump(outdict, f)

