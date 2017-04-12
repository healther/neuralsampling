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
    const int tauref;
    const int tausyn;
    const int delay;
    int nspikes;
    int state;
    FixedQueue interactions;

public:
    Neuron(const int _tauref, const int _tausyn, const int _delay, const int _state,
        const TActivation _activation_type, const TInteraction _interaction_type);
    ~Neuron() {};

    void update_state(const double pot);
    void update_interaction();

    bool spike(const double pot);
    bool has_spiked();

    int get_internalstate();
    int get_state();
    int get_nspikes();

    double get_interaction();
    double activation(const double pot);
};



#endif // NEURON_H
