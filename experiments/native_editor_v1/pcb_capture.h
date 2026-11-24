// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include "copperpath_pcb_move_review.h"

#include <memory>

#include <board.h>
#include <board_commit.h>
#include <footprint.h>
#include <kicad_clipboard.h>
#include <pcb_edit_frame.h>
#include <pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.h>
#include <project.h>
#include <tool/tool_manager.h>
#include <tools/pcb_selection_tool.h>

namespace COPPERPATH_NATIVE
{
inline std::string SerializePcb( BOARD& aBoard )
{
    std::string content;
    CLIPBOARD_IO serializer;
    serializer.SetWriter( [&]( const wxString& aContents )
    {
        auto utf8 = aContents.ToUTF8();

        if( utf8.data() )
            content.assign( utf8.data(), utf8.length() );
    } );
    serializer.SaveBoard( wxEmptyString, &aBoard, nullptr );
    return content;
}

inline std::optional<PCB_CAPTURE> CapturePcbMove( PCB_EDIT_FRAME& aFrame, const std::string& aRequest )
{
    BOARD* board = aFrame.GetBoard();
    TOOL_MANAGER* tools = aFrame.GetToolManager();
    auto* tool = tools ? tools->GetTool<PCB_SELECTION_TOOL>() : nullptr;

    if( !board || !tool || tool->GetSelection().Size() != 1
        || ( tools->GetCurrentTool() && tools->GetCurrentTool() != tool ) )
        return std::nullopt;

    auto* footprint = dynamic_cast<FOOTPRINT*>( *tool->GetSelection().begin() );
    wxString document = aFrame.Prj().AbsolutePath( board->GetFileName() );
    wxString expected;

    if( !footprint || footprint->IsLocked()
        || !wxGetEnv( wxS( "COPPERPATH_NATIVE_DOCUMENT" ), &expected ) || document != expected
        || ( footprint->GetReference() != wxS( "J1" ) && footprint->GetReference() != wxS( "J2" ) ) )
        return std::nullopt;

    std::string saved;
    wxFileName file( document );
    file.SetExt( wxS( "kicad_dru" ) );

    if( wxFileExists( file.GetFullPath() ) )
        return std::nullopt;

    for( const wxString& suffix : { wxS( "kicad_pcb" ), wxS( "kicad_pro" ), wxS( "kicad_sch" ) } )
    {
        file.SetExt( suffix );
        wxFile input( file.GetFullPath() );
        wxFileOffset count = input.IsOpened() ? input.Length() : 0;

        if( count <= 0 || count > 512 * 1024 )
            return std::nullopt;

        std::string data( static_cast<size_t>( count ), '\0' );

        if( input.Read( data.data(), data.size() ) != count )
            return std::nullopt;

        saved += std::to_string( count ) + ":" + data;
    }

    std::string live = SerializePcb( *board );

    if( live.empty() || live.size() > 512 * 1024 )
        return std::nullopt;

    const VECTOR2I position = footprint->GetPosition();
    return PCB_CAPTURE{
        { document.ToStdString() + "@" + std::to_string( reinterpret_cast<std::uintptr_t>( board ) ),
          footprint->m_Uuid.AsStdString(), std::move( live ), std::move( saved ), aRequest },
        footprint->GetReference().ToStdString(), { position.x, position.y }
    };
}

inline APPLY_RESULT ApplyPcbMove( PCB_EDIT_FRAME& aFrame, const MOVE& aMove,
                                  const PCB_CAPTURE& aCaptured, const CHECKED_PCB& aChecked )
{
    if( !aMove.IsSmallTranslation() )
        return APPLY_RESULT::REFUSED;

    const VECTOR2I offset( aMove.to[0] - aMove.from[0], aMove.to[1] - aMove.from[1] );

    BOARD* live = aFrame.GetBoard();
    FOOTPRINT* selected = nullptr;
    std::string expected;

    try
    {
        auto fresh = CapturePcbMove( aFrame, aCaptured.revision.request );

        if( !live || !fresh || !( fresh->revision == aCaptured.revision )
            || fresh->revision.selection != aMove.selection || fresh->from != aMove.from )
            return APPLY_RESULT::REFUSED;

        for( FOOTPRINT* footprint : live->Footprints() )
        {
            if( footprint->m_Uuid.AsStdString() == aMove.selection )
                selected = footprint;
        }

        PCB_IO_KICAD_SEXPR parser;
        std::unique_ptr<BOARD_ITEM> before( parser.Parse( wxString::FromUTF8( aChecked.before ) ) );
        std::unique_ptr<BOARD_ITEM> after( parser.Parse( wxString::FromUTF8( aChecked.after ) ) );
        BOARD* detachedBefore = dynamic_cast<BOARD*>( before.get() );
        BOARD* detachedAfter = dynamic_cast<BOARD*>( after.get() );

        if( !selected || !detachedBefore || !detachedAfter
            || SerializePcb( *detachedBefore ) != aCaptured.revision.live )
            return APPLY_RESULT::REFUSED;

        expected = SerializePcb( *detachedAfter );

        if( expected.empty() || expected == aCaptured.revision.live )
            return APPLY_RESULT::REFUSED;
    }
    catch( ... )
    {
        return APPLY_RESULT::REFUSED;
    }

    BOARD_COMMIT commit( &aFrame );
    bool pushing = false;

    try
    {
        commit.Modify( selected, nullptr, RECURSE_MODE::RECURSE );
        selected->Move( offset );

        if( SerializePcb( *live ) == expected )
        {
            pushing = true;
            commit.Push( wxS( "Copperpath checked component move" ) );
            return SerializePcb( *live ) == expected ? APPLY_RESULT::VERIFIED : APPLY_RESULT::UNCERTAIN;
        }
    }
    catch( ... )
    {
        if( pushing )
            return APPLY_RESULT::UNCERTAIN;
    }

    try
    {
        commit.Revert();
        return SerializePcb( *live ) == aCaptured.revision.live ? APPLY_RESULT::REFUSED : APPLY_RESULT::UNCERTAIN;
    }
    catch( ... )
    {
        return APPLY_RESULT::UNCERTAIN;
    }
}
}
