#ifndef FIXED_QUEUE_H
#define FIXED_QUEUE_H

#include <vector>

class FixedQueue
{
private:
    int position;
    std::vector<double> content;

protected:
    const int size;


public:
    FixedQueue(const int _size, double initial_value);
    ~FixedQueue() {};

    void add_entry(double value);

    double return_entry();
};



#endif // FIXED_QUEUE_H