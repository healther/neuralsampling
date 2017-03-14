"""This module implements the TSP problem for neural networks."""
from __future__ import division, print_function
import sys
import yaml
import numpy as np
import itertools

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import utils


# misc functions

# could be extended to different file formats...
def _readtsp(filename):
    """Return the distance matrix in filename."""
    d = np.loadtxt(filename)
    return d





def create_tsp(tspfilename, temporal, spatial, number, data, start11=False):
    """

        temporal: each city at exactly one position
        spatial:  at each position exactly one city
        number:   in total n cities in route
        data:     distance weights
        start11:  whether city 1 should be the starting point
    """

    distances = _readtsp(tspfilename)
    # weights = np.zeros(len(distances)**2, len(distances)**2)
    weightlist = []
    for city1 in range(len(distances)):
        for position1 in range(len(distances)):
            n1 = utils.double_index_to_single(city1, position1)
            for city2 in range(len(distances)):
                for position2 in range(len(distances)):
                    n2 = utils.double_index_to_single(city2, position2)
                    if city1 == city2:
                        if position1 != position2:
                            weightlist.append([n1, n2, spatial])
                        else:
                            continue  ## TODO: Check
                    else:
                        if position1 == position2:
                            weightlist.append([n1, n2, temporal])
                        elif abs(position1 - position2) == 1:
                            weightlist.append([n1, n2,
                                data * distances[city1, city2]])

    # TODO: Implement the target activity

    return weightlist



def create_general_tsp(n_cities, A, B, C):
    """Generate the general restriction matrix for a TSP.

    Input:
        n_cities    int     number of cities in the TSP
        A           float   penalty for a city not having exactly one place
        B           float   penalty for a place not having exactly one city
        C           float   penalty for the route not having exactly n_cities

    Output:
        W           ndarray weight matrix, encoding a general TSP of n_cities
        b           ndarray bias vector, encoding a general TSP of n_cities
    >>> create_general_tsp(3, 1, 2, 3)
    (array([[ 0., -2., -2., -1.,  0.,  0., -1.,  0.,  0.],
           [-2.,  0., -2.,  0., -1.,  0.,  0., -1.,  0.],
           [-2., -2.,  0.,  0.,  0., -1.,  0.,  0., -1.],
           [-1.,  0.,  0.,  0., -2., -2., -1.,  0.,  0.],
           [ 0., -1.,  0., -2.,  0., -2.,  0., -1.,  0.],
           [ 0.,  0., -1., -2., -2.,  0.,  0.,  0., -1.],
           [-1.,  0.,  0., -1.,  0.,  0.,  0., -2., -2.],
           [ 0., -1.,  0.,  0., -1.,  0., -2.,  0., -2.],
           [ 0.,  0., -1.,  0.,  0., -1., -2., -2.,  0.]]), array([ 3.,  3.,  3.,  3.,  3.,  3.,  3.,  3.,  3.]))
    """
    W = np.zeros((n_cities*n_cities, n_cities*n_cities))
    for i,j,x,y in itertools.product(xrange(n_cities), repeat=4):
        wi = double_index_to_single(i,x, n_cities)
        wj = double_index_to_single(j,y, n_cities)
        W[wi, wj] -= A*row_connections(i,j,x,y)
        W[wi, wj] -= B*column_connections(i,j,x,y)
#        W[wi, wj] -= C#*(1-(wi==wj))
    b = np.ones(n_cities*n_cities)*C
    return W, b


## create functions
def _create_tsp(tsp_data, A, B, C, D, fix_starting_point=False):
    """Create concrete TSP realisation.

    Input:
        tsp_data    ndarray     distance matrix, needs to be a numpy array
        A           float       row penalty
        B           float       column penalty
        C           float       number penalty
        D           float       data peanalty
        fix_starting_point  bool    flag wether to prefer the (0,0)
                                    neuron for route uniquness
                                    ### TODO: fix
    """
    tsp_data = tsp_data/np.linalg.norm(tsp_data)
    n_cities = len(tsp_data)
    W, b = create_general_tsp(n_cities, A, B, C)
    for i,j,x,y in itertools.product(xrange(n_cities), repeat=4):
        wi = double_index_to_single(i,x, n_cities)
        wj = double_index_to_single(j,y, n_cities)
        W[wi, wj] -= D*dataterm(i,j,x,y, tsp_data)

    if fix_starting_point:
        b[0] += C
    return W, b


