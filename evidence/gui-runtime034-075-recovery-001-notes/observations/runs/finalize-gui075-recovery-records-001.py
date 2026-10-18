"""Record lead-observed GUI075 recovery facts, without Native/UI execution."""
from pathlib import Path
import datetime, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'.runs/runtime-directory-034/runtime/.runs/gui-session075'
read=lambda q:json.loads(Path(q).read_bytes())
sha=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest()
prepared=read(base/'prepared-state.json')
ids={'no-repair':'91c142febc9a4804846c18d67f3d116d',
     'repair':'702dbdd14b7d42879a269881e4531d5c',
     'missed_cancel':'33ecf16ec64947419f7eb5aa319e213a'}
jobs={k:str(base/'jobs'/('autorouter-gui-'+v)) for k,v in ids.items()}
ordinary=read(base/'final-controls-ordinary-001.json')
assert {str(p) for p in (base/'jobs').iterdir() if p.is_dir()}==set(jobs.values())|set(ordinary['jobs'].values())
for role,work in jobs.items():
    d=read(Path(work)/'route/result.json')
    assert d['accepted'] is True and d['status']=='routing_accepted'
    assert d['strategy']=='native_validated_thermal_bridge'
    assert d['recovery_needed'] is (role!='no-repair')
    assert read(Path(work)/'settings.json')['seconds']==(90 if role=='no-repair' else 420)
assert not (Path(jobs['missed_cancel'])/'export').exists()
assert not (Path(jobs['missed_cancel'])/'review').exists()
for n in ('001','002'):
    o=read(base/('actual-recovery-process-observation-'+n+'.json'))
    assert o['workspace']==jobs['missed_cancel'] and o['actual_recovery_process_observed'] is False
post=read(base/'recovery-controls-001/repair/postopen-001.json')
assert post['source_unchanged'] is True and post['candidate_PCB_unchanged'] is True
assert {Path(k).suffix for k in post['changed']}=={'.kicad_pro','.kicad_prl','.zip'}
privacy=dict(public_projection=True,raw_browser_screenshots_excluded=True,
    full_browser_AX_excluded=True,raw_capture_filenames_excluded=True,all_PNG_Mac_only=True)
extra=[]
def include(q,kind):
    q=Path(q);assert q.is_file() and q.suffix not in ('.png','.jpg','.jpeg')
    extra.append(dict(path=str(q),sha256=sha(q),kind=kind))
obs=base/'actual-GUI-observations-001'
for q in sorted(obs.iterdir()):
    if q.suffix=='.txt' and 75<=int(q.name[:3])<=106:
        kind=('owned_review_body_ax' if q.name[:3] in ('080','091') else
              'owned_kicad_ax' if q.name[:3] in ('097','098','100','101') else 'owned_router_ax')
        include(q,kind)
for n in ('001','002'):
    include(base/('actual-recovery-process-observation-'+n+'.json'),'owned_observation_receipt')
for name in ('gui075-recovery-preopen-001.py','gui075-recovery-postopen-001.py',
    'gui075-watch-owned-engine-001.py',Path(__file__).name):
    include(ROOT/'.runs'/name,'owned_controller')
for prefix in ('gui075-no-repair-preopen-001','gui075-repair-preopen-001',
    'gui075-repair-postopen-001','gui075-watch-recovery-001','gui075-watch-recovery-002'):
    for suffix in ('-command.log','-time.log'):include(ROOT/'.runs'/(prefix+suffix),'owned_process_log')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
identity=dict(schema=1,recorded_utc=now,source_head=prepared['source_head'],
    runtime_manifest_sha256=prepared['runtime_manifest_sha256'],privacy=privacy)
manifest=dict(identity,finalized=True,jobs=jobs,
    preopen={role:str(base/'recovery-controls-001'/role/'preopen-001.json') for role in ('no-repair','repair')},
    postopen=dict(repair=str(base/'recovery-controls-001/repair/postopen-001.json')),
    public_additional_files=extra)
facts=dict(identity,actual_GUI_recovery_delivery=True,recovery_cancellation_qualified=False,
    full_GUI_qualification=False,known_budget_summary_display_defect=True,observed_roles=list(ids),
    no_repair=dict(actual_recover=True,rendered_FCu_BCu=True,explicit_accept_intent=True,
        fresh_export90=True,opened_in_editor=False,locked_protected_records=1),
    repair=dict(actual_recover=True,rendered_FCu_BCu=True,all22warnings_and7ignored_checks_visible=True,
        explicit_accept_intent=True,fresh_export120=True,checked_open_in_KiCad=True,
        native_editor_rendered=True,pads=379,vias=35,track_segments=1038,nets=173,unrouted=0,
        closed_without_saving_PCB=True,older_format_and_3D_model_notices_retained=True,
        PCB_bytes_unchanged=True,metadata_changes=['PRO','PRL','backup ZIP'],
        later_open_refused_as_stale=True,locked_protected_records=0),
    missed_cancel=dict(actual_route_started=True,observed_incumbent_engine_progress=True,
        owned_repair_phase_observed=False,GUI_cancel_clicked=False,parent_completed_accepted=True,
        review_created=False,export_created=False,
        reason='First finite45second observer began before incumbent completion and missed the repair interval; second began after the interval. Neither observed an eligible worker. This extra attempt and every cost are retained; no cancellation or comparative win is claimed.'),
    display_defect='Review/choice show their own30second operation budget as recovery-method30/export30. Export shows120 as method120. Captured route420/export120 and commands/receipts remain correct. Reproduced and fixed in root source, requiring a new immutable build and fresh GUI qualification.',
    actual_GUI_is_human_review=False,physical_electrical_validation=False,project_complete=False,
    queued_race_forced_in_actual_GUI=False,all_phase_cancellation_qualified=False,
    scope='Actual034 delivery controls on two exposed functional fixtures. Current proofs belong to034 only. Known presentation defect and missed cancellation prevent full034 GUI qualification. Root patch is not retroactive qualification.',
    accounting='All retained command journals and both45second observer costs count. Complete interactive wall/fullCPU, authoring, idle, observations and AI review are unmeasured additional work, not zero; no speed claim.',
    publication='Only owned UI text and exact licensed source/evidence references. Every pixel capture and full browser context stays Mac-only, outside older008/010 backups.')
for name,data in [('final-controls-recovery-001.json',manifest),('actual-GUI-recovery-observations-001.json',facts)]:
    with (base/name).open('x') as stream:json.dump(data,stream,indent=2);stream.write('\n')
print(json.dumps(dict(roles=list(ids),recovery_delivery=True,cancellation_qualified=False,known_display_defect=True,public_additional=len(extra))))
