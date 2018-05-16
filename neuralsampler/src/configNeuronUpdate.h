#ifndef CONFIG_NEURON_UPDATE_H
#define CONFIG_NEURON_UPDATE_H

#include "type.h"

class ConfigNeuronUpdate
{
public:
    double theta;
    double mu;
    double sigma;

    ConfigNeuronUpdate() {theta=0.; mu=0.; sigma=0.;};
    ConfigNeuronUpdate(const double _theta, const double _mu, 
    				   const double _sigma) {
    theta = _theta;
    mu = _mu;
    sigma = _sigma;
    };
    ~ConfigNeuronUpdate() {};
};


#endif // CONFIG_NEURON_UPDATE_H