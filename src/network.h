#ifndef NETWORK_H
#define NETWORK_H

#include <vector>
#include <random>
#include <algorithm>

extern std::mt19937_64 mt_random;

#include "neuron.h"

class Network
{
private:
    const TActivation neuron_activation_type;
    const TInteraction neuron_interaction_type;

    std::vector<double> biases;
    std::vector<std::vector<double> > weights;
    std::vector<std::vector<int> > connected_neuron_ids;
    std::vector<Neuron> neurons;
    int tauref;
    int tausyn;
    bool boptimized;

    void generate_connected_neuron_ids();

public:
    Network(std::vector<double> &_biases, 
            std::vector<std::vector<double> > &_weights, 
            std::vector<int> &_initialstate,
            int _tauref, int _tausyn,
            TActivation _neuron_activation_type,
            TInteraction _neuron_interaction_type);
    ~Network() {};
    
    std::vector<bool> states;

    // std::vector<bool> get_state();
    void get_state();
    void get_internalstate();
    void update_state(double T);
    bool _check_consistency();
};



#endif // NETWORK_H

