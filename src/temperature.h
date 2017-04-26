#ifndef TEMPERATURE_H
#define TEMPERATURE_H

#include <ostream>
#include <vector>
#include <random>
#include <algorithm>

#include "main.h"

    enum ChangeType
{
    Const,
    Linear
};

class Temperature
{
private:
    const ChangeType change_type;

    long long int currentposition;
    double currenttemperature;

    std::vector<double> values;
    std::vector<long long int> times;

    void update_temperature(long long int nupdate);
    void selfcheck();


public:
    Temperature(ChangeType type, YAML::Node temperatureNode);
    Temperature(double T, long long int nupdates);
    Temperature();
    ~Temperature() {};

    double get_temperature(long long int nupdate);
};



#endif // TEMPERATURE_H


