#include <iostream>

#include "fixed_queue.h"


FixedQueue::FixedQueue(const int _size, double initial_value) :
    size(_size)
{
    position = 0;
    content.resize(size, initial_value);
}

void FixedQueue::add_entry(double value)
{
    position = (position+1) % size;
    content[position] = value;
}

double FixedQueue::return_entry()
{
    return content[(position+1)%size];
}