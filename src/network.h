#ifndef NETWORK_H
#define NETWORK_H

#include <ostream>
#include <vector>
#include <random>
#include <algorithm>

extern std::mt19937_64 mt_random;

#include "type.h"
#include "neuron.h"
#include "config.h"

class Network
{
private:
    const TOutputScheme output_scheme;
    const TUpdateScheme update_scheme;
    const TActivation neuron_activation_type;
    const TInteraction neuron_interaction_type;

    std::vector<float> biases;
    std::vector<std::vector<float> > weights;
    std::vector<std::vector<int64_t> > connected_neuron_ids;
    std::vector<Neuron> neurons;
    int64_t tauref;
    int64_t tausyn;
    int64_t delay;
    bool outputEnv;
    bool boptimized;

    void generate_connected_neuron_ids();
    std::vector<int64_t> get_update_inds();
    float get_potential_for_neuronid(int64_t id);

public:
    Network(std::vector<float> &_biases,
            std::vector<std::vector<float> > &_weights,
            std::vector<int64_t> &_initialstate,
            Config config);
    ~Network() {};

    std::vector<int64_t> states;

    // std::vector<bool> get_state();
    void produce_header(std::ostream& stream);
    void produce_output(std::ostream& stream, float T, float Iext);
    void produce_summary(std::ostream& stream);
    void get_state();
    void get_internalstate();
    void update_state(float T);
    void update_state(float T, float Iext);
    bool _check_consistency();
};



#endif // NETWORK_H

