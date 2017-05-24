#ifndef NEURON_H
#define NEURON_H

#include <random>

#include "fixed_queue.h"
#include "type.h"

extern std::mt19937_64 mt_random;
extern std::uniform_real_distribution<double> random_double;

class Neuron
{
private:
    const TActivation activation_type;
    const TInteraction interaction_type;

protected:
    const int64_t tauref;
    const int64_t tausyn;
    const int64_t delay;
    int64_t nspikes;
    int64_t state;
    FixedQueue interactions;

public:
    Neuron(const int64_t _tauref, const int64_t _tausyn, const int64_t _delay,
        const int64_t _state, const TActivation _activation_type,
        const TInteraction _interaction_type);
    ~Neuron() {};

    void update_state(const double pot);
    void update_interaction();

    bool spike(const double pot);
    bool has_spiked();

    int64_t get_internalstate();
    int64_t get_state();
    int64_t get_nspikes();

    double get_interaction();
    double activation(const double pot);
};



#endif // NEURON_H
