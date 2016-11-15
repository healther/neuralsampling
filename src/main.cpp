#include <stdio.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <boost/lexical_cast.hpp>
#include "yaml-cpp/yaml.h"


#include "myrandom.h"
#include "neuron.h"
#include "network.h"


int main(int argc, char const *argv[])
{
    YAML::Node baseNode = YAML::LoadFile(argv[1]);
    YAML::Node configNode = baseNode["Config"];
    YAML::Node biasNode = baseNode["bias"];
    YAML::Node weightNode = baseNode["weight"];
    YAML::Node initialStateNode = baseNode["initialstate"];

    std::vector<double> bias;
    for(YAML::const_iterator it=biasNode.begin(); it!=biasNode.end(); it++) {
        bias.push_back(it->as<double>());
    }
    std::vector<std::vector<double>> weights;
    for(YAML::const_iterator it=weightNode.begin(); it!=weightNode.end(); it++) {
        std::vector<double> weight_line;
        for(YAML::const_iterator jt=it->begin(); jt!=it->end(); jt++) {
            weight_line.push_back(jt->as<double>());
        }
        weights.push_back(weight_line);
    }
    std::vector<int> initialstate;
    for(YAML::const_iterator it=initialStateNode.begin(); it!=initialStateNode.end(); it++) {
        initialstate.push_back(it->as<int>());
    }

    int random_seed = configNode["random_seed"].as<int>();
    int random_skip = configNode["random_skip"].as<int>();
    unsigned int nupdates = configNode["nupdates"].as<int>();
    int tauref = configNode["tauref"].as<int>();
    int tausyn = configNode["tausyn"].as<int>();
    double Tmin = configNode["Tmin"].as<double>();
    double Tmax = configNode["Tmax"].as<double>();
    double T = (Tmax-Tmin)/nupdates + Tmin;
    std::string neuron_type = configNode["neuron_type"].as<std::string>();
    std::string network_update_scheme = configNode["network_update_scheme"].as<std::string>();

    int meanactoutput = configNode["meanactoutput"].as<int>();

    // create corresponding network
    TInteraction neuron_interaction_type;
    TActivation neuron_activation_type;
    if (neuron_type=="log_rect") {
        neuron_interaction_type = Rect;
        neuron_activation_type = Log;
    } else if (neuron_type=="log_exp") {
        neuron_interaction_type = Exp;
        neuron_activation_type = Log;
    } else if (neuron_type=="log_cuto") {
        neuron_interaction_type = Cuto;
        neuron_activation_type = Log;
    } else if (neuron_type=="log_tail") {
        neuron_interaction_type = Tail;
        neuron_activation_type = Log;
    } else if (neuron_type=="erf_rect") {
        neuron_interaction_type = Rect;
        neuron_activation_type = Erf;
    } else if (neuron_type=="erf_exp") {
        neuron_interaction_type = Exp;
        neuron_activation_type = Erf;
    } else if (neuron_type=="erf_cuto") {
        neuron_interaction_type = Cuto;
        neuron_activation_type = Erf;
    } else if (neuron_type=="erf_tail") {
        neuron_interaction_type = Tail;
        neuron_activation_type = Erf;
    } else {
        return -1;
    }

    TUpdateScheme network_update_scheme_type;
    if (network_update_scheme=="InOrder"){
        network_update_scheme_type = InOrder;
    } else if (network_update_scheme=="BatchRandom") {
        network_update_scheme_type = BatchRandom;
    } else if (network_update_scheme=="Random") {
        network_update_scheme_type = Random;
    } else {
        return -1;
    }

    std::cout << neuron_interaction_type << neuron_activation_type << network_update_scheme_type << std::endl;

    Network net(bias, weights, initialstate, tauref, tausyn,
        network_update_scheme_type, neuron_activation_type, neuron_interaction_type);

    // and output initial configuration
    net.get_state();
    int sumact = 0;
    for (unsigned int i = 0; i < bias.size(); ++i)
    {
        if (meanactoutput==0) {
            std::cout << net.states[i];
        }
        else {
            sumact += net.states[i];
        }
    }
    if (meanactoutput==0) {
        std::cout << std::endl;
    } else {
        std::cout << sumact << std::endl;
    }

    // seed random number generator and discard for higher entropy
    mt_random.seed(random_seed);
    mt_random.discard(random_skip);

    // actual simulation
    for (int i = 0; i < nupdates; ++i)
    {
        T = (Tmax-Tmin)*(i+1)/nupdates + Tmin;
        net.update_state(T);
        net.get_state();
        sumact = 0;
        for (unsigned int j = 0; j < bias.size(); ++j)
        {
            if (meanactoutput==0) {
                std::cout << net.states[j];
            }
            else {
                sumact += net.states[j];
            }
        }
        if (meanactoutput==0) {
            std::cout << std::endl;
        } else {
            std::cout << sumact << std::endl;
        }
    }

    return 0;
}






