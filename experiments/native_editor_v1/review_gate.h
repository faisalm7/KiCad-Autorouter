// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>

#if defined( __APPLE__ )
#include <CommonCrypto/CommonDigest.h>
#endif

namespace COPPERPATH_NATIVE
{
inline bool DigestMatches( const std::string& aBytes, const std::string& aDigest )
{
#if defined( __APPLE__ )
    if( aBytes.size() > 2 * 1024 * 1024 || aDigest.size() != 64 )
        return false;

    unsigned char hash[CC_SHA256_DIGEST_LENGTH];
    CC_SHA256( aBytes.data(), static_cast<CC_LONG>( aBytes.size() ), hash );
    constexpr char hex[] = "0123456789abcdef";

    for( size_t i = 0; i < sizeof( hash ); ++i )
    {
        if( aDigest[2 * i] != hex[hash[i] >> 4] || aDigest[2 * i + 1] != hex[hash[i] & 15] )
            return false;
    }

    return true;
#else
    (void) aBytes;
    (void) aDigest;
    return false;
#endif
}

// Exact captured state from one editor. Files and live serialized state
// are independent because the editor can hold unsaved changes.
struct REVISION
{
    std::string document;
    std::string selection;
    std::string live;
    std::string saved;
    std::string request;

    bool operator==( const REVISION& aOther ) const
    {
        return document == aOther.document && selection == aOther.selection
               && live == aOther.live && saved == aOther.saved && request == aOther.request;
    }
};

struct MOVE
{
    std::string selection;
    std::array<int, 2> from;
    std::array<int, 2> to;

    bool IsSmallTranslation() const
    {
        const std::int64_t dx = std::int64_t( to[0] ) - from[0];
        const std::int64_t dy = std::int64_t( to[1] ) - from[1];
        return ( dx == 0 ) != ( dy == 0 ) && dx >= -1000000 && dx <= 1000000
               && dy >= -1000000 && dy <= 1000000;
    }
};

// All transitions run on the editor thread. A detached worker has only its
// ticket and can return findings. The UI supplies the current revision again
// for every decision, including the exact event that will apply the edit.
class REVIEW_GATE
{
public:
    using TICKET = std::uint64_t;

    TICKET Begin( REVISION aCaptured )
    {
        Invalidate();
        m_capture = std::move( aCaptured );
        return m_ticket;
    }

    bool Receive( TICKET aTicket, const REVISION& aNow, MOVE aChecked )
    {
        if( aTicket != m_ticket || !m_capture || m_checked )
            return false;

        if( !( *m_capture == aNow ) || aChecked.selection != aNow.selection || !aChecked.IsSmallTranslation() )
        {
            Invalidate();
            return false;
        }

        m_checked = std::move( aChecked );
        return true;
    }

    std::optional<MOVE> Approve( const REVISION& aNow )
    {
        std::optional<MOVE> result;

        if( m_capture && *m_capture == aNow && m_checked )
            result = std::move( m_checked );

        Invalidate();
        return result;
    }

    void Invalidate()
    {
        ++m_ticket;
        m_capture.reset();
        m_checked.reset();
    }

private:
    TICKET m_ticket = 0;
    std::optional<REVISION> m_capture;
    std::optional<MOVE> m_checked;
};
}
