CXX=g++
CPPFLAGS=-O3 -std=c++11 -ftrapv -Wall -Wpedantic -Wextra
LDFLAGS=
LDLIBS=-lm -lyaml-cpp
INCLUDEPATH=
LIBPATH=

LATEXEXE=lualatex
MV=mv

TESTCXX=$(CXX) $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS)
OCXX=$(CXX) $(CPPFLAGS)

OBJS=neuralsampler network.o neuron.o

bin: bin/neuralsampler

all: bin test doc

test: tests/test_fixed_queue tests/test_neuron tests/test_config tests/test_network
	tests/test_fixed_queue
	tests/test_neuron
	tests/test_config
	tests/test_network

doc: doc/pdf/TSP.pdf

clean:
	$(RM) build/*
	$(RM) bin/*
	$(RM) test/*
	$(RM) src/*.gch
	$(RM) *.tmp

doc/pdf/TSP.pdf:
	$(LATEXEXE) -output-directory=tmp doc/tex/TSP/main.tex
	$(MV) tmp/main.pdf doc/pdf/TSP.pdf
	$(RM) tmp/main.aux tmp/main.log


build/fixed_queue.o: src/fixed_queue.cpp src/fixed_queue.h
	$(OCXX) -c src/fixed_queue.cpp -o build/fixed_queue.o

build/temperature.o: src/temperature.cpp src/temperature.h src/main.h src/type.h
	$(OCXX) -c src/temperature.cpp -o build/temperature.o

build/network.o: src/network.cpp src/network.h src/type.h src/type.h src/neuron.h src/config.h
	$(OCXX) -c src/network.cpp -o build/network.o

build/neuron.o: src/neuron.cpp src/neuron.h src/type.h src/fixed_queue.h
	$(OCXX) -c src/neuron.cpp -o build/neuron.o

build/config.o: src/config.cpp src/config.h src/type.h src/temperature.h src/main.h
	$(OCXX) -c src/config.cpp -o build/config.o


tests/test_temperature: src/temperature_test.cpp build/temperature.o
	$(TESTCXX) src/temperature_test.cpp build/temperature.o $(LDLIBS) -o tests/test_temperature

tests/test_fixed_queue: src/fixed_queue_test.cpp build/fixed_queue.o
	$(TESTCXX) src/fixed_queue_test.cpp build/fixed_queue.o $(LDLIBS) -o tests/test_fixed_queue

tests/test_network: src/network_test.cpp src/main.h src/myrandom.h build/network.o build/config.o build/neuron.o build/fixed_queue.o build/temperature.o
	$(TESTCXX) src/network_test.cpp build/network.o build/config.o build/fixed_queue.o build/neuron.o build/temperature.o $(LDLIBS) -o tests/test_network

tests/test_neuron: src/neuron_test.cpp src/myrandom.h build/neuron.o build/fixed_queue.o
	$(TESTCXX) src/neuron_test.cpp build/fixed_queue.o build/neuron.o $(LDLIBS) -o tests/test_neuron

tests/test_config: src/config_test.cpp src/config.o src/type.h src/main.h build/temperature.o
	$(TESTCXX) src/config_test.cpp build/config.o build/temperature.o $(LDLIBS) -o tests/test_config


bin/neuralsampler: src/main.cpp src/main.h src/myrandom.h build/config.o build/neuron.o build/network.o build/fixed_queue.o build/temperature.o
	$(CXX) $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) build/fixed_queue.o build/config.o build/neuron.o build/network.o build/temperature.o src/main.cpp $(LDLIBS) -o bin/neuralsampler

prof/profile: src/main.cpp src/main.h src/myrandom.h build/config.o build/neuron.o build/network.o build/fixed_queue.o build/temperature.o
	$(CXX) $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) -pg build/config.o build/neuron.o build/network.o build/fixed_queue.o build/temperature.o src/main.cpp $(LDLIBS) -o prof/profile
