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
    const std::vector<int64_t> outputIndexes;

    const std::vector<double> biases;
    const std::vector<std::vector<double> > weights;
    std::vector<std::vector<int64_t> > connected_neuron_ids;
    std::vector<Neuron> neurons;
    bool outputEnv;
    bool boptimized;

    bool generate_connected_neuron_ids();
    std::vector<int64_t> get_update_inds();
    double get_potential_for_neuronid(int64_t id);

public:
    Network(const std::vector<double> &_biases,
            const std::vector<std::vector<double> > &_weights,
            const std::vector<int64_t> &_initialstate,
            const Config& config);
    ~Network() {};

    std::vector<int64_t> states;
    std::map<std::vector<int64_t>, int64_t> summary_states;

    // std::vector<bool> get_state();
    void produce_header(std::ostream& stream);
    void produce_output(std::ostream& stream, double T, double Iext);
    void produce_summary(std::ostream& stream);
    void get_state();
    void get_binary_state();
    void get_internalstate();
    void update_state(double T);
    void update_state(double T, double Iext);
    bool _check_consistency();
};



#endif // NETWORK_H

