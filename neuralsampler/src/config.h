#ifndef CONFIG_H
#define CONFIG_H

#include <ostream>
#include <vector>
#include <random>
#include <algorithm>

#include "type.h"
#include "temperature.h"
#include "configOutput.h"

class Config
{
public:
    int64_t randomSeed;
    int64_t randomSkip;
    int64_t nupdates;
    int64_t tauref;
    int64_t tausyn;
    int64_t delay;
    int64_t subsampling;
    int64_t nneurons;
    TActivation neuronActivationType;
    TInteraction neuronInteractionType;
    TUpdateScheme updateScheme;
    ConfigOutput output;

    Config(int64_t nneurons);
    ~Config() {};

    void updateConfig(YAML::Node ConfigNode);
    bool checkTemperature(Temperature temperature);
};


#endif // CONFIG_H

