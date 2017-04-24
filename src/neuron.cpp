#include <iostream>

#include <math.h>

#include "neuron.h"




Neuron::Neuron(const int _tauref, const int _tausyn, const int _delay, const int _state,
    const TActivation _activation_type, const TInteraction _interaction_type):
    activation_type(_activation_type),
    interaction_type(_interaction_type),
    tauref(_tauref),
    tausyn(_tausyn),
    delay(_delay),
    interactions(_delay, 0.)
{
    state = _state;
    for (int i = 0; i < delay; ++i)
    {
        update_interaction();
    }
}



void Neuron::update_state(const double pot)
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
    double relstate = (double)state/(double)tauref;
    double interaction = (relstate < 1.);
    if (interaction_type==Exp) {
        interaction = (double)tauref/(double)tausyn * std::exp(-relstate)/(1.-std::exp(-(double)tauref/(double)tausyn));
    } else if (interaction_type==Rect) {
        interaction = (state < tauref);
    } else if (interaction_type==Cuto) {
        if (state < tauref)
        {
            interaction = (double)tauref/(double)tausyn * std::exp(-relstate)/(1.-std::exp(-(double)tauref/(double)tausyn));
        } else {
            interaction = 0.;
        }
    } else if (interaction_type==Tail) {
        if (state >= tauref)
        {
            interaction = (double)tauref/(double)tausyn * std::exp(-relstate)/(1.-std::exp(-(double)tauref/(double)tausyn));
        } else {
            interaction = 1.;
        }
    }
    interactions.add_entry(interaction);
}



bool Neuron::spike(const double pot)
{
    bool bspike = false;
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
    return state==0;
}



int Neuron::get_internalstate()
{
    return state;
}

int Neuron::get_state()
{
    return (state<tauref);
}

int Neuron::get_nspikes()
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

