// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include <functional>
#include <memory>
#include <optional>
#include <utility>

#include "copperpath_pcb_move_review.h"

#include <view/view.h>
#include <view/view_overlay.h>
#include <wx/aui/aui.h>
#include <wx/button.h>
#include <wx/panel.h>
#include <wx/sizer.h>
#include <wx/stattext.h>
#include <wx/timer.h>
#include <wx/utils.h>

namespace COPPERPATH_NATIVE
{
inline const wxString PANE_NAME = wxS( "CopperpathNative" );

struct SELECTION_FACTS
{
    wxString document;
    wxString identity;
    wxString label;
    wxString sheet;
    VECTOR2I anchor;
    BOX2I bounds;
    double unitsPerMillimetre;

    bool SameTarget( const SELECTION_FACTS& aOther ) const
    {
        return document == aOther.document && identity == aOther.identity
               && sheet == aOther.sheet && anchor == aOther.anchor
               && bounds.GetOrigin() == aOther.bounds.GetOrigin()
               && bounds.GetSize() == aOther.bounds.GetSize();
    }
};

class EDITOR_PANE : public wxPanel
{
public:
    using READ = std::function<std::optional<SELECTION_FACTS>()>;
    using VIEW = std::function<KIGFX::VIEW*()>;

    EDITOR_PANE( wxWindow& aParent, wxWindow& aCanvas, wxString aDocument, READ aRead, VIEW aView,
                 PCB_MOVE_REVIEW::CAPTURE aCapture, PCB_MOVE_REVIEW::APPLY aApply ) :
            wxPanel( &aParent ),
            m_canvas( aCanvas ),
            m_document( std::move( aDocument ) ),
            m_read( std::move( aRead ) ),
            m_view( std::move( aView ) ),
            m_timer( this )
    {
        wxBoxSizer* layout = new wxBoxSizer( wxVERTICAL );
        int pad = FromDIP( 10 );
        m_selection = new wxStaticText( this, wxID_ANY, wxS( "Select one item on the canvas." ) );
        m_position = new wxStaticText( this, wxID_ANY, wxEmptyString );
        m_locate = new wxButton( this, wxID_ANY, wxS( "Show selection" ) );
        layout->Add( m_selection, 0, wxLEFT | wxRIGHT | wxTOP, pad );
        layout->Add( m_position, 0, wxLEFT | wxRIGHT | wxTOP, pad );
        layout->Add( m_locate, 0, wxALL, pad );
        if( aCapture )
        {
            m_move = new PCB_MOVE_REVIEW( *this, std::move( aCapture ),
                    [this]( const MOVE* aMove ){ return ShowMove( aMove ); }, std::move( aApply ) );
            layout->Add( m_move, 0, wxEXPAND | wxLEFT | wxRIGHT | wxBOTTOM, pad );
        }
        else
        {
            layout->Add( new wxStaticText( this, wxID_ANY, wxS( "Native inspection · read only" ) ),
                         0, wxLEFT | wxRIGHT | wxBOTTOM, pad );
        }
        SetSizer( layout );
        m_locate->Disable();

        m_locate->Bind( wxEVT_BUTTON, [this]( wxCommandEvent& ){ Locate(); } );
        Bind( wxEVT_TIMER, [this]( wxTimerEvent& ){ ReadSelection(); }, m_timer.GetId() );
        m_timer.Start( 250 );
    }

    void Stop()
    {
        m_timer.Stop();
        if( m_move )
            m_move->Stop();
        m_overlay.reset();
        m_proposal.reset();
        m_highlightView = nullptr;
        m_current.reset();
    }

    void ViewChanging()
    {
        if( m_move )
            m_move->Invalidate();
        ClearHighlight();
    }

    void RulesChanged()
    {
        if( m_move )
            m_move->RulesChanged();
    }

    bool CanClose()
    {
        return !m_move || m_move->CanClose();
    }

private:
    void ClearHighlight()
    {
        if( m_overlay )
        {
            m_overlay.reset();
            if( !m_proposal )
                m_highlightView = nullptr;
            m_canvas.Refresh();
            m_locate->SetLabel( wxS( "Show selection" ) );
        }
    }

    void ReadSelection()
    {
        if( m_move )
            m_move->CheckDeadline();

        if( !IsShownOnScreen() )
        {
            ViewChanging();
            return;
        }

        auto current = m_read();

        if( ( m_overlay || m_proposal ) && m_view() != m_highlightView )
            ViewChanging();

        if( current && current->document != m_document )
            current.reset();

        if( current && m_current && current->SameTarget( *m_current ) )
            return;

        if( !current && !m_current )
            return;

        ViewChanging();
        m_current = std::move( current );
        m_locate->Enable( m_current.has_value() );

        if( m_current )
        {
            m_selection->SetLabel( m_current->label );
            m_position->SetLabel( wxString::Format( wxS( "X %.3f mm   Y %.3f mm" ),
                m_current->anchor.x / m_current->unitsPerMillimetre,
                m_current->anchor.y / m_current->unitsPerMillimetre ) );
        }
        else
        {
            m_selection->SetLabel( wxS( "Select one item on the prepared design." ) );
            m_position->SetLabel( wxEmptyString );
        }

        Layout();
    }

