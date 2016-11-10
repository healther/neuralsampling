#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include "neuron.h"
#include "myrandom.h"

SCENARIO("Neuron constructor") {

    GIVEN("Rectangular neuron - active") {
        Neuron n(100, 100, 99, Log, Rect);

        REQUIRE( n.get_internalstate()==99 );
        REQUIRE( n.get_state()== 1);
        REQUIRE( n.get_interaction() == 1. );
        REQUIRE( n.activation(0.) == 0.5 );
        
        WHEN("State is updated - impossible to spike") {
            n.update_state(-50.);
            REQUIRE( n.get_internalstate() == 100 );
            REQUIRE( n.get_state() == 0 );
            REQUIRE( n.get_interaction() == 1. );
            n.update_interaction();
            REQUIRE( n.get_interaction() == 0. );
        }
        WHEN("State is updated - inevitable to spike") {
            n.update_state(50.);
            REQUIRE( n.get_internalstate() == 0 );
            REQUIRE( n.get_state() == 1 );
            REQUIRE( n.get_interaction() == 1. );
            n.update_interaction();
            REQUIRE( n.get_interaction() == 1. );
        }
    }

    GIVEN("Exponential neuron - active") {
        Neuron n(100, 100, 99, Log, Exp);

        REQUIRE( n.get_internalstate()==99 );
        REQUIRE( n.get_state()== 1);
        double f_int = std::exp(-0.99)/(1.-std::exp(-1.));
        REQUIRE( n.get_interaction() == f_int );
        REQUIRE( n.activation(0.) == 0.5 );
        
        WHEN("State is updated - impossible to spike") {
            n.update_state(-50.);
            REQUIRE( n.get_internalstate() == 100 );
            REQUIRE( n.get_state() == 0 );
            REQUIRE( n.get_interaction() == f_int );
            n.update_interaction();
            f_int = std::exp(-1.)/(1.-std::exp(-1.));
            REQUIRE( n.get_interaction() == f_int );
        }
        WHEN("State is updated - inevitable to spike") {
            n.update_state(50.);
            REQUIRE( n.get_internalstate() == 0 );
            REQUIRE( n.get_state() == 1 );
            REQUIRE( n.get_interaction() == f_int );
            n.update_interaction();
            f_int = 1./(1.-std::exp(-1.));
            REQUIRE( n.get_interaction() == f_int );
        }

    }


}




