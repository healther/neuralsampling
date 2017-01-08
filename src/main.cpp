#include <stdio.h>
#include <iostream>
#include <fstream>
#include <vector>

#include "main.h"

#include "myrandom.h"
#include "neuron.h"
#include "network.h"


int main(int argc, char const *argv[])
{
    std::cout << argv[1] << std::endl;
    YAML::Node baseNode = YAML::LoadFile(argv[1]);
    YAML::Node configNode = baseNode["Config"];
    YAML::Node biasNode = baseNode["bias"];
    if (!biasNode) {
        YAML::Node biasFileNode = baseNode["bias_file"];
        biasNode = YAML::LoadFile(biasFileNode.as<std::string>());
    }
    YAML::Node weightNode = baseNode["weight"];
    if (!weightNode) {
        YAML::Node weightFileNode = baseNode["weight_file"];
        weightNode = YAML::LoadFile(weightFileNode.as<std::string>());
    }
    YAML::Node initialStateNode = baseNode["initialstate"];
    if (!initialStateNode) {
        YAML::Node initialStateFileNode = baseNode["initialstate_file"];
        initialStateNode = YAML::LoadFile(initialStateFileNode.as<std::string>());
    }

    if (!biasNode || !weightNode || !initialStateNode) {
        std::cout << "Corrupted configuration file" << std::endl;
        return -1;
    }

    YAML::Node simulationFolderNode = baseNode["outfile"];
    bool b_output_file = baseNode["outfile"];

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
    int delay = configNode["delay"].as<int>();
    double Tmin = configNode["Tmin"].as<double>();
    double Tmax = configNode["Tmax"].as<double>();
    double T = (Tmax-Tmin)/nupdates + Tmin;
    std::string neuron_type = configNode["neuron_type"].as<std::string>();
    std::string network_update_scheme = configNode["network_update_scheme"].as<std::string>();
    std::string output_scheme = configNode["output_scheme"].as<std::string>();
    bool b_remove_config_file = configNode["remove_config_file"].as<bool>();

    // create corresponding network
    TInteraction neuron_interaction_type;
    TActivation neuron_activation_type;
    /// TODO: Replace neuron_type with interaction_type and
    ///         activation_type and include stepfunction
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
        std::cout << "Use network_update_scheme [InOrder, BatchRandom, Random]" << std::endl;
        return -1;
    }

    TOutputScheme network_output_scheme_type;
    if (output_scheme=="MeanActivity") {
        network_output_scheme_type = MeanActivityOutput;
    } else if (output_scheme=="BinaryState") {
        network_output_scheme_type = BinaryStateOutput;
    } else if (output_scheme=="Spikes") {
        network_output_scheme_type = SpikesOutput;
    } else {
        std::cout << "Use network_output_scheme [MeanActivity, BinaryState, Spikes]" << std::endl;
        return -1;
    }

    std::streambuf *buf;
    std::ofstream of;
    if (b_output_file) {
        of.open(simulationFolderNode.as<std::string>() ) ;
        buf = of.rdbuf();;
    } else {
        buf = std::cout.rdbuf();
    }
    std::ostream output(buf);
    output << "Remove config file at the end: " << b_remove_config_file << std::endl;
    output << "Outputformat Updatescheme Activationtype Interactiontype: "
        << network_output_scheme_type << network_update_scheme_type
        << neuron_interaction_type << neuron_activation_type << std::endl;

    Network net(bias, weights, initialstate, tauref, tausyn, delay,
        network_output_scheme_type,
        network_update_scheme_type,
        neuron_activation_type,
        neuron_interaction_type);

    // and output initial configuration
    net.get_state();
    net.produce_output(output);

    // seed random number generator and discard for higher entropy
    mt_random.seed(random_seed);
    mt_random.discard(random_skip);

    // actual simulation
    for (int i = 0; i < nupdates; ++i)
    {
        T = (Tmax-Tmin)*(i+1)/nupdates + Tmin;
        net.update_state(T);
        net.get_state();
        net.produce_output(output);
    }
    of.close();

    if (b_remove_config_file){
        std::remove(argv[1]);
    }

    return 0;
}






