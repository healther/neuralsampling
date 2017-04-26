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
            int _tauref, int _tausyn, int _delay,
            TOutputScheme _output_scheme,
            TUpdateScheme _update_scheme,
            TActivation _neuron_activation_type,
            TInteraction _neuron_interaction_type):
    output_scheme(_output_scheme),
    update_scheme(_update_scheme),
    neuron_activation_type(_neuron_activation_type),
    neuron_interaction_type(_neuron_interaction_type)
{
    boptimized = false; // TODO: make const
    biases = _biases;
    weights = _weights;
    tauref = _tauref;
    tausyn = _tausyn;
    delay = _delay;
    neurons.reserve(biases.size());
    states.resize(biases.size());
    for (unsigned int i = 0; i < biases.size(); ++i)
    {
        neurons.push_back(
            Neuron(tauref, tausyn, delay, _initialstate[i],
            neuron_activation_type, neuron_interaction_type)
        );
        states[i] = neurons[i].get_state();
    }

    generate_connected_neuron_ids();
}

void Network::generate_connected_neuron_ids()
{
    unsigned int n_connections = 0;
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
    if (n_connections*4 < biases.size()*biases.size())
    {
        boptimized = true;
    }
}

void Network::produce_output(std::ostream& stream)
{
    if (output_scheme==MeanActivityOutput) {
        int activity = 0;
        for (unsigned int i = 0; i < biases.size(); ++i)
        {
            activity += neurons[i].get_state();
        }
        stream << activity << "\n";
    } else if (output_scheme==BinaryStateOutput) {
        for (unsigned int i = 0; i < biases.size(); ++i)
        {
            stream << neurons[i].get_state();
        }
        stream << "\n";
    } else if (output_scheme==SpikesOutput) {
        for (unsigned int i = 0; i < biases.size(); ++i) {
            if (neurons[i].has_spiked()) {
                stream << i << " ";
            }
        }
        stream << "\n";
    } else if (output_scheme==SummarySpikes) {

    } else {
        throw;
    }
}

void Network::produce_summary(std::ostream& stream)
{
    if (output_scheme==SummarySpikes) {
        for (unsigned int i = 0; i < biases.size(); ++i) {
            stream << neurons[i].get_nspikes() << " ";
        }
        stream << std::endl;
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

std::vector<int> Network::get_update_inds() {
    std::vector<int> update_inds(biases.size()) ;

    if (update_scheme==Random) {
        std::uniform_int_distribution<int> random_ints(0, biases.size()-1);
        for (unsigned int i = 0; i < biases.size(); ++i) {
            update_inds[i] = random_ints(mt_random);
        }
    } else {
        std::iota (std::begin(update_inds), std::end(update_inds), 0);
        if (update_scheme==BatchRandom) {
            std::shuffle ( update_inds.begin(), update_inds.end(), mt_random);
        }
    }

    return update_inds;
}

double Network::get_potential_for_neuronid(unsigned int neuronid) {
    double pot = biases[neuronid];

    if (boptimized)
    {
        int conid;
        for (unsigned int j = 0; j < connected_neuron_ids[neuronid].size(); ++j)
        {
            conid = connected_neuron_ids[neuronid][j];
            pot += neurons[conid].get_interaction() * weights[neuronid][conid];
        }
    } else {    // not boptimized
        for (unsigned int j = 0; j < biases.size(); ++j)
        {
            pot += neurons[j].get_interaction() * weights[neuronid][j];
        }
    }

    return pot;
}

void Network::update_state(double T)
{
    // generate ids to update (depends on the update scheme)
    std::vector<int> update_inds = get_update_inds() ;

    // update neurons in sequence determined above
    for (unsigned int i = 0; i < biases.size(); ++i)
    {
        int neuronid = update_inds[i];
        double pot = get_potential_for_neuronid(neuronid);
        neurons[neuronid].update_state(pot/T);
        neurons[neuronid].update_interaction();
    }
}

void Network::update_state(double T, double Iext)
{
    // generate ids to update (depends on the update scheme)
    std::vector<int> update_inds = get_update_inds() ;

    // update neurons in sequence determined above
    for (unsigned int i = 0; i < biases.size(); ++i)
    {
        int neuronid = update_inds[i];
        double pot = get_potential_for_neuronid(neuronid) + Iext;
        neurons[neuronid].update_state(pot/T);
        neurons[neuronid].update_interaction();
    }
}

bool Network::_check_consistency()
{
    return 1;
}

