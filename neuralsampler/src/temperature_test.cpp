#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include "temperature.h"

SCENARIO("Temperature Constructor") {

    GIVEN("Node Constructor Const") {
        YAML::Node node = YAML::Load("times: [0, 10, 20]\nvalues: [1, .5, 2.]");
        Temperature t = Temperature(Const, node);

        REQUIRE(t.get_temperature(0) == 1.);
        REQUIRE(t.get_temperature(9) == 1.);
        REQUIRE(t.get_temperature(10) == .5);
        REQUIRE(t.get_temperature(19) == .5);
        // CHECK_THROWS(t.get_temperature(20));
    }


}
