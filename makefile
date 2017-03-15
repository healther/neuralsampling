CXX=g++
CPPFLAGS=-O2
LDFLAGS=
LDLIBS=-lm -lyaml-cpp
INCLUDEPATH=
LIBPATH=

LATEXEXE=lualatex
MV=mv

OBJS=neuralsampler network.o neuron.o

bin: bin/neuralsampler

all: bin test doc

test: tests/test_neuron tests/test_network
	tests/test_neuron
	tests/test_network
	python -m generate.analysis
	python -m generate.cluster
	python -m generate.collect
	python -m generate.config
	python -m generate.control
	python -m generate.misc
	python -m generate.plot
	python -m generate.problem_ising
	python -m generate.problem_sampling
	python -m generate.problem_tsp

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

build/temperature.o: src/temperature.cpp src/temperature.h src/main.h
	$(CXX) $(CPPFLAGS) -c src/temperature.cpp -o build/temperature.o

build/fixed_queue.o: src/fixed_queue.cpp src/fixed_queue.h
	$(CXX) $(CPPFLAGS) -c src/fixed_queue.cpp -o build/fixed_queue.o

build/network.o: src/network.cpp src/neuron.h src/network.h
	$(CXX) $(CPPFLAGS) -c src/network.cpp -o build/network.o

tests/test_network: src/network_test.cpp src/neuron.h src/network.h build/fixed_queue.o
	$(CXX) $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) src/network_test.cpp build/neuron.o build/network.o build/fixed_queue.o $(LDLIBS) -o tests/test_network

build/neuron.o: src/neuron.cpp src/neuron.h
	$(CXX) $(CPPFLAGS) -c src/neuron.cpp -o build/neuron.o

tests/test_neuron: src/neuron_test.cpp src/neuron.cpp src/neuron.h build/fixed_queue.o
	$(CXX) $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) src/neuron_test.cpp build/neuron.o build/fixed_queue.o $(LDLIBS) -o tests/test_neuron

bin/neuralsampler: src/main.cpp src/main.h src/myrandom.h build/neuron.o build/network.o build/fixed_queue.o build/temperature.o
	$(CXX) $(INCLUDEPATH) $(LIBPATH) $(LDFLAGS) $(CPPFLAGS) -o bin/neuralsampler build/neuron.o build/network.o build/fixed_queue.o build/temperature.o src/main.cpp $(LDLIBS)




