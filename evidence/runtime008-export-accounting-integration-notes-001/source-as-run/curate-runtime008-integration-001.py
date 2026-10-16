"""Curate completed runtime008 using runtime007's shared-reader pattern.

No Native/JVM/test/GUI execution; no historical harness reads or source edits.
Only this fresh controller and the selected public evidence/notes are owned.
"""
from pathlib import Path
import datetime,json,sys,time
START=time.monotonic()
ROOT=Path(__file__).resolve().parents[1];CASE=ROOT/'.runs/runtime-directory-008';RUNTIME=CASE/'runtime'
PUBLIC=ROOT/'evidence/runtime008-export-accounting-integration-001.json'
NOTES=ROOT/'evidence/runtime008-export-accounting-integration-notes-001'
sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,review_export as ex,provenance as pv,sexpr as sx
from autorouter import placement_clearance as io,pour_rule_area as pour

def read(path):return f.read_json(path)
def require(value,reason):
    if not value:raise p.Rejected(reason)
def pin(path):return dict(path=str(path.relative_to(ROOT)),sha256=p.sha(path),bytes=path.stat().st_size)
def external(name):
    path=ROOT/'.runs'/(name+'-time.log');values={}
    for line in path.read_text().splitlines():
        key,value=line.split();values[key]=float(value)
    require(set(values)=={'real','user','sys'},'unexpected external timing schema')
    return dict(wall_seconds=values['real'],full_CPU_seconds=values['user']+values['sys'],
        user_seconds=values['user'],system_seconds=values['sys'],time_log=pin(path))

