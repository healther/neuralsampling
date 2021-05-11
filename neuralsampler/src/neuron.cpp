#include <iostream>

#include <math.h>

#include "neuron.h"



Neuron::Neuron(const int64_t _tauref, const int64_t _tausyn,
    const int64_t _delay,
    const int64_t _state,
    const TActivation _activation_type,
    const TInteraction _interaction_type):
    Neuron(_tauref, _tausyn, _delay, _state, ConfigNeuronUpdate(), _activation_type, _interaction_type, MemoryLess)
{
}


Neuron::Neuron(const int64_t _tauref, const int64_t _tausyn,
    const int64_t _delay, const int64_t _state,
    const ConfigNeuronUpdate _neuronUpdate,
    const TActivation _activation_type,
    const TInteraction _interaction_type,
    const TIntegration _integration_type):
    Neuron(_tauref, _tausyn, _delay, 1, _state, _neuronUpdate, _activation_type, _interaction_type, _integration_type)
{
}

Neuron::Neuron(const int64_t _tauref, const int64_t _tausyn,
    const int64_t _delay, const int64_t _num_interactions,
    const int64_t _state,
    const ConfigNeuronUpdate _neuronUpdate,
    const TActivation _activation_type,
    const TInteraction _interaction_type,
    const TIntegration _integration_type):
    activation_type(_activation_type),
    interaction_type(_interaction_type),
    integration_type(_integration_type),
    neuronUpdate(_neuronUpdate),
    tauref(_tauref),
    tausyn(_tausyn),
    delay(_delay),
    num_interactions(_num_interactions),
    taurefsyn((double)_tauref/(double)_tausyn),
    taurefsynexp(std::exp(-(double)_tauref/(double)_tausyn)),
    interactions(_delay, 0.)
{
    nspikes = 0;
    state.resize(num_interactions);
    // fill extra states with something large, such that it does not
    // significantly influence the resulting interaction
    std::fill(state.begin(), state.end(), 9999);
    state[0] = _state;
    for (int64_t i = 0; i < delay; ++i)
    {
        update_interaction();
    }
    membrane_potential = 0.;
}



void Neuron::update_state(const double pot)
{
    double effective_pot = pot;
    if ( integration_type == OU )
    {
        // membrane_potential tracks the OU part of the membrane
        // with OU parameters being held in neuronUpdate
        double noise = random_normal(mt_random);
        membrane_potential += (neuronUpdate.mu - membrane_potential) * neuronUpdate.theta + neuronUpdate.sigma * noise;
        effective_pot += membrane_potential;
    }

    for (int64_t i = 0; i < num_interactions; ++i)
    {
        state[i]++;
        // A neuron is not allowed to spike if it is in the refractory time,
        // i.e. if its state is larger than zero, the statespace here is
        // {0, ..., infty}, with {0, ..., tauref-1} being the refractory
        // states. Therefore starting with the state tauref all upper states
        // are allowed to spike.
    }
    if (state[0] >= tauref)
    {
        if (spike(effective_pot))
        {
            // update the last interaction, which will be dropped
            state[num_interactions-1] = 0;
        }
        // rotate such that the last interaction becomes the first
        std::rotate(state.rbegin(), state.rbegin() + 1, state.rend());
    }
}

void Neuron::update_interaction()
{
    double total_interaction = 0.;
    for (int64_t i = 0; i < num_interactions; ++i)
    {
        double relstateexp = std::exp(-(double)state[i]/(double)tausyn);
        double interaction = (state[i] < tauref);
        if (interaction_type==Exp) {
            interaction = taurefsyn * relstateexp/(1.-taurefsynexp);
        } else if (interaction_type==Rect) {
            interaction = (state[i] < tauref);
        } else if (interaction_type==Cuto) {
            if (state[i] < tauref)
            {
                interaction = taurefsyn * relstateexp/(1.-taurefsynexp);
            } else {
                interaction = 0.;
            }
        } else if (interaction_type==Tail) {
            if (state[i] >= tauref)
            {
                interaction = taurefsyn * relstateexp/(1.-taurefsynexp);
            } else {
                interaction = 1.;
            }
        }
        total_interaction += interaction;
    }
    interactions.add_entry(total_interaction);
}



int Neuron::spike(const double pot)
{
    int bspike = false;
    if (Step==activation_type) {
        bspike = pot>0.;
    } else {
        double r = random_double(mt_random);
        bspike = activation(pot - std::log(tauref)) > r;
    }
    nspikes += bspike;
    return bspike;
}

bool Neuron::has_spiked()
{
    return state[0]==0;
}



int64_t Neuron::get_internalstate()
{
    return state[0];
}

int64_t Neuron::get_state()
{
    return (state[0]<tauref);
}

int64_t Neuron::get_nspikes()
{
    return nspikes;
}



double Neuron::get_interaction()
{
    return interactions.return_entry();
}

double Neuron::activation(const double pot)
{
    if (Log==activation_type) {
        return 1./(1.+std::exp(-pot));
    } else if (Erf==activation_type) {
        return .5 + .5*std::erf(.41631118*pot);
    } else {
        throw;
    }
}