def create(tsp, A, B, C, D, fix_starting_point):
    """Create concrete TSP.

    Input:
        tsp         string      filename of np.savetxt tsp data
                    list        distance matrix
                    ndarray     distance matrix
        A, B, C, D  float       relative peanalties, cf _create_tsp
        fix_starting_point  bool    make route more unique (upto direction)
    """
    if isinstance(tsp, str):
        tsp_data = np.loadtxt(tsp)
    else:
        tsp_data = np.array(tsp)
    W, b = _create_tsp(tsp_data, A, B, C, D, fix_starting_point)
    initialstate = np.zeros(len(b)).astype(int)

    return W.tolist(), b.tolist(), initialstate.tolist()


# analysis functions
def get_pathlength_for_route(route, tsp_data):
    """Return pathlength for a given route in tsp problem tsp_data.

    Input:
        route       list    indices of the stops, must be a permutation of range(len(route))
        tsp_data    array   distances between points

    Output:
        length      float   sum of all distances

    >>> get_pathlength_for_route([0,1,2], [[0., 1., .5], [1., 0., .3], [.5, .3, 0.]])
    1.8
    """
    if isinstance(tsp_data, list):
        tsp_data = np.array(tsp_data)
    return sum(
            [tsp_data[r1,r2] for r1, r2 in zip(route[1:],route[:-1])]
            + [tsp_data[route[-1], route[0]]]
            )


def get_pathlength_from_state(state, tsp_data):
    """Return pathlength for a route given by state.

    Input:
        state       int     final state of the solution
        tsp_data    array   distance between points

    Output:
        route       list    empty if not a valid state
        distance    float   sum of all distances, inf if not valid
    """
    n_cities = len(tsp_data)
    if valid(state, n_cities)!=(True, True, True):
        return [], inf
    if isinstance(state, int):
        state = misc.statestring_from_int(state, n_cities*n_cities)
    bstate = np.array([int(s) for s in state]).reshape((n_cities, n_cities)).tolist()
    route = [line.index(1) for line in bstate]
    d = get_pathlength_for_route(route, tsp_data)
    return route, d


def factorial(n):
    if n<0:
        raise Exception
    elif n==1 or n==0:
        return 1
    else:
        return n*factorial(n-1)


def get_all_routes(tsp_data, max_number=10000):
    if isinstance(tsp_data, list):
        tsp_data = np.array(tsp_data)
    if factorial(len(tsp_data))<max_number:
        return [get_pathlength_for_route(p, tsp_data) for p in itertools.permutations(range(len(tsp_data)))]
    else:
        routes = [np.random.permutation(range(len(tsp_data))) for _ in range(max_number)]
        return [get_pathlength_for_route(p, tsp_data) for p in routes]

def brute_force_minima(tsp_data):
    """Test all connection graphs and outputs returns shortest path and shortest pathlength.

    Input:
        tsp_data    array   distance between points

    Output:
        length      float   length of shortest path

    >>> brute_force_minima([[0., 1., .5], [1., 0., .3], [.5, .3, 0.]])
    1.8
    """
    if isinstance(tsp_data, list):
        tsp_data = np.array(tsp_data)
    return min(get_all_routes(tsp_data))


def column_valid(state, n_cities):
    """Check whether state is column_valid.

    Input:
        state       list    binary representation of the state
                    int     state of the network when interpreting the binary as int
        n_cities    int     number of cities of the TSP

    Output:
        valid       bool    True if state obeys the TSP column restrictions
    >>> column_valid([0,0,0,1, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    True
    >>> column_valid([0,0,1,0, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    False
    >>> column_valid([0,0,0,0, 0,1,0,1, 1,0,0,0, 0,0,1,0], 4)
    True
    >>> column_valid([0,0,1,1, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    False
    """
    state = misc.get_statelist(state, n_cities*n_cities)
    valid = True
    for i in range(n_cities):
        valid *= np.sum(state[i::n_cities])==1
    return bool(valid)


