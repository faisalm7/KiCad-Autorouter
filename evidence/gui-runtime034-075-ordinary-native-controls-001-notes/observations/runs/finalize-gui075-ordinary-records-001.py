"""Record lead-observed075 facts with the existing074 finalization pattern.

No Native validation, GUI action or new acceptance is performed here.
"""
from pathlib import Path
import datetime, hashlib, json, subprocess
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'.runs/runtime-directory-034/runtime/.runs/gui-session075'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
load=lambda path:json.loads(Path(path).read_bytes())
ids=dict(positive='33391da753054a0fa2dfbbeea16c4a1c',high_budget='fe50d5d294414bb8978419f078dd55b0',
    source_control='37c8dce6645246efb3a19c0e2c565151',settings_control='9bc11f224a8244fab5101966e23ed71c',
    export_control='688b1e03db4b4a07b4146a13a83f2c75',reject='0ffc7e610955462a997492263e8d5ed4',
    cancel='8d2f6d99e0cc48858aed4df0ec759fd6')
jobs={k:str(base/'jobs'/('autorouter-gui-'+v)) for k,v in ids.items()}
assert {p.name for p in (base/'jobs').iterdir()}=={'autorouter-gui-'+v for v in ids.values()}
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
prepared=load(base/'prepared-state.json')
rejected=load(Path(jobs['reject'])/'choice/choice.json')
assert rejected['choice']=='reject' and rejected['choice_recorded'] is True
assert not (Path(jobs['reject'])/'export').exists()
cancel=Path(jobs['cancel']);result=load(cancel/'route/result.json')
process=load(cancel/'route.command.process.json');engine=load(cancel/'route/engine-process.json')
observed=load(base/'actual-engine-observation-001.json')
assert result['accepted'] is False and result['status']=='cancelled' and not (cancel/'export').exists()
assert process['exit_code']==2 and process['cancel_requested'] is True and not process['log_truncated']
assert engine['status']=='cancelled' and engine['cleanup_complete'] is True
assert observed['actual_engine_observed'] is True and observed['observed_phase']=='ordinary-engine'
assert engine['pid']==observed['PID'] and engine['cancel_signal']=='SIGINT'
absence={}
for pid in (observed['PID'],observed['PPID']):
    check=subprocess.run(['/bin/ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=2)
    assert check.returncode==1 and not check.stdout.strip()
    absence[str(pid)]=True
cancellation=dict(schema=1,recorded_utc=now,workspace=str(cancel),actual_GUI_cancel_clicked=True,
    actual_GUI_message='Action was cancelled. No positive UI state adopted.',observed_phase='engine',
    engine_observation_sha256=sha(base/'actual-engine-observation-001.json'),engine_PID=engine['pid'],
    requested_signal=engine['cancel_signal'],engine_final_exit_code=engine['exit_code'],engine_cleanup_complete=True,
    CLI_process=process,result_status=result['status'],accepted=False,export_created=False,
    observed_PID_absence=absence,scope='One actual GUI engine-phase cancellation on licensed exposed Interf; protected0. '
    'Source Native findings remain visible. SIGINT requested, final negative exit retained; no SIGINT-only, '
    'all-phase or permanent-descendant claim. This is one absence snapshot, never permission to kill a reused PID.')
with (base/'actual-GUI-cancellation-001.json').open('x') as stream:
    json.dump(cancellation,stream,indent=2);stream.write('\n')
privacy=dict(public_projection=True,raw_browser_screenshots_excluded=True,full_browser_AX_excluded=True,
    raw_capture_filenames_excluded=True,all_PNG_Mac_only=True)
extra=[]
def include(path,kind):
    path=Path(path);assert path.is_file() and path.suffix not in ('.png','.jpg','.jpeg')
    extra.append(dict(path=str(path),sha256=sha(path),kind=kind))
for name in ('postopen-001.json','actual-GUI-cancellation-001.json','actual-engine-observation-001.json'):
    include(base/name,'owned_observation_receipt')
include(base.parent/'gui-launcher075/install.json','owned_observation_receipt')
for name in ('prepare-runtime034-gui075.py','prepare-gui075-controls-001.py','gui075-preopen-001.py',
    'gui075-postopen-001.py','gui075-mutate-control-001.py','gui075-watch-owned-engine-001.py',
    'record-gui075-fault-observation-001.py',Path(__file__).name):
    include(ROOT/'.runs'/name,'owned_controller')
for name in ('prepare-runtime034-gui075-time-001.log','prepare-gui075-controls-001-time.log',
    'gui075-positive-preopen-001-time.log','gui075-positive-postopen-001-time.log','gui075-high-preopen-001-time.log',
    'gui075-source-preopen-001-time.log','gui075-source-mutate-001-time.log','gui075-settings-preopen-001-time.log',
    'gui075-settings-mutate-001-time.log','gui075-export-preopen-001-time.log','gui075-export-mutate-001-time.log',
    'gui075-watch-ordinary-001-time.log'):
    include(ROOT/'.runs'/name,'owned_process_log')
observations=base/'actual-GUI-observations-001'
for name,kind in (
    ('005-current-toolbar-launch-AX.txt','owned_router_ax'),('007-invalid-budget-refused-AX.txt','owned_router_ax'),
    ('008-preset-loaded-AX.txt','owned_router_ax'),('009-preset-saved-AX.txt','owned_router_ax'),
    ('012-first-route-completed-AX.txt','owned_router_ax'),('014-no-ack-accept-refused-AX.txt','owned_router_ax'),
    ('015-rendered-review-body-AX.txt','owned_review_body_ax'),('019-review-open-accept-refusal-AX.txt','owned_router_ax'),
    ('020-review-closed-AX.txt','owned_kicad_ax'),('023-first-export-verified-AX.txt','owned_router_ax'),
    ('027-export-editor-AX.txt','owned_kicad_ax'),('029-opened-export-closed-AX.txt','owned_kicad_ax'),
    ('031-postopen-stale-refused-AX.txt','owned_router_ax'),('037-high-export-complete-AX.txt','owned_router_ax'),
    ('043-source-control-open-refused-AX.txt','owned_router_ax'),('049-settings-control-open-refused-AX.txt','owned_router_ax'),
    ('055-export-control-open-refused-AX.txt','owned_router_ax'),('060-reject-complete-AX.txt','owned_router_ax'),
    ('068-route-method-settled-AX.txt','owned_router_ax'),('072-cancel-final-AX.txt','owned_router_ax')):
    include(observations/name,kind)
manifest=dict(schema=1,recorded_utc=now,finalized=True,source_head=prepared['source_head'],
    runtime_manifest_sha256=prepared['runtime_manifest_sha256'],jobs=jobs,
    preopen=dict(positive=str(base/'preopen-001.json'),high_budget=str(base/'preopen-high-001.json'),
        **{k+'_control':str(base/'freshness-controls-001'/k/'preopen-001.json') for k in ('source','settings','export')}),
    faults={k:str(base/'freshness-controls-001'/k/'refusal-001.json') for k in ('source','settings','export')},
    public_additional_files=extra,privacy=privacy,queued_race_forced_in_actual_GUI=False)
facts=dict(schema=1,recorded_utc=now,source_head=prepared['source_head'],
    runtime_manifest_sha256=prepared['runtime_manifest_sha256'],privacy=privacy,
    actual_GUI_ordinary_qualification=True,actual_GUI_full_qualification=False,recovery_GUI_qualified=False,
    observed_roles=list(ids),actual_toolbar_launch=True,actual_toolbar_owner_assisted=False,
    current_runtime_root_observed=True,actual_budget0_refused_before_workspace=True,
    preset90_loaded_and_saved_actual=True,protected_existing_items=4,
    rendered_review_before_after_FCu_BCu_observed=True,accept_without_ack_refused=True,
    accept_with_review_project_open_refused_and_route_retained=True,
    explicit_accept_after_project_close_and_ack_recorded=True,fresh90_export_and_checked_opening=True,
    actual_exported_PCB_render_observed_in_KiCad=True,exported_PCB_and_project_closed_without_editing=True,
    exported_PCB_pads=6,exported_PCB_track_segments=6,exported_PCB_vias=1,exported_PCB_nets=3,exported_PCB_unrouted=0,
    editor_older_format_notice_retained=True,opened_positive_export_became_stale=True,
    opened_positive_export_later_refusal_observed=True,PCB_hash_unchanged_after_editor=True,
    editor_metadata_changes=['PRO','PRL','backup ZIP'],high420_routing_and120_export_validated=True,
    high_export_opened_in_editor=False,three_independent_preopen_freshness_refusals=['source','captured_settings','typed_export_true_to_integer1'],
    each_mutation_after_saved_current_proof=True,original_source_pristine=True,
    explicit_reject_recorded_and_export_disabled=True,actual_cancellation_phase='engine',
    cancellation_requested_signal=engine['cancel_signal'],cancelled_engine_final_exit_code=engine['exit_code'],
    cancelled_engine_cleanup_complete=True,cancelled_CLI_exit_code=process['exit_code'],
    cancelled_result_accepted=False,cancelled_export_created=False,all_phase_cancellation_qualified=False,
    SIGINT_only_termination_claimed=False,permanent_descendant_absence_claimed=False,
    queued_race_forced_in_actual_GUI=False,queued_callback_software_regressions='Full177 software boundary scope; actual forced queue hold unobserved.',
    live_application_or_undo_qualified=False,unsaved_buffer_detection_qualified=False,human_PCB_review=False,
    physical_electrical_validation=False,full_release_qualified=False,
    interaction_correction='An unintended settings picker after a too-early menu action was cancelled; no project/settings were loaded and no extra job created. Ordinary Route selection/labels were then observed settled before cancellation job. No implementation defect or actual forced timing claim inferred.',
    qualification_scope='Seven actual ordinary075 roles only on two functional fixtures. Current034; no inherited earlierGUI qualification or routing breadth/quality/human/electrical claim. Recovery controls remain separate and unfinished.',
    capture_scope='Owned PCB and router pixels were observed inline; raw captures stay Mac-only. Public packet allowlists owned UI text and review body only.',
    accounting='Actual command/Native journals retained. Whole interactive wall/fullCPU including owner/authoring/idle/UI observation is unmeasured, not zero. Preparation/readback/curation/review are additional, no speed claim.')
for name,data in [('final-controls-ordinary-001.json',manifest),('actual-GUI-ordinary-observations-001.json',facts)]:
    with (base/name).open('x') as stream:json.dump(data,stream,indent=2);stream.write('\n')
print(json.dumps(dict(finalized=True,ordinary_roles=list(ids),public_additional=len(extra),engine_exit=engine['exit_code'],CLI_exit=process['exit_code'],recovery_qualified=False)))
