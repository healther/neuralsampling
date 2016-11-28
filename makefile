CXX=g++
CPPFLAGS=-O3
LDFLAGS=
LDLIBS=-lm -lyaml-cpp
INCLUDEPATH=
LIBPATH=

OBJS=neuralsampler network.o neuron.o

bin: bin/neuralsampler

all: bin/neuralsampler tests/test_neuron tests/test_network

test: tests/test_neuron tests/test_network
	tests/test_neuron
	tests/test_network
	python generate/config.py
	python generate/misc.py
	python generate/ising.py
	python generate/analysis.py
	python generate/tsp.py
	python generate/collect.py

clean:
	$(RM) build/*
	$(RM) bin/*
	$(RM) test/*
	$(RM) src/*.gch
	$(RM) *.tmp

build/network.o: src/network.cpp src/neuron.h src/network.h
	$(CXX) $(CPPFLAGS) -c src/network.cpp -o build/network.o

tests/test_network: src/network_test.cpp src/neuron.h build/neuron.o build/network.o src/network.h
	$(CXX) $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) src/network_test.cpp build/neuron.o build/network.o $(LDLIBS) -o tests/test_network

build/neuron.o: src/neuron.cpp src/neuron.h
	$(CXX) $(CPPFLAGS) -c src/neuron.cpp -o build/neuron.o

tests/test_neuron: src/neuron_test.cpp src/neuron.cpp src/neuron.h
	$(CXX) $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) src/neuron_test.cpp build/neuron.o $(LDLIBS) -o tests/test_neuron

bin/neuralsampler: build/neuron.o build/network.o src/myrandom.h src/neuron.h src/network.h src/main.h src/main.cpp
	$(CXX) $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) -o bin/neuralsampler build/neuron.o build/network.o src/main.cpp $(LDLIBS)




