// SPDX-License-Identifier: GPL-3.0-or-later
#include "review_gate.h"

#include <cassert>

using namespace COPPERPATH_NATIVE;

int main()
{
#if defined( __APPLE__ )
    const std::string sample = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    assert( DigestMatches( "abc", sample ) );
    assert( !DigestMatches( "abcd", sample ) );
    assert( !DigestMatches( "abc", "" ) );
#endif

    const REVISION captured{ "frame / board", "selected UUID", "live PCB with J2 edit",
                             "saved PCB, rules, schematic", "Move selected right by 0.5 mm" };
    const MOVE checked{ captured.selection, { 14000000, 10000000 }, { 14500000, 10000000 } };
    REVIEW_GATE review;

    auto ticket = review.Begin( captured );
    assert( review.Receive( ticket, captured, checked ) );
    auto decision = review.Approve( captured );
    assert( decision && decision->to == checked.to );
    assert( !review.Approve( captured ) );
    assert( !review.Receive( ticket, captured, checked ) );

    auto oldTicket = review.Begin( captured );
    ticket = review.Begin( captured );
    assert( !review.Receive( oldTicket, captured, checked ) );
    assert( review.Receive( ticket, captured, checked ) );
    assert( !review.Receive( ticket, captured, checked ) );
    assert( review.Approve( captured ) );

    for( auto field : { &REVISION::document, &REVISION::selection, &REVISION::live,
                        &REVISION::saved, &REVISION::request } )
    {
        REVISION changed = captured;
        changed.*field += " changed";

        ticket = review.Begin( captured );
        assert( !review.Receive( ticket, changed, checked ) );
        assert( !review.Receive( ticket, captured, checked ) );
        assert( !review.Approve( captured ) );

        ticket = review.Begin( captured );
        assert( review.Receive( ticket, captured, checked ) );
        assert( !review.Approve( changed ) );
        assert( !review.Approve( captured ) );
    }

    ticket = review.Begin( captured );
    MOVE unrelated = checked;
    unrelated.selection = "unrelated UUID";
    assert( !review.Receive( ticket, captured, unrelated ) );
    assert( !review.Approve( captured ) );

    for( const std::array<int, 2>& invalid : { checked.from, { 14000001, 10000001 }, { 15000001, 10000000 } } )
    {
        ticket = review.Begin( captured );
        assert( !review.Receive( ticket, captured, MOVE{ captured.selection, checked.from, invalid } ) );
        assert( !review.Approve( captured ) );
    }

    ticket = review.Begin( captured );
    review.Invalidate();
    assert( !review.Receive( ticket, captured, checked ) );
    assert( !review.Approve( captured ) );
}
