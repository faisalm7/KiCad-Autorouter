// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include "copperpath_review_gate.h"

#include <array>
#include <chrono>
#include <functional>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#include <kiid.h>
#include <nlohmann/json.hpp>
#include <wx/button.h>
#include <wx/file.h>
#include <wx/filename.h>
#include <wx/panel.h>
#include <wx/process.h>
#include <wx/sizer.h>
#include <wx/stattext.h>
#include <wx/textctrl.h>
#include <wx/utils.h>

namespace COPPERPATH_NATIVE
{
struct PCB_CAPTURE
{
    REVISION revision;
    std::string reference;
    std::array<int, 2> from;
};

struct CHECKED_PCB
{
    std::string before;
    std::string after;
};

enum class APPLY_RESULT { REFUSED, VERIFIED, UNCERTAIN };

// Each worker receives an owned byte snapshot and a typed request. Only a
// current successful result can draw a proposal. The editor owns approval.
class PCB_MOVE_REVIEW : public wxPanel
{
public:
    using CAPTURE = std::function<std::optional<PCB_CAPTURE>( const std::string& )>;
    using PREVIEW = std::function<bool( const MOVE* )>;
    using APPLY = std::function<APPLY_RESULT( const MOVE&, const PCB_CAPTURE&, const CHECKED_PCB& )>;

    PCB_MOVE_REVIEW( wxWindow& aParent, CAPTURE aCapture, PREVIEW aPreview, APPLY aApply ) :
            wxPanel( &aParent ),
            m_capture( std::move( aCapture ) ),
            m_preview( std::move( aPreview ) ),
            m_apply( std::move( aApply ) )
    {
        wxGetEnv( wxS( "COPPERPATH_NATIVE_PYTHON" ), &m_python );
        wxGetEnv( wxS( "COPPERPATH_NATIVE_RUNTIME" ), &m_runtime );
        wxGetEnv( wxS( "COPPERPATH_NATIVE_CHECKER" ), &m_checker );
        wxGetEnv( wxS( "COPPERPATH_NATIVE_SESSION" ), &m_session );
        m_enabled = wxFileName( m_python ).IsAbsolute() && wxFileExists( m_python )
                    && wxFileName( m_checker ).IsAbsolute() && wxFileExists( m_checker )
                    && wxFileName( m_runtime ).IsAbsolute() && wxDirExists( m_runtime )
                    && wxFileName( m_session ).IsAbsolute() && wxDirExists( m_session );
        auto* layout = new wxBoxSizer( wxVERTICAL );
        auto* actions = new wxBoxSizer( wxHORIZONTAL );
        int pad = FromDIP( 8 );
        m_request = new wxTextCtrl( this, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize,
                                   wxTE_PROCESS_ENTER );
        m_request->SetHint( wxS( "Move selected right by 0.5 mm" ) );
        m_check = new wxButton( this, wxID_ANY, wxS( "Check move" ) );
        m_stop = new wxButton( this, wxID_ANY, wxS( "Stop" ) );
        m_accept = new wxButton( this, wxID_ANY, wxS( "Apply checked move" ) );
        m_plan = new wxStaticText( this, wxID_ANY,
                                  m_enabled ? wxS( "Select J1 or J2. Local move check." )
                                            : wxS( "Move checks need the prepared worker." ) );
        layout->Add( m_request, 0, wxEXPAND | wxBOTTOM, pad );
        actions->Add( m_check, 0, wxRIGHT, pad );
        actions->Add( m_stop );
        layout->Add( actions, 0, wxBOTTOM, pad );
        layout->Add( m_plan, 0, wxEXPAND );
        layout->Add( m_accept, 0, wxTOP, pad );
        m_accept->Hide();
        SetSizer( layout );
        m_request->Enable( m_enabled );
        m_check->Enable( m_enabled );
        m_stop->Disable();
        m_request->Bind( wxEVT_TEXT, [this]( wxCommandEvent& ){ Invalidate(); } );
        m_request->Bind( wxEVT_TEXT_ENTER, [this]( wxCommandEvent& ){ Begin(); } );
        m_check->Bind( wxEVT_BUTTON, [this]( wxCommandEvent& ){ Begin(); } );
        m_stop->Bind( wxEVT_BUTTON, [this]( wxCommandEvent& ){ Invalidate(); } );
        m_accept->Bind( wxEVT_BUTTON, [this]( wxCommandEvent& ){ Apply(); } );
        Bind( wxEVT_END_PROCESS, &PCB_MOVE_REVIEW::Finished, this );
    }

