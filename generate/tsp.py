
import sys
import yaml
import numpy as np
import itertools

import analysis


def readtsp(filename):
    """Returns the distance matrix in filename"""
    d = np.loadtxt(filename)
    return d


def double_index_to_single(x, i, n_cities):
    return x*n_cities+i


def single_index_to_double(n, n_cities):
    return n%n_cities, int(n/n_cities)


def row_connections(i,j,x,y):
    """

    >>> row_connections(0,0,0,0)
    0
    >>> row_connections(0,0,0,1)
    0
    >>> row_connections(0,1,0,1)
    0
    >>> row_connections(0,1,0,0)
    1
    """
    return (x==y)*(1-(i==j))


def column_connections(i,j,x,y):
    return (i==j)*(1-(x==y))


def dataterm(i,j,x,y, tsp_data):
    # return tsp_data[i,j] * ((y==x+1)+(y==x-1))
    n_cities=len(tsp_data)
    return tsp_data[x,y] * ((j==(i+1)%n_cities)+(j==(i-1)%n_cities))


def create_general_tsp(n_cities, A, B, C, D, tsp_data, fix_starting_point=False):
    W = np.zeros((n_cities*n_cities, n_cities*n_cities))
    for i,j,x,y in itertools.product(xrange(n_cities), repeat=4):
        wi = double_index_to_single(i,x, n_cities)
        wj = double_index_to_single(j,y, n_cities)
        W[wi, wj] -= A*row_connections(i,j,x,y)
        W[wi, wj] -= B*column_connections(i,j,x,y)
        W[wi, wj] -= C#*(1-(wi==wj))
        W[wi, wj] -= D*dataterm(i,j,x,y, tsp_data)

    b = np.ones(n_cities*n_cities)*C*n_cities
    if fix_starting_point:
        b[0] += C
    return W, b


def get_pathlength_for_route(route, tsp_data):
    return sum([tsp_data[r1,r2] for r1, r2 in zip(route[1:],route[:-1])] + [tsp_data[route[-1], route[0]]])



def get_pathlength_from_state(state, tsp_data):
    n_cities = len(tsp_data)
    if isinstance(state, int):
        state = '{0:0{width}b}'.format(state, width=n_cities*n_cities)
    bstate = np.array([int(s) for s in state]).reshape((n_cities, n_cities)).tolist()
    route = [line.index(1) for line in bstate]
    d = get_pathlength_for_route(route, tsp_data)
    return route, d

def brute_force_minima(tsp_data):
    """Tests all connection graphs and outputs returns shortest path and shortest pathlength"""
    return min(get_pathlength_for_route(p, tsp_data) for p in itertools.permutations(range(len(tsp_data))))


def column_valid(state, n_cities):
    """Checks whether state is column_valid

    Input:
        state       list    binary representation of the state 
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
    valid = True
    for i in range(n_cities):
        valid *= np.sum(state[i::n_cities])==1
    return bool(valid)

def row_valid(state, n_cities):
    """Checks whether state is row_valid

    Input:
        state       list    binary representation of the state 
        n_cities    int     number of cities of the TSP

    Output:
        valid       bool    True if state obeys the TSP row restrictions
    >>> row_valid([0,0,0,1, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    True
    >>> row_valid([0,0,1,0, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    True
    >>> row_valid([0,0,0,0, 0,1,0,1, 1,0,0,0, 0,0,1,0], 4)
    False
    >>> row_valid([0,0,1,1, 0,1,0,0, 1,0,0,0, 0,0,1,0], 4)
    False
    """
    valid = True
    for i in range(n_cities):
        valid *= np.sum(state[i*n_cities:(i+1)*n_cities])==1
    return bool(valid)

def number_valid(state, n_cities):
    """Checks whether state is column_valid

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
    """
    return np.sum(state)==n_cities

def check_validity_of_minima(W, b, n_cities):
    e = analysis.energy_for_network(W, b)
    minimal_states = np.nonzero(e==min(e))[0]
    valids = []
    column_fail = []
    row_fail = []
    number_fail = []
    for ms in minimal_states:
        sms = '{0:0{width}b}'.format(ms, width=n_cities*n_cities)
        bms = [ int(b) for b in sms ]
        bvalid = True
        if not column_valid(bms, n_cities):
            column_fail.append(ms)
            bvalid = False
        if not row_valid(bms, n_cities):
            row_fail.append(ms)
            bvalid = False
        if not number_valid(bms, n_cities):
            number_fail.append(ms)
            bvalid = False
        if bvalid:
            valids.append(ms)

    print("{} minimal energy states available".format(len(minimal_states)))
    print(" of those:")
    s = " {} valid\n {} rowfailed\n {} columnfailed\n"
    s += " {} numberfailed"
    s = s.format(   len(valids), len(row_fail), 
                    len(column_fail), len(number_fail))
    print(s)
    print("Valid ones: ", valids)
    print("number: ", number_fail)
    print("row: ", row_fail)


    return minimal_states


if __name__ == '__main__':
    if len(sys.argv)==1:
        import doctest
        print(doctest.testmod())
    elif len(sys.argv):
        d = readtsp('tsptest')
        print(create_general_tsp(len(d), 1., 1., 1., 1., d))

