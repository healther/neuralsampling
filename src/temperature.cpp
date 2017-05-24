#include <iostream>
#include <vector>
#include <cmath>

#include <random>
#include <algorithm>

#include "temperature.h"


Temperature::Temperature():
    change_type(Const)
{
    times.push_back(0);
    times.push_back(1);
    values.push_back(1.);
    values.push_back(1.);

    currentposition = 0;
    currenttemperature = 1.;
}


Temperature::Temperature(double T, int nupdates):
    change_type(Const)
{
    times.push_back(0);
    times.push_back(nupdates+1);
    values.push_back(T);
    values.push_back(T);

    currentposition = -1;
    currenttemperature = T;
}


Temperature::Temperature(ChangeType type, YAML::Node temperatureParameters):
    change_type(type)
{
    YAML::Node temperatureTimeNode = temperatureParameters["times"];
    for(YAML::const_iterator it=temperatureTimeNode.begin(); it!=temperatureTimeNode.end(); it++) {
        times.push_back(it->as<int>());
    }
    YAML::Node temperatureValueNode = temperatureParameters["values"];
    for(YAML::const_iterator it=temperatureValueNode.begin(); it!=temperatureValueNode.end(); it++) {
        values.push_back(it->as<double>());
    }

    if ( (times[0] <= 0) && (times[1] > 0))
    {
        currentposition = 0;
        currenttemperature = values[0];
    } else {
        throw;
    }
}


double Temperature::get_temperature(int nupdate) {
    if (change_type == Const) {
        if (nupdate >= times[currentposition+1]) {
            currentposition++;
            currenttemperature = values[currentposition];
        }
    } else if (change_type == Linear) {
        if (nupdate >= times[currentposition+1]) {
            currentposition++;
        }
        currenttemperature =
            (values[currentposition+1] - values[currentposition]) *
            (nupdate-times[currentposition]) /
            (double) (times[currentposition+1] - times[currentposition]) +
            values[currentposition];
    } else {
        throw;
    }
    return currenttemperature;
}


bool Temperature::check_nupdatemax(int nupdatemax) {
    return times.back() > nupdatemax;
}