    ~PCB_MOVE_REVIEW() override
    {
        Stop();
    }

    void Invalidate()
    {
        m_gate.Invalidate();
        m_checked.reset();
        m_preview( nullptr );
        m_accept->Hide();
        m_stop->SetLabel( wxS( "Stop" ) );
        m_stop->Disable();

        if( m_pid && !m_retired )
        {
            m_retired = true;
            m_stopDeadline = std::chrono::steady_clock::now() + std::chrono::seconds( 3 );
            SignalStop();
        }

        if( m_planVisible || m_pid )
            ShowStatus( m_pid ? ( m_termSent ? wxS( "Stopping the detached check…" )
                                             : wxS( "Stop signal unavailable. Waiting for the check to end." ) )
                              : wxS( "Check the current request." ) );

        m_planVisible = false;
    }

    void CheckDeadline()
    {
        if( !m_pid )
            return;

        auto now = std::chrono::steady_clock::now();

        if( !m_retired && now >= m_deadline )
            Invalidate();
        else if( m_retired && now >= m_stopDeadline && !m_stopRetried )
        {
            m_stopRetried = true;
            if( !m_termSent )
                SignalStop();

            ShowStatus( wxS( "Copperpath is waiting for the check to stop. Apply is unavailable." ) );
        }
    }

    bool CanClose()
    {
        if( !m_pid )
            return true;

        if( !m_retired )
            Invalidate();

        return false;
    }

    void RulesChanged()
    {
        Invalidate();
        m_enabled = false;
        m_request->Disable();
        m_check->Disable();
        ShowStatus( wxS( "Board setup changed. Reopen the unchanged test project for a checked move." ) );
    }

    void Stop()
    {
        m_gate.Invalidate();
        m_checked.reset();

        if( m_process )
        {
            if( !m_termSent )
                SignalStop();

            m_process->Detach();
            m_process = nullptr;
            m_pid = 0;
        }
    }

private:
    void SignalStop()
    {
        // SIGTERM lets the shared runner retire and reap its own Native group.
        m_termSent = wxProcess::Kill( m_pid, wxSIGTERM ) == wxKILL_OK;
    }

    void ShowStatus( const wxString& aText )
    {
        m_plan->SetLabelText( aText );
        m_plan->Wrap( FromDIP( 230 ) );
        Layout();
    }

    static bool Persist( const wxString& aName, const std::string& aText )
    {
        wxFile file( aName, wxFile::write_excl );
        return file.IsOpened() && file.Write( aText.data(), aText.size() ) == aText.size()
               && file.Close();
    }

    static std::string ReadResult( const wxString& aName, wxFileOffset aLimit )
    {
        wxFile file( aName );
        wxFileOffset count = file.IsOpened() ? file.Length() : 0;

        if( count <= 0 || count > aLimit )
            throw std::runtime_error( "missing or oversized result" );

        std::string data( static_cast<size_t>( count ), '\0' );

        if( file.Read( data.data(), data.size() ) != count )
            throw std::runtime_error( "incomplete result" );

        return data;
    }

    static std::array<int, 2> Position( const nlohmann::json& aValue )
    {
        if( !aValue.is_array() || aValue.size() != 2 )
            throw std::runtime_error( "checked position has the wrong shape" );

        std::array<int, 2> result;

        for( size_t i = 0; i < result.size(); ++i )
        {
            if( !aValue[i].is_number_integer() )
                throw std::runtime_error( "checked position must use integer nanometres" );

            auto number = aValue[i].get<std::int64_t>();

            if( number < std::numeric_limits<int>::min() || number > std::numeric_limits<int>::max() )
                throw std::runtime_error( "checked position is out of range" );

            result[i] = static_cast<int>( number );
        }

        return result;
    }

    static std::string RequestRecord( const PCB_CAPTURE& aState )
    {
        return nlohmann::json{
            { "schema", 1 }, { "editor_format", "clipboard" }, { "request", aState.revision.request },
            { "selection", { { "ref", aState.reference }, { "uid", aState.revision.selection },
                              { "from_nm", aState.from } } }
        }.dump();
    }

