#ifndef TEMPERATURE_H
#define TEMPERATURE_H

#include "yaml-cpp/yaml.h"
#include <ostream>
#include <vector>
#include <random>
#include <algorithm>

enum ChangeType
{
    Const,
    Linear
};

class Temperature
{
private:
    const ChangeType change_type;

    int currentposition;
    double currenttemperature;

    std::vector<double> values;
    std::vector<int> times;

    void update_temperature(int nupdate);


public:
    Temperature(ChangeType type, YAML::Node temperatureNode);
    ~Temperature() {};

    double get_temperature(int nupdate);
};



#endif // TEMPERATURE_H


