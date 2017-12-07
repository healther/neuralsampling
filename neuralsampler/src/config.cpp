#include <iostream>

#include "main.h"
#include "config.h"


Config::Config() {
    // generate Config with sensible defaults
    randomSeed = 42424242;
    randomSkip = 1000000;
    nupdates = 100000;
    tauref = 1;
    tausyn = 1;
    delay = 1;
    neuronActivationType = Log;
    neuronInteractionType = Rect;
    updateScheme = InOrder;
    outputScheme = MeanActivityOutput;
    outputEnv = true;
}


void Config::updateConfig(YAML::Node configNode) {
    if (configNode["randomSeed"])
    {
        randomSeed = configNode["randomSeed"].as<int64_t>();
    }
    if (configNode["randomSkip"]) {
        randomSkip = configNode["randomSkip"].as<int64_t>();
    }
    if (configNode["nupdates"]) {
        nupdates = configNode["nupdates"].as<int64_t>();
    }
    if (configNode["tauref"]) {
        tauref = configNode["tauref"].as<int64_t>();
    }
    if (configNode["tausyn"]) {
        tausyn = configNode["tausyn"].as<int64_t>();
    }
    if (configNode["delay"]) {
        delay = configNode["delay"].as<int64_t>();
    }
    if (configNode["neuronType"]) {
        std::string neuron_type =
                configNode["neuronType"].as<std::string>();
        if (neuron_type=="log") {
            neuronActivationType = Log;
        } else if (neuron_type=="erf") {
            neuronActivationType = Erf;
        } else {
            std::cout << "Invalid neuron type. Aborting." << std::endl;
            throw;
        }
    }
    if (configNode["synapseType"]) {
        std::string synapse_type =
                configNode["synapseType"].as<std::string>();
        if (synapse_type=="rect") {
            neuronInteractionType = Rect;
        } else if (synapse_type=="exp") {
            neuronInteractionType = Exp;
        } else if (synapse_type=="cuto") {
            neuronInteractionType = Cuto;
        } else if (synapse_type=="tail") {
            neuronInteractionType = Tail;
        } else  {
            std::cout << "Invalid synapse type. Aborting." << std::endl;
            throw;
        }
    }
    if (configNode["networkUpdateScheme"])
    {
        std::string network_update_scheme =
                configNode["networkUpdateScheme"].as<std::string>();
        if (network_update_scheme=="InOrder"){
            updateScheme = InOrder;
        } else if (network_update_scheme=="BatchRandom") {
            updateScheme = BatchRandom;
        } else if (network_update_scheme=="Random") {
            updateScheme = Random;
        } else {
            std::cout << "Use network_update_scheme [InOrder, BatchRandom, Random]" << std::endl;
            throw;
        }
    }
    if (configNode["outputScheme"]) {
        std::string output_scheme =
                configNode["outputScheme"].as<std::string>();
        if (output_scheme=="MeanActivity") {
            outputScheme = MeanActivityOutput;
        } else if (output_scheme=="MeanActivityEnergy") {
            outputScheme = MeanActivityEnergyOutput;
        } else if (output_scheme=="BinaryState") {
            outputScheme = BinaryStateOutput;
        } else if (output_scheme=="Spikes") {
            outputScheme = SpikesOutput;
        } else if (output_scheme=="SummarySpikes") {
            outputScheme = SummarySpikes;
        } else {
            std::cout << "Use network_output_scheme [MeanActivity, MeanActivityEnergy, BinaryState, Spikes, SummarySpikes]" << std::endl;
            throw;
        }
    }
    if (configNode["outputEnv"]) {
        outputEnv = configNode["outputEnv"].as<bool>();
    }
}


bool Config::checkTemperature(Temperature temperature) {
    return temperature.check_nupdatemax(nupdates);
}
