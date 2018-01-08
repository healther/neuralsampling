#ifndef CONFIG_H
#define CONFIG_H

#include <ostream>
#include <vector>
#include <random>
#include <algorithm>

#include "type.h"
#include "temperature.h"

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
    TActivation neuronActivationType;
    TInteraction neuronInteractionType;
    TUpdateScheme updateScheme;
    TOutputScheme outputScheme;
    bool outputEnv;

    Config();
    ~Config() {};

    void updateConfig(YAML::Node ConfigNode);
    bool checkTemperature(Temperature temperature);


};


#endif // CONFIG_H

