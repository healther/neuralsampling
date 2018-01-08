#define CATCH_CONFIG_MAIN
#include "catch.hpp"

#include "fixed_queue.h"

SCENARIO("Fixed Queue Constructor") {

    GIVEN("Small") {
        FixedQueue f = FixedQueue(3, 1);
        REQUIRE( f.position == 0 );
        f.add_entry(2);

        REQUIRE( f.content[0] == 1 );
        REQUIRE( f.content[1] == 1 );
        REQUIRE( f.content[2] == 2 );
        REQUIRE( f.content.size() == 3);
        REQUIRE( f.position == 1 );
        REQUIRE( f.return_entry() == 1);
        REQUIRE( f.return_entry() == 1);
        f.add_entry(3);
        REQUIRE( f.content[0] == 3 );
        REQUIRE( f.content[1] == 1 );
        REQUIRE( f.content[2] == 2 );
    }


}
