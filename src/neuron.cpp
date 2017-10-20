#include <iostream>

#include <math.h>

#include "neuron.h"




Neuron::Neuron(const int64_t _tauref, const int64_t _tausyn,
    const int64_t _delay, const int64_t _state,
    const TActivation _activation_type, const TInteraction _interaction_type):
    activation_type(_activation_type),
    interaction_type(_interaction_type),
    tauref(_tauref),
    tausyn(_tausyn),
    delay(_delay),
    interactions(_delay, 0.)
{
    nspikes = 0;
    state = _state;
    for (int64_t i = 0; i < delay; ++i)
    {
        update_interaction();
    }
}



void Neuron::update_state(const float pot)
{
    // std::cout << state << std::endl;
    state++;
    // A neuron is not allowed to spike if it is in the refractory time,
    // i.e. if its state is larger than zero, the statespace here is
    // {0, ..., infty}, with {0, ..., tauref-1} being the refractory
    // states. Therefore starting with the state tauref all upper states
    // are allowed to spike.
    if (state >= tauref)
    {
        if (spike(pot))
        {
            state = 0;
        }
    }
}

void Neuron::update_interaction()
{
    float relstate = (float)state/(float)tauref;
    float interaction = (relstate < 1.);
    if (interaction_type==Exp) {
        interaction = (float)tauref/(float)tausyn * std::exp(-relstate)/(1.-std::exp(-(float)tauref/(float)tausyn));
    } else if (interaction_type==Rect) {
        interaction = (state < tauref);
    } else if (interaction_type==Cuto) {
        if (state < tauref)
        {
            interaction = (float)tauref/(float)tausyn * std::exp(-relstate)/(1.-std::exp(-(float)tauref/(float)tausyn));
        } else {
            interaction = 0.;
        }
    } else if (interaction_type==Tail) {
        if (state >= tauref)
        {
            interaction = (float)tauref/(float)tausyn * std::exp(-relstate)/(1.-std::exp(-(float)tauref/(float)tausyn));
        } else {
            interaction = 1.;
        }
    }
    interactions.add_entry(interaction);
}



bool Neuron::spike(const float pot)
{
    bool bspike = false;
    if (Step==activation_type) {
        bspike = pot>0.;
    } else {
        float r = random_float(mt_random);
        bspike = activation(pot - std::log(tauref)) > r;
    }
    nspikes += bspike;
    return bspike;
}

bool Neuron::has_spiked()
{
    return state==0;
}



int64_t Neuron::get_internalstate()
{
    return state;
}

int64_t Neuron::get_state()
{
    return (state<tauref);
}

int64_t Neuron::get_nspikes()
{
    return nspikes;
}



float Neuron::get_interaction()
{
    return interactions.return_entry();
}

float Neuron::activation(const float pot)
{
    if (Log==activation_type) {
        return 1./(1.+std::exp(-pot));
    } else if (Erf==activation_type) {
        return .5 + .5*std::erf(.41631118*pot);
    } else {
        throw;
    }
}

