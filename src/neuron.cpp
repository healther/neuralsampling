#include <iostream>

#include <math.h>

#include "neuron.h"




Neuron::Neuron(const int _tauref, const int _tausyn, const int _state,
    const TActivation _activation_type, const TInteraction _interaction_type):
    tauref(_tauref),
    tausyn(_tausyn),
    activation_type(_activation_type),
    interaction_type(_interaction_type)
{
    state = _state;
    update_interaction();
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
    interaction = (relstate < 1.);
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
}



bool Neuron::spike(const double pot)
{
    double r = random_double(mt_random);
    return activation(pot - std::log(tauref)) > r;
}



int Neuron::get_internalstate()
{
    return state;
}

int Neuron::get_state()
{
    return (state<tauref);
}



double Neuron::get_interaction()
{
    return interaction;
}

double Neuron::activation(const double pot)
{
    if (0==interaction_type) {
        return 1./(1.+std::exp(-pot));
    } else if (1==interaction_type) {
        return .5 + .5*std::erf(.41631118*pot);
    }
}

