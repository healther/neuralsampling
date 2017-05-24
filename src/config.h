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
    int randomSeed;
    int randomSkip;
    unsigned int nupdates;
    int tauref;
    int tausyn;
    int delay;
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