    void Locate()
    {
        ReadSelection();

        if( m_overlay )
        {
            ClearHighlight();
            return;
        }

        KIGFX::VIEW* view = m_view();

        if( !m_current || !view )
            return;

        m_overlay = DrawOutline( *view, m_current->bounds, KIGFX::COLOR4D( 0.1, 0.7, 0.9, 1.0 ) );
        m_locate->SetLabel( wxS( "Clear highlight" ) );
    }

    std::shared_ptr<KIGFX::VIEW_OVERLAY> DrawOutline( KIGFX::VIEW& aView, BOX2I aBounds,
                                                     const KIGFX::COLOR4D& aColour )
    {
        const double units = m_current->unitsPerMillimetre;
        BOX2I frame = aBounds;
        frame.Inflate( static_cast<int>( 0.25 * units ) );
        auto outline = aView.MakeOverlay();
        m_highlightView = &aView;
        outline->SetIsFill( false );
        outline->SetIsStroke( true );
        outline->SetStrokeColor( aColour );
        outline->SetLineWidth( 0.12 * units );
        const VECTOR2I start = frame.GetOrigin();
        const VECTOR2I end = frame.GetEnd();
        outline->Rectangle( VECTOR2D( start.x, start.y ), VECTOR2D( end.x, end.y ) );
        aView.Update( outline.get() );
        m_canvas.Refresh();
        return outline;
    }

    bool ShowMove( const MOVE* aMove )
    {
        if( m_proposal )
        {
            m_proposal.reset();
            m_canvas.Refresh();
        }

        if( !aMove )
            return true;

        if( !m_current || m_current->identity.ToStdString() != aMove->selection )
            return false;

        if( KIGFX::VIEW* view = m_view() )
        {
            BOX2I moved = m_current->bounds;
            moved.Move( VECTOR2I( aMove->to[0] - aMove->from[0], aMove->to[1] - aMove->from[1] ) );
            m_proposal = DrawOutline( *view, moved, KIGFX::COLOR4D( 1.0, 0.66, 0.18, 1.0 ) );
            return true;
        }

        return false;
    }

    wxWindow&                      m_canvas;
    wxString                       m_document;
    READ                           m_read;
    VIEW                           m_view;
    wxTimer                        m_timer;
    wxStaticText*                  m_selection;
    wxStaticText*                  m_position;
    wxButton*                      m_locate;
    PCB_MOVE_REVIEW*               m_move = nullptr;
    std::optional<SELECTION_FACTS> m_current;
    std::shared_ptr<KIGFX::VIEW_OVERLAY> m_overlay;
    std::shared_ptr<KIGFX::VIEW_OVERLAY> m_proposal;
    KIGFX::VIEW*                   m_highlightView = nullptr;
};

inline void Attach( wxWindow& aParent, wxAuiManager& aManager, wxWindow& aCanvas,
                    EDITOR_PANE::READ aRead, EDITOR_PANE::VIEW aView,
                    PCB_MOVE_REVIEW::CAPTURE aCapture = {}, PCB_MOVE_REVIEW::APPLY aApply = {} )
{
    wxString document;

    if( !wxGetEnv( wxS( "COPPERPATH_NATIVE_DOCUMENT" ), &document ) || document.IsEmpty()
        || aManager.GetManagedWindow() != &aParent || aManager.GetPane( PANE_NAME ).IsOk() )
        return;

    auto* panel = new EDITOR_PANE( aParent, aCanvas, document, std::move( aRead ), std::move( aView ),
                                  std::move( aCapture ), std::move( aApply ) );
    wxAuiPaneInfo info;
    info.Name( PANE_NAME ).Caption( wxS( "Copperpath" ) ).Left().Layer( 1 )
        .MinSize( aParent.FromDIP( wxSize( 230, 128 ) ) )
        .BestSize( aParent.FromDIP( wxSize( 270, 200 ) ) )
        .Floatable( false ).CloseButton( false );

    if( !aManager.AddPane( panel, info ) )
        panel->Destroy();
}

inline void Stop( wxAuiManager& aManager )
{
    wxAuiPaneInfo& pane = aManager.GetPane( PANE_NAME );

    if( pane.IsOk() )
        static_cast<EDITOR_PANE*>( pane.window )->Stop();
}

inline void ViewChanging( wxAuiManager& aManager )
{
    wxAuiPaneInfo& pane = aManager.GetPane( PANE_NAME );

    if( pane.IsOk() )
        static_cast<EDITOR_PANE*>( pane.window )->ViewChanging();
}

inline void RulesChanged( wxAuiManager& aManager )
{
    wxAuiPaneInfo& pane = aManager.GetPane( PANE_NAME );

    if( pane.IsOk() )
        static_cast<EDITOR_PANE*>( pane.window )->RulesChanged();
}

inline bool CanClose( wxAuiManager& aManager )
{
    wxAuiPaneInfo& pane = aManager.GetPane( PANE_NAME );
    return !pane.IsOk() || static_cast<EDITOR_PANE*>( pane.window )->CanClose();
}
}
