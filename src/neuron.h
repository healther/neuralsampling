#ifndef NEURON_H
#define NEURON_H

#include <random>

extern std::mt19937_64 mt_random;
extern std::uniform_real_distribution<double> random_double;

enum TActivation { Log, Erf };
enum TInteraction { Rect, Exp, Tail, Cuto };


class Neuron
{
private:
    const TActivation activation_type;
    const TInteraction interaction_type;

protected:
    const int tauref;
    const int tausyn;
    int state;
    double interaction;

public:
    Neuron(const int _tauref, const int _tausyn, const int _state, 
        const TActivation _activation_type, const TInteraction _interaction_type);
    ~Neuron() {};

    void update_state(const double pot);
    void update_interaction();

    bool spike(const double pot);
    bool has_spiked();

    int get_internalstate();
    int get_state();

    double get_interaction();
    double activation(const double pot);
};



#endif // NEURON_H
