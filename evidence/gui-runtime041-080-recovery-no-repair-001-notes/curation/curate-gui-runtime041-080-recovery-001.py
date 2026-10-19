"""Prepare three bounded GUI080 recovery packets; never invoke Native/readers.

Each execution curates exactly one completed role. The caller must provide the
final journal003 SHA; original002 and all immutable041 identities are fixed.
Existing030 retain/tree/cost functions and079 packet mechanics are reused.
"""
from pathlib import Path
import argparse,ast,datetime,hashlib,json,os,re,resource,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
RUNTIME=ROOT/'.runs/runtime-directory-041/runtime'
BASE=RUNTIME/'.runs/gui-session080'
HEAD='f7524d7bbfb4824640c8ca51dc978769b2fab98b'
MANIFEST='3d1f5200848cec85a1d7fd0666dfcf3634f4aaa02caeeec66575f99df9a46399'
PREPARED='a0ee6588cdaf5594c1baaf4564a79b86ff9117484f642eadfe4cc253ca6cd3ff'
JOURNAL002='b35244177a14fcfe96d56607eaa0ea4f24ca727479a1b50504bfe1a72e215a19'
RETENTION='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
TEMPLATES={
 'no-repair':('curate-gui-runtime039-079-recovery-no-repair-001.py','3e2001fb212e5704255576e4b67ba0b950e76ddcb9f7905cdbdbcf764712edc5'),
 'repair':('curate-gui-runtime039-079-recovery-repair-001.py','0f01279ca1a10a5cf64a5600ccc20ebf6a7382052d29291d81b8a65c2dad5b62'),
 'forced-cancel':('curate-gui-runtime039-079-postincumbent-cancel-001.py','b171d399c5ba90e2c5331c8ea86c7152097dbffd700889f1edb099aa831d001c')}
DEPENDENCIES={'gui-runtime041-080-progress-001': '4bb6f6b09c3364a803ab79e2f6ef9212ef955dd626ffccbd9f909d27a22651e3', 'gui-runtime041-080-safety-001': 'f963f1828ead4430a6418421a5682e20b73ed543b3d965bfb1ad20df1b53f208', 'runtime041-native-milestone-001': '6b490ab1b16b6bbb81c0e4c3a3584d0d96b7d21a116a9cd69e2463d47642da34', 'gui-runtime039-079-recovery-no-repair-001': 'aec84defed20515e425fa01b0c950e93ef7ddcb9d03bb4a676d28b312285173a', 'gui-runtime039-079-recovery-repair-001': 'a924dfce4a281cd552ce1de4a5cd3bd2f7847224f2de7a07a852c68ca821681e', 'gui-runtime039-079-postincumbent-cancel-001': '22e303b7770f560f658d2027bb34f37427b6eb3885b518b1cd8cf8071f3d80cf', 'runtime039-native-floor-schema-milestone-001': 'c5c851c9b70156a734c604a83d4b50edbb86d2480b66e828278ffade037a5704', 'runtime039-mixer-default-failure-001': '3711bed9b16ac771f69b4dda6a67258a087b943c99333181322f70fe8370640f', 'runtime033-current-interf-Cthermal-001': 'e249cb319fedd350439bf651b454e65e7bc57558b0307d514dc95a2c7b3e0707'}
WORKSPACES={'no-repair':'autorouter-gui-3772928c5eb14119afa94c9c14446414',
 'forced-cancel':'autorouter-gui-424eb044902f4d65a288ffa2103076ab',
 'repair':'autorouter-gui-a3d39a9d6416437489999834f914a0ee'}