    void Apply()
    {
        if( !m_planVisible || m_pid || !m_checked || !m_apply || !m_accept->IsShownOnScreen() )
            return;

        std::optional<PCB_CAPTURE> now;

        try
        {
            now = m_capture( m_request->GetValue().ToStdString( wxConvUTF8 ) );
        }
        catch( const std::exception& )
        {
            now.reset();
        }

        auto move = now ? m_gate.Approve( now->revision ) : std::nullopt;
        CHECKED_PCB checked = std::move( *m_checked );
        Invalidate();

        if( !move )
        {
            ShowStatus( wxS( "The board changed. Check the request again." ) );
            return;
        }

        // A consumed approval can never be replayed after a failed or uncertain transaction.
        const APPLY_RESULT result = m_apply( *move, *now, checked );
        m_enabled = false;
        m_request->Disable();
        m_check->Disable();

        if( result == APPLY_RESULT::VERIFIED )
            ShowStatus( wxS( "Move verified in KiCad. Use Edit → Undo to recover it." ) );
        else if( result == APPLY_RESULT::REFUSED )
            ShowStatus( wxS( "KiCad refused the exact move. No transaction was committed." ) );
        else
            ShowStatus( wxS( "Move outcome uncertain. Inspect the editor and its Undo history." ) );
    }

    void Begin()
    {
        if( !m_enabled || m_pid )
            return;

        Invalidate();
        std::string request = m_request->GetValue().ToStdString( wxConvUTF8 );

        if( request.empty() || request.size() > 128 )
        {
            ShowStatus( wxS( "Describe one move of up to 1 mm." ) );
            return;
        }

        std::optional<PCB_CAPTURE> captured;

        try
        {
            captured = m_capture( request );
        }
        catch( const std::exception& )
        {
            ShowStatus( wxS( "KiCad could not capture the current PCB." ) );
            return;
        }

        if( !captured )
        {
            ShowStatus( wxS( "Select one supported footprint on the prepared PCB." ) );
            return;
        }

        wxString id = KIID().AsString();
        id.Replace( wxS( "-" ), wxEmptyString );
        m_job = m_session + wxS( "/native-jobs/" ) + id;
        if( !wxFileName::Mkdir( m_job, 0700, wxPATH_MKDIR_FULL )
            || !Persist( m_job + wxS( "/request.json" ), RequestRecord( *captured ) )
            || !Persist( m_job + wxS( "/snapshot.kicad_pcb" ), captured->revision.live ) )
        {
            ShowStatus( wxS( "The private validation copy could not be created." ) );
            return;
        }

        m_ticket = m_gate.Begin( std::move( captured->revision ) );
        m_retired = false;
        m_termSent = false;
        m_stopRetried = false;
        m_process = new wxProcess( this );
        const std::vector<wxString> args{ m_python, wxS( "-I" ), wxS( "-B" ), m_checker,
                                         wxS( "--runtime" ), m_runtime, wxS( "--job" ), m_job };
        std::vector<std::wstring> wideArgs;
        std::vector<const wchar_t*> argv;

        for( const wxString& arg : args )
            wideArgs.push_back( arg.ToStdWstring() );

        for( const std::wstring& arg : wideArgs )
            argv.push_back( arg.c_str() );
        argv.push_back( nullptr );
        wxExecuteEnv env;
        env.cwd = m_job;
        for( const wxString& key : { wxS( "HOME" ), wxS( "PATH" ), wxS( "TMPDIR" ), wxS( "USER" ),
                                    wxS( "LANG" ), wxS( "LC_ALL" ), wxS( "KICAD_CONFIG_HOME" ),
                                    wxS( "KICAD_CACHE_HOME" ), wxS( "KICAD_DOCUMENTS_HOME" ) } )
        {
            wxString value;

            if( wxGetEnv( key, &value ) )
                env.env[key] = value;
        }
        m_pid = wxExecute( argv.data(), wxEXEC_ASYNC | wxEXEC_HIDE_CONSOLE, m_process, &env );

        if( !m_pid )
        {
            delete m_process;
            m_process = nullptr;
            m_gate.Invalidate();
            ShowStatus( wxS( "Could not start the detached check." ) );
            return;
        }

        m_check->Disable();
        m_stop->Enable();
        m_deadline = std::chrono::steady_clock::now() + std::chrono::seconds( 50 );
        ShowStatus( wxS( "Checking an isolated copy with KiCad…" ) );
    }

