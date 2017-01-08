#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include "network.h"
#include "neuron.h"
#include "myrandom.h"

SCENARIO("Network constructor") {

    GIVEN("3 Neuron network") {
        std::vector<double> biases {0., 1., -1.};
        std::vector< std::vector<double> > weights { {0., 1., 0.5}, {1., 0., 0.5}, {1., 0.5, 0.}};
        std::vector<int> initialstate {0, 4, 8};
        int tauref = 5;
        int tausyn = 5;
        int delay = 1;
        TActivation act = Log;
        TInteraction inter = Rect;
        TUpdateScheme updscheme = InOrder;
        TOutputScheme outscheme = MeanActivityOutput;

        Network n(biases, weights, initialstate, tauref, tausyn, delay, outscheme, updscheme, act, inter);
        REQUIRE( n.states[0] == 1 );
        REQUIRE( n.states[1] == 1 );
        REQUIRE( n.states[2] == 0 );
        n.get_internalstate();
        REQUIRE( n.states[0] == 0 );
        REQUIRE( n.states[1] == 4 );
        REQUIRE( n.states[2] == 8 );

    }


}
