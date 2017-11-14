#ifndef TEMPERATURE_H
#define TEMPERATURE_H

#include <ostream>
#include <vector>
#include <random>
#include <algorithm>

#include "main.h"
#include "type.h"

class Temperature
{
private:
    const ChangeType change_type;

    int64_t currentposition;
    double currenttemperature;

    std::vector<double> values;
    std::vector<int64_t> times;

    void update_temperature(int64_t nupdate);


public:
    Temperature(ChangeType type, YAML::Node temperatureNode);
    Temperature(double T, int64_t nupdates);
    Temperature();
    ~Temperature() {};

    double get_temperature(int64_t nupdate);
    bool check_nupdatemax(int64_t nupdatemax);
};



#endif // TEMPERATURE_H


