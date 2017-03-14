#include <iostream>
#include <vector>
#include <cmath>

#include <random>
#include <algorithm>

#include "temperature.h"


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

    currentposition = 0;
    currenttemperature = 1.;
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
