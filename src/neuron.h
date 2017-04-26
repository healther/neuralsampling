#ifndef NEURON_H
#define NEURON_H

#include <random>
#include "fixed_queue.h"

extern std::mt19937_64 mt_random;
extern std::uniform_real_distribution<double> random_double;

enum TActivation { Log, Erf, Step };
enum TInteraction { Rect, Exp, Tail, Cuto };


class Neuron
{
private:
    const TActivation activation_type;
    const TInteraction interaction_type;

protected:
    const long long int tauref;
    const long long int tausyn;
    const long long int delay;
    long long int nspikes;
    long long int state;
    FixedQueue interactions;

public:
    Neuron(const long long int _tauref, const long long int _tausyn,
        const long long int _delay, const long long int _state,
        const TActivation _activation_type, const TInteraction _interaction_type);
    ~Neuron() {};

    void update_state(const double pot);
    void update_interaction();

    bool spike(const double pot);
    bool has_spiked();

    long long int get_internalstate();
    long long int get_state();
    long long int get_nspikes();

    double get_interaction();
    double activation(const double pot);
};



#endif // NEURON_H