    void Finished( wxProcessEvent& aEvent )
    {
        if( aEvent.GetPid() != m_pid || !m_process )
            return;

        delete m_process;
        m_process = nullptr;
        m_pid = 0;
        m_check->Enable( m_enabled );
        m_stop->Disable();

        if( m_retired || aEvent.GetExitCode() != 0 || std::chrono::steady_clock::now() >= m_deadline )
        {
            m_gate.Invalidate();
            ShowStatus( m_retired ? wxS( "Check stopped. No proposal kept." )
                                  : wxS( "KiCad could not verify this move." ) );
            return;
        }

        try
        {
            auto fresh = m_capture( m_request->GetValue().ToStdString( wxConvUTF8 ) );

            if( !fresh )
                throw std::runtime_error( "stale check" );

            auto value = nlohmann::json::parse( ReadResult( m_job + wxS( "/checked-result.json" ), 2 * 1024 * 1024 ) );
            auto& plan = value.at( "plan" );
            auto& findings = value.at( "findings" );
            const std::string request = RequestRecord( *fresh );
            CHECKED_PCB checked{
                value.at( "before" ).get<std::string>(), value.at( "candidate" ).get<std::string>()
            };
            MOVE move{ plan.at( "uid" ).get<std::string>(), Position( plan.at( "from_nm" ) ),
                       Position( plan.at( "to_nm" ) ) };

            if( value.at( "schema" ) != 1 || value.at( "status" ) != "checked"
                || value.at( "request" ).dump() != request || plan.at( "ref" ) != fresh->reference
                || !DigestMatches( request, value.at( "request_sha256" ).get<std::string>() )
                || !DigestMatches( fresh->revision.live, value.at( "snapshot_sha256" ).get<std::string>() )
                || !DigestMatches( checked.before, value.at( "checked_before_sha256" ).get<std::string>() )
                || !DigestMatches( checked.after, value.at( "checked_candidate_sha256" ).get<std::string>() )
                || move.from != fresh->from || !m_gate.Receive( m_ticket, fresh->revision, move ) )
                throw std::runtime_error( "check no longer matches the selected item" );

            if( m_apply )
                m_checked = std::move( checked );

            if( !m_preview( &move ) )
                throw std::runtime_error( "proposal was not drawn on the current canvas" );
            m_planVisible = true;
            m_stop->SetLabel( wxS( "Discard" ) );
            m_stop->Enable();
            m_accept->Show( bool( m_apply ) );
            ShowStatus( wxString::Format( wxS( "Proposed position %.3f, %.3f mm\nExisting findings retained: %d open, %d warnings\n%s" ),
                move.to[0] / 1000000., move.to[1] / 1000000.,
                findings.at( "opens" ).get<int>(), findings.at( "warnings" ).get<int>(),
                m_apply ? wxS( "Ready for review" ) : wxS( "Preview only" ) ) );
        }
        catch( const std::exception& )
        {
            m_gate.Invalidate();
            m_checked.reset();
            m_preview( nullptr );
            m_accept->Hide();
            m_planVisible = false;
            m_stop->SetLabel( wxS( "Stop" ) );
            m_stop->Disable();
            ShowStatus( wxS( "This check is unavailable or stale. Check again." ) );
        }
    }

    CAPTURE             m_capture;
    PREVIEW             m_preview;
    APPLY               m_apply;
    REVIEW_GATE         m_gate;
    std::optional<CHECKED_PCB> m_checked;
    REVIEW_GATE::TICKET m_ticket = 0;
    wxTextCtrl*         m_request;
    wxButton*           m_check;
    wxButton*           m_stop;
    wxButton*           m_accept;
    wxStaticText*       m_plan;
    wxString            m_python, m_runtime, m_checker, m_session, m_job;
    wxProcess*          m_process = nullptr;
    std::chrono::steady_clock::time_point m_deadline, m_stopDeadline;
    long                m_pid = 0;
    bool                m_enabled = false;
    bool                m_retired = false;
    bool                m_termSent = false;
    bool                m_stopRetried = false;
    bool                m_planVisible = false;
};
}
