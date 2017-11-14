#include <iostream>
#include <iomanip>
#include <vector>
#include <cmath>

#include <random>
#include <algorithm>

#include "network.h"


Network::Network(std::vector<double> &_biases,
            std::vector<std::vector<double> > &_weights,
            std::vector<int64_t> &_initialstate,
            Config config):
    output_scheme(config.outputScheme),
    update_scheme(config.updateScheme),
    neuron_activation_type(config.neuronActivationType),
    neuron_interaction_type(config.neuronInteractionType)
{
    boptimized = false; // TODO: make const
    biases = _biases;
    weights = _weights;
    tauref = config.tauref;
    tausyn = config.tausyn;
    delay = config.delay;
    outputEnv = config.outputEnv;

    neurons.reserve(biases.size());
    states.resize(biases.size());
    for (std::size_t i = 0; i < biases.size(); ++i)
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
    std::size_t n_connections = 0;
    connected_neuron_ids.resize(biases.size());
    for (std::size_t i = 0; i < biases.size(); ++i)
    {
        for (std::size_t j = 0; j < biases.size(); ++j)
        {
            if (fabs(weights[i][j])>1E-14)
            {
                connected_neuron_ids[i].push_back(j);
                n_connections++;
            }
        }
    }
    // check if network is sparse enough
    if (n_connections * 1.5 < biases.size() * biases.size())
    {
        boptimized = true;
    }
}

void Network::produce_header(std::ostream& stream)
{
    stream << "# using sparse connectivity: " << boptimized << "\n";
    if (output_scheme==SummarySpikes) {
        stream << "# only summary output\n";
    } else {
        stream << "# ";
        if (outputEnv) {
            stream << "Temperature Iext ";
        }
        if (output_scheme==MeanActivityOutput) {
            stream << "Activity\n# \n";
        } else if (output_scheme==MeanActivityEnergyOutput) {
            stream << "Activity Energy\n# \n";
        } else if (output_scheme==BinaryStateOutput) {
            stream << "NeuronStates\n# \n";
        } else if (output_scheme==SpikesOutput) {
            stream << "Spikes\n# \n";
        } else {
            throw;
        }
    }
}

void Network::produce_output(std::ostream& stream, double T, double Iext)
{
    if (output_scheme==SummarySpikes) {

    } else {
        if (outputEnv) {
            stream << T << " " << Iext << " --- ";
        }
        if (output_scheme==MeanActivityOutput) {
            int64_t activity = 0;
            for (std::size_t i = 0; i < biases.size(); ++i)
            {
                activity += neurons[i].get_state();
            }
            stream << activity << "\n";
        } else if (output_scheme==MeanActivityEnergyOutput) {
            int64_t activity = 0;
            double energy = 0.0;
            for (std::size_t i = 0; i < biases.size(); ++i)
            {
                activity += neurons[i].get_state();
                energy += -0.5 * (get_potential_for_neuronid(i) + biases[i]) * neurons[i].get_state();
            }
            stream << activity << " " << energy << "\n";
        } else if (output_scheme==BinaryStateOutput) {
            for (std::size_t i = 0; i < biases.size(); ++i)
            {
                stream << neurons[i].get_state();
            }
            stream << "\n";
        } else if (output_scheme==SpikesOutput) {
            for (std::size_t i = 0; i < biases.size(); ++i) {
                if (neurons[i].has_spiked()) {
                    stream << i << " ";
                }
            }
            stream << "\n";
        } else {
            throw;
        }
    }
}

void Network::produce_summary(std::ostream& stream)
{
    stream.fill('0');
    stream << "____End of simulation____\n\n\nSummary:\n";
    stream << "NeuronNr NumberOfSpikes\n-----------\n";
    for (std::size_t i = 0; i < biases.size(); ++i) {
        stream << std::setw(5) << i << " " << std::setw(12) << neurons[i].get_nspikes() << "\n";
    }
}

void Network::get_state()
{
    for (std::size_t i = 0; i < biases.size(); ++i)
    {
        states[i] = neurons[i].get_state();
    }
}

void Network::get_internalstate()
{
    for (std::size_t i = 0; i < biases.size(); ++i)
    {
        states[i] = neurons[i].get_internalstate();
    }
}

std::vector<int64_t> Network::get_update_inds() {
    std::vector<int64_t> update_inds(biases.size()) ;

    if (update_scheme==Random) {
        std::uniform_int_distribution<int64_t> random_ints(0, biases.size()-1);
        for (std::size_t i = 0; i < biases.size(); ++i) {
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

double Network::get_potential_for_neuronid(int64_t neuronid) {
    double pot = biases[neuronid];

    if (boptimized)
    {
        for (auto conid = connected_neuron_ids[neuronid].begin(); conid != connected_neuron_ids[neuronid].end(); ++conid)
        {
            pot += neurons[*conid].get_interaction() * weights[neuronid][*conid];
        }
    } else {    // not boptimized
        for (std::size_t j = 0; j < biases.size(); ++j)
        {
            pot += neurons[j].get_interaction() * weights[neuronid][j];
        }
    }

    return pot;
}

void Network::update_state(double T)
{
    update_state(T, 0.);
}

void Network::update_state(double T, double Iext)
{
    // generate ids to update (depends on the update scheme)
    std::vector<int64_t> update_inds = get_update_inds() ;

    // update neurons in sequence determined above
    for (std::size_t i = 0; i < biases.size(); ++i)
    {
        int64_t neuronid = update_inds[i];
        double pot = get_potential_for_neuronid(neuronid) + Iext;
        neurons[neuronid].update_state(pot/T);
        neurons[neuronid].update_interaction();
    }
}

bool Network::_check_consistency()
{
    return 1;
}

