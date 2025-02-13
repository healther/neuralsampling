#ifndef TYPE_H
#define TYPE_H
enum ChangeType
{
    Const,
    Linear
};

enum TActivation { Log, Erf, Step };
enum TInteraction { Rect, Exp, Tail, Cuto };
enum TIntegration { MemoryLess, OU };
enum TUpdateScheme { InOrder, BatchRandom, Random };
enum TOutputScheme { InternalStateOutput, BinaryStateOutput,
                     SpikesOutput, SummarySpikes, SummaryStates,
                     MeanActivityOutput, MeanActivityEnergyOutput,
                    };


#endif // TYPE_H
