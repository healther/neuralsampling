#ifndef FIXED_QUEUE_H
#define FIXED_QUEUE_H

#include <vector>

class FixedQueue
{
private:



protected:
    const int size;


public:
    int position;
    std::vector<float> content;

    FixedQueue(const int _size, float initial_value);
    ~FixedQueue() {};

    void add_entry(float value);

    float return_entry();
};



#endif // FIXED_QUEUE_H
