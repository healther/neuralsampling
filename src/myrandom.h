#ifndef MYRANDOM_H
#define MYRANDOM_H

#include <random>

std::mt19937_64 mt_random;
std::uniform_real_distribution<float> random_float(0.0,1.0);

#endif // MYRANDOM_H