SKIP={'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}
COUNTS=('opens','blocking','warnings','exclusions')


def read(path):return json.loads(io.read_bytes(path,4*1024**2))


def only_role(journal,role,workspace):
    rows=[row for row in journal['observations'] if row.get('role')==role and row.get('workspace')==str(workspace)]
    assert len(rows)==1,(role,'one completed journal role required')
    return rows[0]


def main():
    global notes,refs,files,material,total
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',required=True,choices=tuple(WORKSPACES))
    parser.add_argument('--journal003-sha256',required=True)
    args=parser.parse_args();assert re.fullmatch('[0-9a-f]{64}',args.journal003_sha256)
    start=time.monotonic();cpu0=resource.getrusage(resource.RUSAGE_SELF)
    mode=args.mode;label='postincumbent-cancel' if mode=='forced-cancel' else 'recovery-'+mode
    stem='gui-runtime041-080-'+label+'-001'
    notes=ROOT/'evidence'/(stem+'-notes');output=ROOT/'evidence'/(stem+'.json')
    assert not os.path.lexists(notes) and not os.path.lexists(output),'Fresh packet required; never overwrite'
    journal2_path=ROOT/'.runs/gui080-observations-002.json'
    journal3_path=ROOT/'.runs/gui080-observations-003.json'
    assert p.sha(journal2_path)==JOURNAL002 and p.sha(journal3_path)==args.journal003_sha256
    journal2=read(journal2_path);journal3=read(journal3_path)
    assert journal2['runtime']==journal3['runtime']=='041' and journal2['session']==journal3['session']=='080'
    assert journal3['prior_segment_sha256']==JOURNAL002
    assert p.sha(BASE/'prepared-state.json')==PREPARED
    prepared=read(BASE/'prepared-state.json')
    assert prepared['source_head']==HEAD and prepared['runtime_manifest_sha256']==MANIFEST
    assert p.sha(RUNTIME/'runtime-distribution.json')==MANIFEST
    protocol_path=Path(prepared['recovery_protocol']);assert protocol_path==BASE/'recovery-controls-001/protocol-required-001.json'
    assert p.sha(protocol_path)==prepared['recovery_protocol_sha256']
    protocol=read(protocol_path)
    workspace=BASE/'jobs'/WORKSPACES[mode];control=BASE/'recovery-controls-001'/('repair' if mode=='repair' else 'no-repair')
    declared=protocol['recovery']['repair' if mode=='repair' else 'no-repair']
    parent=read(workspace/'route/result.json');incumbent=read(workspace/'route/incumbent/result.json')
    settings=read(workspace/'settings.json')
    assert parent['strategy']=='native_validated_thermal_bridge'
    assert parent['source']==incumbent['source']==declared['source']
    assert parent['source_hashes']==incumbent['source_hashes']==declared['source_hashes']
    assert io.inventory(Path(parent['source']).parent)==parent['source_hashes']
    assert parent['tools']==incumbent['tools']==prepared['tools']
    assert settings==declared['settings']
    assert settings['seconds']==parent['budget_seconds']==parent['cpu_budget_seconds']==(420 if mode=='repair' else 90)
    assert parent['incumbent']['receipt_sha256']==p.sha(workspace/'route/incumbent/result.json')
    assert p.sha(Path(incumbent['candidate']))==incumbent['candidate_sha256']
    assert p.sha(workspace/'route/incumbent/final-drc.json')==incumbent['native_report_sha256']

    # Exact-content reuse from finite, named, already-public packets only.
    refs={};files=[];material=[];total=0;dependencies=[]
    dep_names=list(DEPENDENCIES)
    for earlier in ('recovery-no-repair','postincumbent-cancel'):
        name='gui-runtime041-080-'+earlier+'-001'
        if name!=stem and (ROOT/'evidence'/(name+'.json')).is_file():dep_names.append(name)
    for name in dep_names:
        path=ROOT/'evidence'/(name+'.json')
        if name in DEPENDENCIES:assert p.sha(path)==DEPENDENCIES[name]
        data=read(path);index=data['files_index'];assert p.sha(ROOT/index['path'])==index['sha256']
        idx=read(ROOT/index['path'])
        for row in idx.get('files',[]):refs.setdefault(row['sha256'],row['path'])
        for row in idx.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
        dependencies.append(dict(path=str(path.relative_to(ROOT)),sha256=p.sha(path),files_index=index))
    helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
    assert p.sha(helper)==RETENTION
    functions=[node for node in ast.parse(helper.read_bytes()).body if isinstance(node,ast.FunctionDef) and node.name in ('retain','tree','cost')]
    assert [node.name for node in functions]==['retain','tree','cost']
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'),globals())
    queue=[];excluded=[];time_inputs=[]
    def add(path,name):
        path=Path(path);assert path.is_file() and not path.is_symlink() and ROOT in path.parents
        queue.append((path,Path(name)))
    def add_tree(path,name,full=False):
        for rel,sha in io.inventory(path,max_bytes=64*1024**2).items():
            if not full and set(Path(rel).parts)&SKIP:
                excluded.append(dict(original=str((path/rel).relative_to(ROOT)),sha256=sha,bytes=(path/rel).stat().st_size,reason='Generated KiCad/engine cache or UI configuration, excluded by existing079 retainer policy.'))
                continue
            add(path/rel,Path(name)/rel)
    def add_time(name):
        path=ROOT/'.runs'/name
        if path.is_file():
            add(path,Path('helpers-logs')/name);time_inputs.append(dict(path=str(path.relative_to(ROOT)),sha256=p.sha(path),complete_external=cost(path)))
    add(journal2_path,'cutoff/observations-002.json');add(journal3_path,'cutoff/observations-003.json')
    add(BASE/'prepared-state.json','preparation/prepared-state.json');add(protocol_path,'preparation/recovery-protocol-required-001.json')
    add(RUNTIME/'runtime-distribution.json','runtime/runtime-distribution.json')
    add_tree(workspace,Path('job'))
    details={};ui=[]
    if mode=='forced-cancel':
        uirow=only_role(journal2,'postincumbent_native_cancel_forced',workspace);ui.append(uirow)
        assert uirow['actual_gui'] is True and uirow['forced_window'] is True
        ready_path=control/'postincumbent-pause-ready-001.json';result_path=control/'postincumbent-pause-result-001.json'
        qualification_path=control/'postincumbent-cancel-qualification-001.json'
        ready=read(ready_path);pause=read(result_path);qualified=read(qualification_path)
        cli=read(workspace/'route.command.process.json');worker=read(workspace/'route/refill-drc-process.json')
        plan_path=ROOT/'.runs/gui080-postincumbent-pause-plan-001.json';plan=read(plan_path)
        assert plan['workspace']==workspace.name and plan['maximum_attempts']==1 and plan['forced_window'] is True
        controller=ROOT/'.runs/gui080-postincumbent-pause-control-001.py'
        assert plan['controller_sha256']==p.sha(controller)==pause['helper_sha256']==ready['helper_sha256']
        assert ready['workspace']==pause['workspace']==qualified['workspace']==str(workspace)
        assert ready['ready'] is True and pause['ready_written'] is True and pause['control_observation_complete'] is True
        assert pause['ready_sha256']==p.sha(ready_path) and pause['known_worker_exit_during_hold'] is True
        assert pause['paused'] is True and pause['GUI_signalled'] is False and pause['CLI_signalled'] is False
        assert pause['forced_window'] is True and pause['natural_timing_claim'] is False
        assert parent['accepted'] is False and parent['status']=='cancelled'
        assert parent['repair'] is None and parent['recovery_needed'] is False
        assert incumbent['accepted'] is True and incumbent['invariants_unchanged'] is True
        assert all(incumbent['native'][key]==0 for key in COUNTS)
        assert pause['incumbent_sha256']==p.sha(workspace/'route/incumbent/result.json')
        assert cli==qualified['gui_cli_process'] and cli['exit_code']==2 and cli['cancel_requested'] is True
        assert worker['pid']==pause['worker']['pid']==ready['worker']['pid']==qualified['worker_pid']==19133
        assert worker['name']=='refill-drc' and worker['status']=='cancelled' and worker['cleanup_complete'] is True
        assert worker['cwd']==str(workspace/'route') and not worker.get('phase')
        own_worker=[step for step in parent['steps'] if step.get('pid')==worker['pid'] and step.get('phase')!='incumbent']
        assert len(own_worker)==1
        assert all(own_worker[0].get(key)==worker.get(key) for key in ('name','argv','cwd','status','exit_code','cleanup_complete'))
        assert not any(step['name']=='final-drc' and step.get('phase')!='incumbent' for step in parent['steps'])
        assert all(step['cleanup_complete'] is True and step['log_truncated'] is False for step in parent['steps'])
        assert not any((workspace/name).exists() for name in ('review','choice','export'))
        assert qualified['production_reader']['current'] is False and qualified['source_unchanged'] is True
        assert qualified['Native_interruption_qualified_in_this_forced_interval'] is True
        assert qualified['natural_timing_claim'] is False and qualified['SIGINT_only_claim'] is False and qualified['all_phase_cancellation_claim'] is False
        for name,sha in qualified['receipt_sha256'].items():assert p.sha(ROOT/name)==sha
        for path in (ready_path,result_path,qualification_path,plan_path,controller):add(path,Path('control')/path.name)
        for name in ('gui080-postincumbent-cancel-reader-001.log','gui080-postincumbent-cancel-reader-001-time.log','gui080-observe-postincumbent-cancel-001.py'):
            add(ROOT/'.runs'/name,Path('helpers-logs')/name)
        add_time('gui080-postincumbent-pause-001-time.log')
        details=dict(forced_window=True,natural_timing_claim=False,actual_worker_interruption_in_this_forced_interval=True,
            worker_pid=worker['pid'],worker_status=worker['status'],worker_exit_code=worker['exit_code'],worker_cleanup_complete=True,
            controller_observation=pause,qualification=qualified,production_reader=qualified['production_reader'],
            parent_final_native_completed=False,incumbent_final_native_completed=True,no_review_choice_export=True,
            known_historical_reporting_defect=dict(raw_parent_schematic_parity=parent.get('schematic_parity'),
                meaning='Old041 parent incorrectly labels intended parity as checked despite interrupted own refill. Incumbent parity completed; parent admission/reader remain false. Raw041 bytes are preserved, never repaired by curation.'),
            SIGINT_only_claim=False,all_phase_cancellation_claim=False,permanent_worker_absence_claim=False)
    else:
        repair=mode=='repair';expected=[0,0,22,0] if repair else [0,0,0,0]
        uirow=only_role(journal3 if repair else journal2,'recovery_repair_delivery' if repair else 'recovery_no_repair_delivery',workspace)
        ui.append(uirow);assert uirow['actual_gui'] is True
        pre_path=control/'preopen-001.json';post_path=control/'postopen-001.json'
        pre=read(pre_path);post=read(post_path);before=control/'preopen-export';after=control/'postopen-snapshot-001'
        exported=read(before/'export.json');review=read(workspace/'review/review.json');choice=read(workspace/'choice/choice.json')
        assert uirow['preopen_receipt_sha256']==p.sha(pre_path) and uirow['postopen_receipt_sha256']==p.sha(post_path)
        assert uirow['source_unchanged'] is True and uirow['candidate_PCB_unchanged'] is True
        assert pre['workspace']==post['workspace']==str(workspace) and pre['role']==post['role']==mode
        assert pre['source']==parent['source'] and pre['source_hashes']==parent['source_hashes']
        assert pre['settings']==settings and pre['settings_sha256']==p.sha(workspace/'settings.json')
        assert pre['route']['current'] is True and pre['export']['current'] is True and pre['source_unchanged'] is True
        assert io.inventory(before)==pre['snapshot_hashes'] and io.inventory(after)==post['snapshot_hashes']
        assert parent['accepted'] is True and parent['invariants_unchanged'] is True
        assert exported['export_accepted'] is True and exported['applied'] is False
        assert exported['original_geometry_and_routing_unchanged'] is True
        assert exported['budget_seconds']==exported['cpu_budget_seconds']==declared['additional_export_seconds']==(120 if repair else 90)
        assert exported['inputs']['receipt_sha256']==p.sha(workspace/'route/result.json')
        assert exported['source_hashes']==parent['source_hashes']
        assert parent['candidate_sha256']==exported['candidate_sha256']==p.sha(Path(parent['candidate']))
        assert choice['choice']=='accept' and choice['applied'] is False and review['status']=='ready_for_manual_review'
        assert review['candidate_sha256']==parent['candidate_sha256']
        for record,folder in ((parent,workspace/'route'),(exported,before/'validation')):
            assert [record['native'][key] for key in COUNTS]==expected
            assert len(record['native']['ignored_checks'])==(7 if repair else 2)
            assert record['schematic_parity']=='checked by final native DRC'
            assert all(step['cleanup_complete'] is True and step['log_truncated'] is False for step in record['steps'])
            own=[step for step in record['steps'] if step['name']=='final-drc' and step.get('phase')!='incumbent']
            assert len(own)==1 and '--schematic-parity' in own[0]['argv']
            assert p.sha(folder/'final-drc.json')==record['native_report_sha256']
        protected=len(incumbent['protected_route_import']['matches'])
        assert protected==pre['protected_original_locked_items']==(0 if repair else 1)
        assert post['source_unchanged'] is True and post['candidate_PCB_unchanged'] is True
        pcb='validation/candidate/'+Path(parent['source']).name
        assert pre['snapshot_hashes'][pcb]==post['snapshot_hashes'][pcb]==parent['candidate_sha256']
        if repair:
            assert parent['recovery_needed'] is True and incumbent['accepted'] is False and incumbent['status']=='drc_rejected'
            assert [incumbent['native'][key] for key in COUNTS]==[0,1,22,0]
            assert parent['repair']['status']=='validated_trial_candidate'
            assert parent['repair']['routing_accepted'] is False and parent['repair']['comparison_eligible'] is False
            selected=[trial for trial in parent['repair']['trials'] if trial.get('validation_passed') is True and trial.get('candidate_sha256')==parent['candidate_sha256']]
            assert len(selected)==1 and p.sha(Path(selected[0]['candidate']))==parent['candidate_sha256']
        else:
            assert parent['recovery_needed'] is False and parent['repair'] is None
            assert incumbent['accepted'] is True and all(incumbent['native'][key]==0 for key in COUNTS)
            assert incumbent['candidate_sha256']==parent['candidate_sha256']
            assert len(pre['snapshot_hashes'])==85 and len(post['snapshot_hashes'])==86
            miss=only_role(journal2,'natural_postincumbent_cancel_interval_missed',workspace)
            assert miss['cancellation_pass'] is False and miss['Native_interruption_proved'] is False
            ui.append(miss)
            add(control/'postincumbent-cancel-observed-001.json','natural-miss/postincumbent-cancel-observed-001.json')
            for name in ('gui080-observe-postincumbent-cancel-001.py','gui080-postincumbent-cancel-observer-001.log'):
                add(ROOT/'.runs'/name,Path('natural-miss')/name)
            add_time('gui080-postincumbent-cancel-observer-001-time.log')
        add_tree(before,Path('before-open/export'),full=True);add_tree(after,Path('after-open/export'),full=True)
        for path in (pre_path,post_path,control/'route-settings.json'):add(path,Path('control')/path.name)
        postproof_path=control/'postopen-current-proof-001.json';postproof=None
        if postproof_path.is_file():
            postproof=read(postproof_path);add(postproof_path,'control/postopen-current-proof-001.json')
            assert postproof['Native_executed'] is False and postproof['postopen_current_proof']['refused'] is True
        for name in ('gui080-recovery-preopen-001.py','gui080-recovery-postopen-001.py'):add(ROOT/'.runs'/name,Path('helpers-logs')/name)
        for stage in ('preopen','postopen'):add_time('gui080-'+mode+'-'+stage+'-001-time.log')
        details=dict(parent_Native_counts=parent['native'],incumbent_Native_counts=incumbent['native'],export_Native_counts=exported['native'],
            parent_candidate_sha256=parent['candidate_sha256'],parent_own_final_Native_completed=True,export_own_final_Native_completed=True,
            whole_method_seconds=settings['seconds'],separate_export_seconds=exported['budget_seconds'],
            protected_original_items=protected,thermal_protection_positive_control=False if repair else None,
            recovery_needed=parent['recovery_needed'],repair=parent['repair'],
            before_open=dict(files=len(pre['snapshot_hashes']),bytes=sum((before/name).stat().st_size for name in pre['snapshot_hashes']),
                receipt_sha256=p.sha(pre_path),current_route_and_export_recorded=True),
            after_open=dict(files=len(post['snapshot_hashes']),bytes=sum((after/name).stat().st_size for name in post['snapshot_hashes']),
                receipt_sha256=p.sha(post_path),changed=post['changed'],source_unchanged=True,candidate_PCB_unchanged=True,
                current_production_reader=postproof,new_Native_validity_inferred=False),
            nested_costs=dict(review=dict(wall_seconds=review['wall_seconds'],CPU_seconds=review['total_cpu_seconds']),
                export=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds'])),
            preopen_receipt_wall_seconds=pre['wall_seconds'],preopen_complete_external_CPU_unknown=not any('preopen' in row['path'] for row in time_inputs))

    samples=[]
    for process_path in sorted(workspace.glob('*.command.process.json')):
        process=read(process_path);log=process_path.with_name(process_path.name.replace('.process.json','.log'))
        assert process['log_truncated'] is False and log.stat().st_size==process['log_bytes']
        if mode!='forced-cancel':assert process['exit_code']==0 and process['cancel_requested'] is False
        samples.append(dict(stage=process_path.name.removesuffix('.command.process.json'),receipt_sha256=p.sha(process_path),log_sha256=p.sha(log),sample=process))
    template_name,template_sha=TEMPLATES[mode];assert p.sha(ROOT/'.runs'/template_name)==template_sha
    add(helper,'curation/retention-helper030.py');add(Path(__file__),'curation/'+Path(__file__).name)
    # Complete byte-preserving raw text only; preflight before creating output.
    known=set(refs);planned_bytes=0;planned_files=0;filtered=[];omissions=[]
    for path,dest in queue:
        raw=io.read_bytes(path,4*1024**2);sha=hashlib.sha256(raw).hexdigest()
        if sha not in known:
            try:assert b'\0' not in raw;raw.decode('utf-8')
            except (AssertionError,UnicodeDecodeError):
                assert path.suffix.lower()=='.zip','Unknown binary is not silently omitted'
                omissions.append(dict(original=str(path.relative_to(ROOT)),bytes=len(raw),sha256=sha,reason='KiCad-generated postopen backupZIP remains Mac-only; exact digest/size retained.'))
                continue
            planned_bytes+=len(raw);planned_files+=1;known.add(sha)
        filtered.append((path,dest))
    assert planned_bytes<16*1024**2-8192 and planned_files<1999,('Packet exceeds unchanged bound; split meaningful packets, do not raise caps',planned_bytes,planned_files)
    notes.mkdir()
    for path,dest in filtered:retain(path,dest)
    scope=('This packet retains one completed actual Runtime041/GUI080 recovery role: '+mode+'. '
        'Immutable source f7524d7b and manifest3d1f5200 are bound to frozen preparation, protocol, job, source inventory and process proofs. '
        'Journal002 is fixed and journal003 is caller-SHA-bound before curation. It does not promote unrelated roles or claim complete GUI qualification.\n\n'
        'No-repair job377 was a natural Cancel timing miss first, not a Cancel pass; its valid accepted result was reused without rerouting for delivery. '
        'The separate job424 forced a finite STOP window on only actual Native19133; actual GUI Cancel then yielded cancelled/cleanup-complete worker, CLI2 and rejected parent/no review, choice or export. '
        'This is not natural timing, SIGINT-only, all-phase cancellation or permanent process absence. Old041 cancelled-parent schematic_parity overclaims a final check; raw bytes remain unchanged and the accepted incumbent is distinguished from the interrupted parent. '
        'Repair joba3d is included only by the separate repair mode after its own final delivery journal and preopen/postopen proof exist; no unexecuted repair stages can be invented.\n\n'
        'Before-open proof bytes are retained separately from editor-modified metadata. PCB/source equality does not establish new Native validity after PRO/PRL/backupZIP changes. '
        'Screenshots remain CUA-transcript-only; no browser AX, unrelated browser data, private inputs, downloaded binaries, apps or venv are published. '
        'Project-owned fixture/code is GPL through repository LICENSE; exposed Interf source and derivatives retain CC-BY-SA4.0 and Larry Ewing/GIMP notices through original/source payloads and exact dependency references. '
        'Zero protected items on the repair source is not a positive protection control.\n\n'
        'No Native, engine, test or production reader is rerun by this curator. CLI, parent, incumbent, repair and Native costs nest and must not be added twice. '
        'Only exact external time logs are complete cost evidence; receipt wall samples are separately named. Whole interactive CPU and unmetered preparation/authoring/review costs are unknown, not zero. '
        'No broad completion, quality, speed, family independence, Windows, restoration, human PCB, electrical/physical or release claim is made. Raw new Mac-only artifacts remain outside old008/010 restores.\n')
    scope_path=notes/'SCOPE.md';scope_path.open('x').write(scope);raw=scope_path.read_bytes();sha=hashlib.sha256(raw).hexdigest();total+=len(raw)
    files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha));material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(raw),sha256=sha))
    assert total<16*1024**2 and len(files)<2000
    index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material,omitted_binary_payloads=omissions,excluded_generated_files=excluded))
    u=resource.getrusage(resource.RUSAGE_SELF)
    summary=dict(schema=1,kind='actual-runtime041-GUI080-'+label+'-bounded-cutoff',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        accepted=False,project_complete=False,actual_GUI=True,actual_GUI_fully_qualified=False,human_PCB_review=False,physical_electrical_validation=False,
        Native_rerun_by_curation=False,production_readers_rerun_by_curation=False,source_head=HEAD,runtime_manifest_sha256=MANIFEST,native_version='10.0.7',workspace=str(workspace),
        cutoffs=[dict(path=str(journal2_path.relative_to(ROOT)),sha256=JOURNAL002),dict(path=str(journal3_path.relative_to(ROOT)),sha256=args.journal003_sha256)],
        actual_UI=ui,source=parent['source'],source_hashes=parent['source_hashes'],source_unchanged_now=True,settings=settings,
        parent=dict(status=parent['status'],accepted=parent['accepted'],receipt_sha256=p.sha(workspace/'route/result.json')),
        incumbent=dict(status=incumbent['status'],accepted=incumbent['accepted'],receipt_sha256=p.sha(workspace/'route/incumbent/result.json')),
        role=details,accounting=dict(CLI_samples=samples,additional_complete_external=time_inputs,
            parent_nested=dict(wall_seconds=parent['wall_seconds'],CPU_seconds=parent['total_cpu_seconds']),
            incumbent_nested=dict(wall_seconds=incumbent['wall_seconds'],CPU_seconds=incumbent['total_cpu_seconds']),
            whole_interactive_wall_seconds=None,whole_interactive_CPU_seconds=None,unmetered_authoring_review_costs_unknown=True,
            meaning='CLI/parent/incumbent/repair/trial/Native nested observations are not additive; complete interactive cost is unknown.'),
        rights='Owned fixture/core GPL; Interf CC-BY-SA4.0 plus Larry Ewing/GIMP attribution for source-derived payload. Exact source/notices retained or content-referenced. No private or downloaded tool payload.',
        limitations='Role-specific functional/cancellation evidence, not full-GUI/human/physical/Windows/restoration or comparative routing-quality qualification.',
        dependencies=dependencies,curator_template=dict(path='.runs/'+template_name,sha256=template_sha),
        retention=dict(helper=str(helper.relative_to(ROOT)),helper_sha256=RETENTION,functions=['retain','tree','cost'],
            max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,new_payload_files=len(files),new_payload_bytes=total,
            material_rows=len(material),omitted_binary_rows=len(omissions),counts_exclude_index_summary=True),
        curation_sample=dict(wall_seconds=time.monotonic()-start,CPU_seconds=u.ru_utime+u.ru_stime-cpu0.ru_utime-cpu0.ru_stime,complete_external_unknown=True),
        files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
    # Readback remains bounded retention/hash verification, never an acceptance reader.
    assert p.sha(journal2_path)==JOURNAL002 and p.sha(journal3_path)==args.journal003_sha256
    assert io.inventory(Path(parent['source']).parent)==parent['source_hashes']
    for row in files:
        raw=io.read_bytes(ROOT/row['path'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    for row in material:
        raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    assert not os.path.lexists(output);p.save_json(output,summary)
    print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),new_files=len(files),new_bytes=total,material_rows=len(material),actual_GUI_fully_qualified=False)))


if __name__=='__main__':main()
