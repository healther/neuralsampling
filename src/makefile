CPPFLAGS=-O0
LDFLAGS=
LDLIBS=-lm -lyaml-cpp
INCLUDEPATH=-I/usr/local/include
LIBPATH=-L/usr/local/lib

OBJS=neuralsampler network.o neuron.o

network.o: network.cpp neuron.h network.h
	g++ $(CPPFLAGS) -c network.cpp

test_network: network_test.cpp neuron.h neuron.o network.o network.h
	g++ $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) network_test.cpp neuron.o network.o $(LDLIBS) -o test_network

neuron.o: neuron.cpp neuron.h
	g++ $(CPPFLAGS) -c neuron.cpp

test_neuron: neuron_test.cpp neuron.cpp neuron.h
	g++ $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) neuron_test.cpp neuron.o $(LDLIBS) -o test_neuron

neuralsampler: neuron.o network.o myrandom.h neuron.h network.h main.cpp
	g++ $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) -o neuralsampler neuron.o network.o main.cpp $(LDLIBS)




all: neuralsampler test_neuron test_network

clean:
	$(RM) $(OBJS)
	$(RM) *.gch
