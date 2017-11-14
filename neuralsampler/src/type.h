#ifndef TYPE_H
#define TYPE_H
enum ChangeType
{
    Const,
    Linear
};

enum TActivation { Log, Erf, Step };
enum TInteraction { Rect, Exp, Tail, Cuto };
enum TUpdateScheme { InOrder, BatchRandom, Random };
enum TOutputScheme { BinaryStateOutput, SpikesOutput, SummarySpikes,
                     MeanActivityOutput, MeanActivityEnergyOutput,
                    };


#endif // TYPE_H
