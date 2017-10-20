#include <iostream>

#include "fixed_queue.h"


FixedQueue::FixedQueue(const int _size, float initial_value) :
    size(_size)
{
    position = 0;
    content.resize(size, initial_value);
}

void FixedQueue::add_entry(float value)
{
    position = (position+1) % size;
    content[(position+1) % size] = value;
}

float FixedQueue::return_entry()
{
    return content[position];
}
