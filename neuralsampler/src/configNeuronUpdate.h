#ifndef CONFIG_NEURON_UPDATE_H
#define CONFIG_NEURON_UPDATE_H

#include <stdint.h>

#include "type.h"

class ConfigNeuronUpdate
{
public:
    double theta;
    double mu;
    double sigma;
    int64_t nsteps;
    double tau;

    ConfigNeuronUpdate() {theta=1.; mu=0.; sigma=0.;};
    ConfigNeuronUpdate(const double _theta, const double _mu, 
                       const double _sigma, const int64_t _nsteps) {
    theta = _theta;
    mu = _mu;
    sigma = _sigma;
    nsteps = _nsteps;
    tau = 1. / (double) nsteps;
    };
    ~ConfigNeuronUpdate() {};
};


#endif // CONFIG_NEURON_UPDATE_H