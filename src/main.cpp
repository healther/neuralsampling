#include <stdio.h>
#include <iostream>
#include <fstream>
#include <vector>

#include "main.h"

#include "myrandom.h"
#include "neuron.h"
#include "network.h"
#include "temperature.h"


int main(int argc, char const *argv[])
{
    // report inputfilename and load the yaml content
    if (argc != 2) {
        std::cout << "Provide the configuration you wish to run." << std::endl;
        return 1;
    }
    std::cout << argv[1] << std::endl;
    YAML::Node baseNode = YAML::LoadFile(argv[1]);
    YAML::Node configNode = baseNode["Config"];
    YAML::Node biasNode = baseNode["bias"];
    if (!biasNode) {
        YAML::Node biasFileNode = baseNode["biasFile"];
        biasNode = YAML::LoadFile(biasFileNode.as<std::string>());
    }
    YAML::Node weightNode = baseNode["weight"];
    if (!weightNode) {
        YAML::Node weightFileNode = baseNode["weightFile"];
        weightNode = YAML::LoadFile(weightFileNode.as<std::string>());
    }
    YAML::Node initialStateNode = baseNode["initialstate"];
    if (!initialStateNode) {
        YAML::Node initialStateFileNode = baseNode["initialstateFile"];
        initialStateNode = YAML::LoadFile(initialStateFileNode.as<std::string>());
    }
    YAML::Node temperatureNode = baseNode["temperature"];
    YAML::Node currentNode = baseNode["externalCurrent"];

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
    // read sparse representation of weight matrix in
    std::vector<std::vector<double>> weights(bias.size());
    for(unsigned int i = 0; i < bias.size(); ++i) {
        std::vector<double> weight_line(bias.size());
        for(unsigned int j = 0; j < bias.size(); ++j) {weight_line[j] = 0.;}
        weights[i] = weight_line;
    }
    // translate in dense matrix
    int i, j;
    double w;
    for(YAML::const_iterator it=weightNode.begin(); it!=weightNode.end(); it++) {
        i = (*it)[0].as<int>();
        j = (*it)[1].as<int>();
        w = (*it)[2].as<double>();
        weights[i][j] = w;
    }

    std::vector<int> initialstate;
    for(YAML::const_iterator it=initialStateNode.begin(); it!=initialStateNode.end(); it++) {
        initialstate.push_back(it->as<int>());
    }

    // get general config
    long long int random_seed = configNode["randomSeed"].as<long long int>();
    long long int random_skip = configNode["randomSkip"].as<long long int>();
    unsigned long long int nupdates = configNode["nupdates"].as<long long int>();
    int tauref = configNode["tauref"].as<int>();
    int tausyn = configNode["tausyn"].as<int>();
    int delay = configNode["delay"].as<int>();
    std::string neuron_type = configNode["neuronType"].as<std::string>();
    std::string synapse_type = configNode["synapseType"].as<std::string>();
    std::string network_update_scheme = configNode["networkUpdateScheme"].as<std::string>();
    std::string output_scheme = configNode["outputScheme"].as<std::string>();
    bool output_env = configNode["outputEnv"].as<bool>(false);

    // get temperature
    std::string temperature_type = temperatureNode["type"].as<std::string>();
    ChangeType ttype;
    if (temperature_type=="Linear") {
        ttype = Linear;
    } else if (temperature_type=="Const") {
        ttype = Const;
    } else {
        std::cout << "Invalid temperature type. Aborting" << std::endl;
        exit(1);
    }
    Temperature temperature = Temperature(ttype, temperatureNode);

    // get external current
    std::string current_type = currentNode["type"].as<std::string>();
    if (current_type=="Linear") {
        ttype = Linear;
    } else if (current_type=="Const") {
        ttype = Const;
    } else {
        std::cout << "Invalid current type. Aborting" << std::endl;
    }
    Temperature current = Temperature(ttype, currentNode);

    // create corresponding network
    TInteraction neuron_interaction_type;
    TActivation neuron_activation_type;
    /// TODO: include stepfunction
    if (neuron_type=="log") {
        neuron_activation_type = Log;
    } else if (neuron_type=="erf") {
        neuron_activation_type = Erf;
    } else {
        std::cout << "Invalid neuron type. Aborting." << std::endl;
        return -1;
    }
    if (synapse_type=="rect") {
        neuron_interaction_type = Rect;
    } else if (synapse_type=="exp") {
        neuron_interaction_type = Exp;
    } else if (synapse_type=="cuto") {
        neuron_interaction_type = Cuto;
    } else if (synapse_type=="tail") {
        neuron_interaction_type = Tail;
    } else  {
        std::cout << "Invalid synapse type. Aborting." << std::endl;
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
    } else if (output_scheme=="SummarySpikes") {
        network_output_scheme_type = SummarySpikes;
    } else {
        std::cout << "Use network_output_scheme [MeanActivity, BinaryState, Spikes, SummarySpikes]" << std::endl;
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
    // output << "Remove config file at the end: " << b_remove_config_file << std::endl;
    output << "Outputformat OutputEnv Updatescheme Activationtype Interactiontype: "
        << network_output_scheme_type
        << output_env
        << network_update_scheme_type
        << neuron_activation_type
        << neuron_interaction_type
        << std::endl;

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
    double T, Iext;
    for (unsigned int i = 0; i < nupdates; ++i)
    {
        T = temperature.get_temperature(i);
        Iext = current.get_temperature(i);
        if (output_env) {
            output << T << " " << Iext << " ";
        }
        net.update_state(T, Iext);
        net.get_state();
        net.produce_output(output);
        if (i % 100000 == 0)
        {
            net.produce_summary(output);
        }
    }
    net.produce_summary(output);
    of.close();

    return 0;
}






