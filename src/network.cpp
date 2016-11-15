#include <iostream>
#include <vector>
#include <cmath>

#include <random>
#include <algorithm>

#include "neuron.h"
#include "network.h"



Network::Network(std::vector<double> &_biases, 
            std::vector<std::vector<double> > &_weights,
            std::vector<int> &_initialstate,
            int _tauref, int _tausyn,
            TUpdateScheme _update_scheme,
            TActivation _neuron_activation_type,
            TInteraction _neuron_interaction_type):
    update_scheme(_update_scheme),
    neuron_activation_type(_neuron_activation_type),
    neuron_interaction_type(_neuron_interaction_type)
{
    boptimized = false; // TODO: make const
    biases = _biases;
    weights = _weights;
    tauref = _tauref;
    tausyn = _tausyn;
    neurons.reserve(biases.size());
    states.resize(biases.size());
    for (unsigned int i = 0; i < biases.size(); ++i)
    {
        neurons.push_back(
            Neuron(tauref, tausyn, _initialstate[i], 
            neuron_activation_type, neuron_interaction_type)
        );
        states[i] = neurons[i].get_state();
    }

    generate_connected_neuron_ids();
}

void Network::generate_connected_neuron_ids()
{
    int n_connections = 0;
    connected_neuron_ids.resize(biases.size());
    for (unsigned int i = 0; i < biases.size(); ++i)
    {
        for (unsigned int j = 0; j < biases.size(); ++j)
        {
            if (fabs(weights[i][j])>1E-14)
            {
                connected_neuron_ids[i].push_back(j);
                n_connections++;
            }
        }
    }
    // check if network is sparse enough
    if (n_connections*4<biases.size()*biases.size())
    {
        boptimized = true;
    }
}

void Network::get_state()
{
    for (unsigned int i = 0; i < biases.size(); ++i)
    {
        states[i] = neurons[i].get_state();
    }
}

void Network::get_internalstate()
{
    for (unsigned int i = 0; i < biases.size(); ++i)
    {
        states[i] = neurons[i].get_internalstate();
    }
}

void Network::update_state(double T)
{
    std::vector<int> update_inds(biases.size()) ;

    if (update_scheme==Random) {
        std::uniform_int_distribution<int> random_ints(0, biases.size());
        for (unsigned int i = 0; i < biases.size(); ++i) {
            update_inds[i] = random_ints(mt_random);
        }
    } else {
        std::iota (std::begin(update_inds), std::end(update_inds), 0);
        if (update_scheme==BatchRandom) {
            std::shuffle ( update_inds.begin(), update_inds.end(), mt_random);
        }
    }

    for (unsigned int i = 0; i < biases.size(); ++i)
    {
        int ii = update_inds[i];
        double pot = biases[ii];
        if (boptimized)
        {
            int conid;
            for (unsigned int j = 0; j < connected_neuron_ids[ii].size(); ++j)
            {
                conid = connected_neuron_ids[ii][j];
                pot += neurons[conid].get_interaction() * weights[i][conid];
            }
        } else {    // not boptimized
            for (unsigned int j = 0; j < biases.size(); ++j)
            {
                pot += neurons[j].get_interaction() * weights[ii][j];
            }
        }   // endif boptimized
        neurons[ii].update_state(pot/T);
        neurons[ii].update_interaction();
    }
}

bool Network::_check_consistency()
{
    return 1;
}

