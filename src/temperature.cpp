#include <iostream>
#include <vector>
#include <cmath>
#include <cassert>

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


Temperature::Temperature(double T, long long int nupdates):
    change_type(Const)
{
    times.push_back(0);
    times.push_back(nupdates+1);
    values.push_back(T);
    values.push_back(T);

    currentposition = 0;
    currenttemperature = T;
}


Temperature::Temperature(ChangeType type, YAML::Node temperatureParameters):
    change_type(type)
{
    YAML::Node temperatureTimeNode = temperatureParameters["times"];
    for(YAML::const_iterator it=temperatureTimeNode.begin(); it!=temperatureTimeNode.end(); it++) {
        times.push_back(it->as<long long int>());
    }
    YAML::Node temperatureValueNode = temperatureParameters["values"];
    for(YAML::const_iterator it=temperatureValueNode.begin(); it!=temperatureValueNode.end(); it++) {
        values.push_back(it->as<double>());
    }

    // ensure that valid data was loaded
    selfcheck();
    // initialize values
    currentposition = 0;
    currenttemperature = values[0];
}


void Temperature::selfcheck() {
    // initial temperature must be set
    assert( times.front() == 0);
    // final time must be larger than 0
    assert( times.back() > 0);
    // times need to be sorted
    for (unsigned int i = 0; i < times.size()-1; ++i)
    {
        assert(times[i+1] - times[i] > 0);
    }
    // there must be as many times as values
    assert(times.size() == values.size());
}


double Temperature::get_temperature(long long int nupdate) {
    if (change_type == Const) {
        if (nupdate >= times.at( currentposition + 1 )) {
            currentposition++;
            currenttemperature = values[currentposition];
        }
    } else if (change_type == Linear) {
        if (nupdate >= times.at( currentposition + 1 )) {
            currentposition++;
        }
        double dV = values.at(currentposition+1) - values.at(currentposition);
        double currentt = nupdate - times.at(currentposition);
        double dt = times.at(currentposition+1) - times.at(currentposition);
        currenttemperature = dV * currentt / dt  + values.at(currentposition);
    } else {
        std::cout << "Unknown interpolation type" << std::endl;
        throw;
    }
    return currenttemperature;
}