def main():
    require(c.ROOT==RUNTIME and Path(sys.prefix).resolve()==RUNTIME/'.venv','runtime008 reader context required')
    require(not PUBLIC.exists() and not NOTES.exists(),'fresh public destinations required')
    setup=read(CASE/'setup.json');workflow=read(RUNTIME/'.runs/qualification-route/result.json')
    improve=read(RUNTIME/'.runs/qualification-improve-2cu/result.json');workspace=Path(workflow['workspace']);iw=Path(improve['workspace'])
    route=read(workspace/'route/result.json');export=read(workspace/'export/export.json')
    ir=read(iw/'route/result.json');ie=read(iw/'export/export.json')
    negative=read(CASE/'native1000/result.json');intrusion=read(ROOT/'.runs/runtime008-pour-intrusion-001/result.json')
    refusal=read(ROOT/'.runs/runtime008-schematic-class-refusal-001/result.json')
    full=read(ROOT/'.runs/full-integration-141/execution.json');doctor=read(ROOT/'.runs/runtime008-doctor-001.json')
    manifest=read(RUNTIME/pv.MANIFEST);tools=p.tool_manifest();head='76d2c666f3fe8f009e46f5421c77e18eaacbf7b2'
    require(setup['source_head']==tools['git_head']==full['git_head']==manifest['build_source']['git_head']==head,'frozen source HEAD differs')
    implementation=tools['implementation_sha256']
    require(len(implementation)==42 and implementation==full['tools']['implementation_sha256'],'42 runtime/full141 pins differ')
    for name,digest in implementation.items():
        require(p.sha(ROOT/name)==p.sha(RUNTIME/name)==manifest['immutable_files_sha256'][name]==digest,
            'runtime/root/full141 module differs: '+name)
    for name,digest in manifest['immutable_files_sha256'].items():require(p.sha(RUNTIME/name)==digest,'immutable runtime artifact changed: '+name)
    require(p.sha(RUNTIME/pv.MANIFEST)==setup['manifest_sha256'] and
        sorted(tools['files'].values())==sorted(full['tools']['files'].values()),'manifest or Native/engine tool pins differ')
    require(workflow['workflow_delivered'] and improve['workflow_delivered'] and
        workflow['actual_GUI'] is False and improve['actual_GUI'] is False and negative['passed'] and
        full['process']['status']=='success' and full['process']['exit_code']==0 and full['process']['cleanup_complete'],
        'required completed stage failed')
    require(workflow['tools']==improve['tools']==negative['tools']==tools and negative['source_head']==head and
        negative['source_hashes']==setup['source_hashes'],'workflow/control runtime or source pins differ')
    require(p.sha(ROOT/'.runs/full-integration-141/command.log')==full['log_sha256'],'full141 log changed')
    source=Path(setup['source']);original=sx.read(source);candidate=sx.read(Path(route['candidate']));protected=p.protected_for_record(route,original)
    require(p.tree_hash(source.parent)==setup['source_hashes'] and p.immutable(original)==p.immutable(candidate) and
        len(protected)==10 and all(p.locked(row) and row in p.routes(candidate) for row in protected),'original/protected source differs')
    require(p.tree_hash(Path(improve['source']).parent)==improve['source_hashes'],'2Cu Improve source changed')
    with p.validation_readback_session():
        current_route=p.check_result(workspace/'route/result.json');current_export=ex.check_export(workspace/'export/export.json')
        current_improve=p.check_result(iw/'route/result.json');current_ie=ex.check_export(iw/'export/export.json')
    require(all(x['current'] is True for x in [current_route,current_export,current_improve,current_ie]),'current CLI final reader refused')
    for data in [route,export,ir,ie]:
        require(data['schematic_parity']=='checked by final native DRC' and p.native_accepted(data['native']) and
            [data['native'][k] for k in ['opens','blocking','warnings','exclusions']]==[0,0,6,0] and
            len(data['native']['ignored_checks'])==2 and data['whole_project_drc_clean'] is False,'fullSCH Native findings differ')
    require(route['candidate_sha256']==export['candidate_sha256'] and ir['candidate_sha256']==ie['candidate_sha256'],
        'each workflow/export candidate lineage differs')
    route_audit=read(workspace/'route/pour-keepout-audit.json');export_audit=read(workspace/'export/validation/pour-keepout-audit.json')
    pour.verify_native_record(route_audit,Path(route['candidate']));pour.verify_native_record(export_audit,Path(export['candidate']))
    bad=negative['negative'];stage=CASE/'native1000/invalid-job';badboard=Path(bad['candidate'])
    replay=f.check_drc_stage(stage,{'steps':bad['steps']},'invalid-final',badboard,
        stage/'invalid-final-input'/source.name,False,bad['before'],schematic_parity=True)
    require(replay==bad['native'] and not p.native_accepted(replay) and replay['blocking']>0 and
        p.sha(stage/'invalid-final.json')==bad['report_sha256'] and p.sha(badboard)==bad['candidate_sha256'],
        'same-rule Native negative differs')
    require(intrusion['status']=='controls_passed' and intrusion['controls_passed'] is True and
        intrusion['tools']==tools and intrusion['source_candidate_sha256']==route['candidate_sha256'],'saved-fill intrusion control differs')
    inf=ROOT/'.runs/runtime008-pour-intrusion-001/job';inbad=inf/'negative'/source.name
    require(p.sha(inbad)==intrusion['negative_candidate_sha256'] and p.sha(inf/'negative-audit.json')==intrusion['negative_audit_sha256'],
        'saved-fill negative material changed')
    f.process_check(inf,intrusion,'negative-audit',[*f.SANDBOX,str(c.PYTHON),str(RUNTIME/'autorouter/native.py'),
        'pour-audit',str(inbad),str(inf/'negative-audit.json')],allowed=(1,))
    try:pour.verify_native_record(intrusion['negative_audit'],inbad)
    except ValueError:pass
    else:raise p.Rejected('invalid saved fill accepted')
    counter=ROOT/'.runs/schematic-class-false-accept-001/source'
    require(refusal['status']=='controls_passed' and refusal['controls_passed'] is True and refusal['native_executed'] is False and
        refusal['JVM_executed'] is False and refusal['native_steps']==[] and refusal['source_unchanged'] is True and
        refusal['source_hashes']==p.tree_hash(counter) and refusal['tools']==tools,'unchanged counterexample refusal differs')
    for name in ['preview','route']:
        item=refusal[name];proc=item['process'];reason=item['CLI_result'].get('reason','')
        require(proc['exit_code']==2 and proc['status']=='nonzero_exit' and proc['cleanup_complete'] is True and
            'schematic class intent not qualified' in reason and 'netclass_flag unsupported' in reason and
            p.sha(ROOT/'.runs/runtime008-schematic-class-refusal-001'/(name+'.log'))==item['log_sha256'],
            'actual installed unsupported CLI record differs')
    unsupported=read(ROOT/'.runs/runtime008-schematic-class-refusal-001/route/result.json')
    require(unsupported['accepted'] is False and unsupported['status']=='unsupported' and unsupported['steps']==[] and
        p.sha(ROOT/'.runs/runtime008-schematic-class-refusal-001/route/result.json')==refusal['route_receipt_sha256'],
        'unsupported route receipt differs')
    require(doctor['ready'] is True and doctor['workspace']==str(RUNTIME),'saved doctor is not ready008')
    for mode,child in [('route',RUNTIME/'.runs/qualification-route/result.json'),('improve-2cu',RUNTIME/'.runs/qualification-improve-2cu/result.json')]:
        enc=read(RUNTIME/'.runs'/('enclosure-'+mode)/'execution.json');proc=enc['process']
        require(enc['workflow_delivered'] is True and enc['actual_GUI'] is False and enc['child_sha256']==p.sha(child) and
            proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True and proc['log_truncated'] is False,
            'completed workflow enclosure differs')
    timings={label:external(name) for label,name in [
        ('runtime_setup','prepare-runtime-directory-008'),('four_copper_CLI_workflow','run-runtime-directory008-workflow-route'),
        ('geometry_and_same_rule_Native_negative','runtime008-geometry-negative'),('saved_fill_intrusion','runtime008-pour-intrusion'),
        ('unchanged_class_counterexample_refusal','runtime008-schematic-class-refusal-001'),
        ('two_copper_Improve_CLI_workflow','run-runtime008-improve-2cu'),('doctor','runtime008-doctor-001'),
        ('full141','full-integration-141-wrapper')]}
    paths=[CASE/'setup.json',RUNTIME/pv.MANIFEST,RUNTIME/'.runs/qualification-route/result.json',RUNTIME/'.runs/enclosure-route/execution.json',
        CASE/'native1000/result.json',RUNTIME/'.runs/qualification-improve-2cu/result.json',RUNTIME/'.runs/enclosure-improve-2cu/execution.json',
        ROOT/'.runs/runtime008-pour-intrusion-001/result.json',ROOT/'.runs/runtime008-schematic-class-refusal-001/result.json',
        ROOT/'.runs/runtime008-doctor-001.json',ROOT/'.runs/full-integration-141/execution.json',
        workspace/'route/result.json',workspace/'export/export.json',iw/'route/result.json',iw/'export/export.json']
    copies={'source-as-run/curate-runtime008-integration-001.py':Path(__file__)}
    for name in ['prepare-runtime-directory-008.py','run-runtime-directory008-workflow.py','runtime008-geometry-negative.py',
                 'runtime008-pour-intrusion.py','runtime008-schematic-class-refusal-001.py','run-runtime008-improve-2cu.py']:
        copies['source-as-run/'+name]=ROOT/'.runs'/name
    for index,path in enumerate(paths):copies['records/'+str(index).zfill(2)+'-'+path.name]=path
    for label,item in timings.items():copies['timing/'+label+'.log']=ROOT/item['time_log']['path']
    record=dict(schema=1,kind='current-runtime008-export-accounting-integration',source_head=head,artifact_id='runtime008',
        accepted=False,workflow_delivered=True,actual_GUI=False,human_review=False,physical_electrical_validation=False,
        runtime=str(RUNTIME),runtime_manifest_sha256=p.sha(RUNTIME/pv.MANIFEST),implementation_sha256=implementation,
        matched_runtime_modules=42,immutable_artifact_files=len(manifest['immutable_files_sha256']),
        current_root_full141_runtime_manifest_pins_match=True,tools=tools,source_hashes=setup['source_hashes'],source_unchanged=True,
        source_drc=route['source_drc'],
        route=dict(candidate_sha256=route['candidate_sha256'],native=route['native'],metrics=route['metrics'],
            current_readback=current_route,pour_audit=route_audit,protected_routes=10),
        export=dict(candidate_sha256=export['candidate_sha256'],native=export['native'],metrics=export['metrics'],
            current_readback=current_export,pour_audit=export_audit),
        geometry=negative['geometry'],same_rule_negative=bad,final_runtime_pour_intrusion=intrusion,
        schematic_class_refusal=refusal,
        unsupported_readback_limit='Unsupported receipt current-result refusal is missing engine journal/provenance, not independent proof that check_result reached the class guard. Actual installed preview and direct route demonstrate guard refusal.',
        intrusion_historical_label_note='Retained source-as-run controller/record scope string says runtime007. Actual runtime/source/tool pins and paths bind this008 run; the copied label is not rewritten.',
        two_copper_Improve=dict(workflow_delivered=True,source=improve['source'],source_hashes=improve['source_hashes'],
            candidate_sha256=ir['candidate_sha256'],native=improve['native'],metrics=improve['metrics'],
            current_readback=current_improve,current_export_readback=current_ie),
        full141=dict(passed=True,methods=1832,unittest_seconds=215.004,source_head=full['git_head'],
            process=full['process'],internal_wall_seconds=full['wall_seconds'],internal_full_CPU_seconds=full['full_cpu_seconds']),
        doctor=dict(ready=True,receipt=pin(ROOT/'.runs/runtime008-doctor-001.json'),lead_reported_exit_code=0,
            lead_reported_reaped_session=84804),
        costs=timings,
        internal_control_samples=dict(setup={k:setup.get(k) for k in ['wall_seconds','full_CPU_seconds']},
            geometry={k:negative.get(k) for k in ['wall_seconds','full_cpu_seconds']},
            intrusion={k:intrusion.get(k) for k in ['wall_seconds','full_CPU_seconds']},
            class_refusal={k:refusal.get(k) for k in ['wall_seconds','full_CPU_seconds']}),
        related_evidence=[pin(ROOT/'evidence/export-cpu-roundoff-source-full141-001.json'),
            pin(ROOT/'evidence/gui-runtime008-059-native-opening-001.json')],
        GUI_scope='This record covers CLI-driven production Request/Workflow/CliJob/preview/Route/review/test-intent/export/current readers. Actual GUI059 is separately linked. Its opened export is stale; these unopened CLI exports remain current.',
        scope='Owned exposed correctness/integration controls under unchanged original rules and sources. False-refusal accounting fix; no routing gain, new independent family or comparative B0/B1/B2/C effectiveness measurement.',
        limits=['Six warnings and two ignored checks retained in every positive final Native report; whole-project cleanliness is false.',
            'No electrical/physical or human PCB validation, Windows/relocation/standalone qualification, four-copper Improve or formal release claim.',
            'Actual006 class false acceptance and GUI058 failure remain historical;008 does not retroactively repair their receipts.',
            'External complete costs are separate from nested internal/process samples and from benchmarks. Authoring/review/interactive costs are not fully measured. Sampled resource guards may overshoot; no OS aggregate quota.',
            'No Native/JVM/test/GUI rerun or product/docs edit during curation. No incidental Finder/browser content, credentials, source boards/schematics or binaries copied.'],
        curation_source=pin(Path(__file__)),notes_directory=str(NOTES.relative_to(ROOT)),
        retained_files={name:dict(original=str(path.relative_to(ROOT)),sha256=p.sha(path),bytes=path.stat().st_size)for name,path in copies.items()},
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    require(p.tree_hash(source.parent)==setup['source_hashes'] and p.tool_manifest()==tools,'late source/runtime drift')
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):
            require(Path(module.__file__).resolve().is_relative_to(RUNTIME),'reader import escaped008: '+name)
    NOTES.mkdir();(NOTES/'source-as-run').mkdir();(NOTES/'records').mkdir();(NOTES/'timing').mkdir()
    for name,path in copies.items():
        with (NOTES/name).open('xb')as handle:handle.write(io.read_bytes(path,2*1024**2))
        require(p.sha(NOTES/name)==p.sha(path),'curated copy differs')
    p.save_json(PUBLIC,record)
    print(json.dumps(dict(workflow_delivered=True,all_four_current_CLI_readers=True,full141_passed=True,
        source_head=head,sha256=p.sha(PUBLIC),curation_wall_seconds=time.monotonic()-START)))

if __name__=='__main__':main()
