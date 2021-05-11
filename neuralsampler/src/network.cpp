#include <iostream>
#include <iomanip>
#include <vector>
#include <cmath>

#include <random>
#include <algorithm>

#include "network.h"


Network::Network(const std::vector<double> &_biases,
                 const std::vector<std::vector<double> > &_weights,
                 const std::vector<int64_t> &_initialstate,
                 const Config& config):
    output_scheme(config.output.outputScheme),
    update_scheme(config.updateScheme),
    outputIndexes(config.output.outputIndexes),
    biases(_biases),
    weights(_weights)
{
    outputEnv = config.output.outputEnv;

    neurons.reserve(biases.size());
    states.resize(outputIndexes.size());
    for (std::size_t i = 0; i < biases.size(); ++i)
    {
        neurons.push_back(
            Neuron(config.tauref, config.tausyn, config.delay,
                   config.num_interactions,
                   _initialstate[i], config.neuronUpdate,
                   config.neuronActivationType,
                   config.neuronInteractionType, config.neuronIntegrationType)
        );
    }
    get_state();

    boptimized = generate_connected_neuron_ids();  // TODO: make const
}

bool Network::generate_connected_neuron_ids()
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
        return true;
    } else {
        return false;
    }
}

void Network::produce_header(std::ostream& stream)
{
    stream << "# using sparse connectivity: " << boptimized << "\n";
    if (output_scheme==SummarySpikes || output_scheme==SummaryStates) {
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
        } else if (output_scheme==InternalStateOutput) {
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

    } else if (output_scheme==SummaryStates) {
        summary_states[states]++;
    } else {
        if (outputEnv) {
            stream << T << " " << Iext << " --- ";
        }
        if (output_scheme==MeanActivityOutput) {
            int64_t activity = 0;
            for (std::size_t i = 0; i < biases.size(); ++i)
            {
                activity += states[i];
            }
            stream << activity << "\n";
        } else if (output_scheme==MeanActivityEnergyOutput) {
            int64_t activity = 0;
            double energy = 0.0;
            for (std::size_t i = 0; i < biases.size(); ++i)
            {
                activity += states[i];
                energy += -0.5 * (get_potential_for_neuronid(i) + biases[i]) * neurons[i].get_state();
            }
            stream << activity << " " << energy << "\n";
        } else if (output_scheme==BinaryStateOutput) {
            for (std::size_t i = 0; i < biases.size(); ++i)
            {
                stream << states[i];
            }
            stream << "\n";
        } else if (output_scheme==InternalStateOutput) {
            for (std::size_t i = 0; i < biases.size(); ++i)
            {
                stream << states[i] << " ";
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
    stream << "Summary:\n";
    stream << "NeuronNr NumberOfSpikes\n-----------\n";
    for (std::size_t i = 0; i < biases.size(); ++i) {
        stream << std::setw(5) << i << " " << std::setw(12) << neurons[i].get_nspikes() << "\n";
    }
    stream << "Internalstate:\n";
    for (std::size_t i = 0; i < biases.size(); ++i) {
        stream << std::setw(5) << i << " " << std::setw(5) << neurons[i].get_internalstate() << "\n";
    }
    if (output_scheme==SummaryStates) {
        stream << "Summary States:\n";
        for (auto it=summary_states.begin(); it!=summary_states.end(); ++it) {
            for (auto it2=it->first.begin(); it2!=it->first.end(); ++it2) {
                stream << *it2;
            }
            stream << " : " << it->second << "\n";
        }
        summary_states[states]++;
    }
}

void Network::get_state()
{
    if (output_scheme==InternalStateOutput) {
        get_internalstate();
    } else {
        get_binary_state();
    }
}

void Network::get_binary_state()
{
    for (std::size_t i = 0; i < outputIndexes.size(); ++i)
    {
        states[i] = neurons[outputIndexes[i]].get_state();
    }
}

void Network::get_internalstate()
{
    for (std::size_t i = 0; i < outputIndexes.size(); ++i)
    {
        states[i] = neurons[outputIndexes[i]].get_internalstate();
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
        for (auto conid = connected_neuron_ids[neuronid].begin();
             conid != connected_neuron_ids[neuronid].end(); ++conid)
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

