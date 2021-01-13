"""This module implements standard sampling."""
import sys
import numpy as np


def create_beta_distribution(n, factor, alpha, beta, rseed, ic_low, ic_high,
                ic_rseed):
    """Create a BM with beta distributed parameters.

    Input:
        n           int     number of samplers
        factor      float   prefactor of the distribution
        alpha       float   alpha parameter of the beta distribution
        beta        float   beta parameter of the beta distribution
        rseed       int     random seed for the parameter draw
        ic_low      float   lower end of the initial condition distribution
        ic_high     float   upper bound of the initial condition distribution
        ic_random   int     random seed for the initial conditions

    >>> create_beta_distribution(3, 1., .5, .5, 12, 0, 10, 13)
    ([[0.0, 0.30425651289269606, 0.49974839820651534], [0.30425651289269606, 0.0, 0.32013983380426525], [0.49974839820651534, 0.32013983380426525, 0.0]], [-0.4992597294794353, -0.07487731161190547, 0.32439364137800153], [7, 2, 8]) # noqa
    """
    np.random.seed(rseed)
    weights = factor * (.5 - np.random.beta(alpha, beta, size=(n, n)))
    weights = np.triu(weights, 1)
    weights += weights.T
    biases = factor * (.5 - np.random.beta(alpha, beta, size=n))
    np.random.seed(ic_rseed)
    initial_conditions = np.random.uniform(ic_low, ic_high,
                                            len(biases)).astype(int)

    return weights.tolist(), biases.tolist(), initial_conditions.tolist()


def create(weights, biases, initial_conditions):
    """Create concrete Boltzmann machine.

    Input:
        weights             string      filename of weights ndarray
                            ndarray     weight matrix, must be symetric and
                                        zero diagonal
        biases              string      filename of biases ndarray
                            ndarray     biases vector
        initial_conditions  string      filename of initial_conditions ndarray
                            ndarray     initial_conditions vector
                            [float, float, int]    uniform initialisation
                                        above {low, ..., high}

    >>> create([[0., 1.], [1., 0.]], [.5, -.5], [0, 5])
    ([[0.0, 1.0], [1.0, 0.0]], [0.5, -0.5], [0, 5])
    """
    if isinstance(weights, str):
        weights = np.loadtxt(weights)
    else:
        weights = np.array(weights)
    if isinstance(biases, str):
        biases = np.loadtxt(biases)
    else:
        biases = np.array(biases)
    if isinstance(initial_conditions, str):
        initial_conditions = np.loadtxt(initial_conditions)
    elif len(initial_conditions) == 3:
        low = initial_conditions[0]
        high = initial_conditions[1]
        rseed = initial_conditions[2]
        np.random.seed(rseed)
        initial_conditions = np.random.uniform(low, high,
                                        len(biases)).astype(int)
    else:
        initial_conditions = np.array(initial_conditions)

    return weights.tolist(), biases.tolist(), initial_conditions.tolist()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        import doctest
        print(doctest.testmod())
