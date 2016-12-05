"""This module implements the TSP problem for neural networks."""
import sys
import yaml
import numpy as np
import itertools

import analysis
import misc


### input/output functions
def readtsp(filename):
    """Return the distance matrix in filename."""
    d = np.loadtxt(filename)
    return d


### misc functions
def double_index_to_single(x, i, n_cities):
    """Transform double index (city, position) in single index.

    >>> double_index_to_single(0, 0, 5)
    0
    >>> double_index_to_single(1, 0, 5)
    5
    >>> double_index_to_single(1, 1, 5)
    6
    >>> double_index_to_single(6, 1, 4)
    9
    >>> double_index_to_single(6, 7, 5)
    7
    """
    return ( (x%n_cities) *n_cities + (i%n_cities) )


def single_index_to_double(n, n_cities):
    """Transform single index i to double index (city, position).

    >>> single_index_to_double(7, 5)
    (1, 2)
    >>> single_index_to_double(17, 4)
    (0, 1)
    """
    return int(n/n_cities) % n_cities, n%n_cities


def row_connections(i,j,x,y):
    """Return True if the entry penalizes multiple positions of a city in a route.

    Expects all coordinates to be 0<= {i,j,x,y} <n_cities

    >>> row_connections(0,0,0,0)
    0
    >>> row_connections(0,0,0,1)
    0
    >>> row_connections(0,1,0,1)
    0
    >>> row_connections(0,1,0,0)
    1
    >>> row_connections(2,1,0,0)
    1
    """
    return (x==y)*(1-(i==j))


def column_connections(i,j,x,y):
    """Return True if the entry penalizes multiple cities at a single position in a route.

    Expects all coordinates to be 0<= {i,j,x,y} <n_cities

    >>> column_connections(0,0,0,0)
    0
    >>> column_connections(0,1,0,0)
    0
    >>> column_connections(0,1,0,1)
    0
    >>> column_connections(0,0,0,1)
    1
    >>> column_connections(0,0,2,1)
    1
    """
    return (i==j)*(1-(x==y))


def dataterm(i,j,x,y, tsp_data):
    """Return the appropriate dataterm, if entry penalizes distance."""
    n_cities=len(tsp_data)
    return tsp_data[x,y] * ((j==(i+1)%n_cities)+(j==(i-1)%n_cities))


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
        tsp_data = np.loadtxt(tsp_datafile)
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
    return min(get_pathlength_for_route(p, tsp_data) for p in itertools.permutations(range(len(tsp_data))))


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
    if isinstance(state, int):
        state = misc.statelist_from_int(state, n_cities*n_cities)
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
    if isinstance(state, int):
        state = misc.statelist_from_int(state, n_cities*n_cities)
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
    if isinstance(state, int):
        state = misc.statelist_from_int(state, n_cities*n_cities)
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


if __name__ == '__main__':
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv):
        d = readtsp('tsptest')
        print(create_general_tsp(len(d), 1., 1., 1., 1., d))