def row_valid(state, n_cities):
    """Check whether state is row_valid.

    Input:
        state       list    binary representation of the state
        n_cities    int     number of cities of the TSP

    Output:
        valid       bool    True if state obeys the TSP row restrictions

    ### TODO: Rewrite test for all input types and valid checks,
    ###         introduce a make_statelist function
    >>> row_valid([0,0,0,1, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    True
    >>> row_valid([0,0,1,0, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    True
    >>> row_valid([0,0,0,0, 0,1,0,1, 1,0,0,0, 0,0,1,0], 4)
    False
    >>> row_valid([0,0,1,1, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    False
    """
    state = misc.get_statelist(state, n_cities*n_cities)
    valid = True
    for i in range(n_cities):
        valid *= np.sum(state[i*n_cities:(i+1)*n_cities])==1
    return bool(valid)


def number_valid(state, n_cities):
    """Check whether state is column_valid.

    Input:
        state       list    binary representation of the state
        n_cities    int     number of cities of the TSP

    Output:
        valid       bool    True if state obeys the TSP column restrictions
    >>> number_valid([0,0,0,1, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    True
    >>> number_valid([0,0,1,0, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    True
    >>> number_valid([0,0,0,0, 0,1,0,1, 1,0,0,0, 0,0,1,0], 4)
    True
    >>> number_valid([0,0,1,1, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    False
    >>> number_valid(23, 4)
    True
    >>> number_valid(22, 4)
    False
    """
    state = misc.get_statelist(state, n_cities*n_cities)
    return np.sum(state)==n_cities


def valid(state, n_cities):
    """Check validity of state."""
    return (row_valid(state, n_cities),
            column_valid(state, n_cities),
            number_valid(state, n_cities))


def check_validity_of_minima(W, b, verbose=False):
    n_cities = len(b)
    minimal_states = analysis.get_minmal_energy_states(W, b)
    valids = []
    column_fail = []
    row_fail = []
    number_fail = []
    for ms in minimal_states:
        sms = '{0:0{width}b}'.format(ms, width=n_cities*n_cities)
        bms = [ int(b) for b in sms ]
        cva, rva, nva = valid(ms, n_cities)
        if not cva:
            column_fail.append(ms)
        if not rva:
            row_fail.append(ms)
        if not nva:
            number_fail.append(ms)
        if cva and rva and nva:
            valids.append(ms)

    print("{} minimal energy states available".format(len(minimal_states)))
    print(" of those:")
    s = " {} valid\n {} rowfailed\n {} columnfailed\n"
    s += " {} numberfailed"
    s = s.format(   len(valids), len(row_fail),
                    len(column_fail), len(number_fail))
    print(s)
    if verbose:
        print("Valid ones: ", valids)
        print("number: ", number_fail)
        print("row: ", row_fail)

    return minimal_states, valids, row_fail, column_fail, number_fail


def plot(plotname, state_freq_dict, tsp_data, nbins=30, min_frequency=40):
    n_cities = len(tsp_data)
    states = [k for k,v in state_freq_dict.iteritems() if v>min_frequency]
    frequencies = [v for k,v in state_freq_dict.iteritems() if v>min_frequency]

    valid_states = [s for s in states if all(valid(s, n_cities))]
    valid_frequencies = [v for s,v in zip(states, frequencies)
                                if all(valid(s, n_cities))]
    dists = [get_pathlength_from_state(s, tsp_data)[1] for s in states]
    print(len(valid_states)/len(states))

    rls = get_all_routes(tsp_data)

    with PdfPages(plotname) as pdf:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        n, bins, patches = ax.hist(rls, bins=nbins, normed=True, label='all')
        ax.hist(dists, bins, alpha=.5, normed=True, label='sampled')
        ax.legend()
        plt.savefig(pdf, format='pdf')

if __name__ == '__main__':
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv):
        d = readtsp('tsptest')
        print(create_general_tsp(len(d), 1., 1., 1., 1., d))

