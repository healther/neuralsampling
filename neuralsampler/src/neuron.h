#ifndef NEURON_H
#define NEURON_H

#include <random>

#include "type.h"
#include "fixed_queue.h"
#include "configNeuronUpdate.h"

extern std::mt19937_64 mt_random;
extern std::uniform_real_distribution<double> random_double;
extern std::normal_distribution<double> random_normal;

class Neuron
{
private:
    const TActivation activation_type;
    const TInteraction interaction_type;
    const TIntegration integration_type;
    const ConfigNeuronUpdate neuronUpdate;

protected:
    const int64_t tauref;
    const int64_t tausyn;
    const int64_t delay;
    const int64_t num_interactions;
    const double taurefsyn;
    const double taurefsynexp;
    double membrane_potential;
    int64_t nspikes;
    std::vector<int64_t> state;
    FixedQueue interactions;

public:
    Neuron(const int64_t _tauref, const int64_t _tausyn, const int64_t _delay,
        const int64_t _num_interactions,
        const int64_t _state, const ConfigNeuronUpdate _neuronUpdate,
        const TActivation _activation_type,
        const TInteraction _interaction_type,
        const TIntegration _integration_type);
    Neuron(const int64_t _tauref, const int64_t _tausyn, const int64_t _delay,
        const int64_t _state, const ConfigNeuronUpdate _neuronUpdate,
        const TActivation _activation_type,
        const TInteraction _interaction_type,
        const TIntegration _integration_type);
    Neuron(const int64_t _tauref, const int64_t _tausyn, const int64_t _delay,
        const int64_t _state,
        const TActivation _activation_type,
        const TInteraction _interaction_type);
    ~Neuron() {};

    void update_state(const double pot);
    void update_interaction();

    int spike(const double pot);
    bool has_spiked();

    int64_t get_internalstate();
    int64_t get_state();
    int64_t get_nspikes();

    double get_interaction();
    double activation(const double pot);
};



#endif // NEURON_H
