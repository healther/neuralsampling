#include <iostream>

#include "main.h"
#include "configOutput.h"


ConfigOutput::ConfigOutput(int64_t nneurons) {
    // generate ConfigOutput with sensible defaults
    outputScheme = MeanActivityOutput;
    outputEnv = true;
    outputIndexes = {};
    for (auto i = 0; i < nneurons; ++i)
    {
        outputIndexes.push_back(i);
    }
    outputTimes.push_back(1L<<63);
}


void ConfigOutput::updateConfig(YAML::Node configOutputNode) {
    if (configOutputNode["outputScheme"]) {
        std::string output_scheme =
                configOutputNode["outputScheme"].as<std::string>();
        if (output_scheme=="MeanActivity") {
            outputScheme = MeanActivityOutput;
        } else if (output_scheme=="MeanActivityEnergy") {
            outputScheme = MeanActivityEnergyOutput;
        } else if (output_scheme=="BinaryState") {
            outputScheme = BinaryStateOutput;
        } else if (output_scheme=="InternalStateOutput") {
            outputScheme = InternalStateOutput;
        } else if (output_scheme=="Spikes") {
            outputScheme = SpikesOutput;
        } else if (output_scheme=="SummarySpikes") {
            outputScheme = SummarySpikes;
        } else if (output_scheme=="SummaryStates") {
            outputScheme = SummaryStates;
        } else {
            std::cout << "Use network_output_scheme [MeanActivity, MeanActivityEnergy, BinaryState, InternalStateOutput, Spikes, SummarySpikes, SummaryStates]" << std::endl;
            throw;
        }
    }
    if (configOutputNode["outputIndexes"] && (configOutputNode["outputIndexes"].size() > 0)) {
        outputIndexes.clear();
        for (auto it = configOutputNode["outputIndexes"].begin(); it != configOutputNode["outputIndexes"].end(); ++it)
        {
            outputIndexes.push_back(it->as<int64_t>());
        }
    }
    if (configOutputNode["outputTimes"] && (configOutputNode["outputTimes"].as<int64_t>() > 0)) {
        outputTimes.clear();
        for (auto it = configOutputNode["outputTimes"].begin(); it != configOutputNode["outputTimes"].end(); ++it)
        {
            outputTimes.push_back(it->as<int64_t>());
        }
    }
    if (configOutputNode["outputEnv"]) {
        outputEnv = configOutputNode["outputEnv"].as<bool>();
    }
}
