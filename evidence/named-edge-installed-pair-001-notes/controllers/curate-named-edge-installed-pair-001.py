"""Retain exact installed-pair Native proofs and unchanged-design readback."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx
base=ROOT/'.runs/named-edge-installed-pair-001';plan=f.read_json(base/'PROTOCOL.frozen-001.json')
assert p.sha(base/'PROTOCOL.frozen-001.json')=='929553786a1c5f77fcfaecdfecb8ca2c3f64a62f67173f1604e2a556d08aaf5c'
notes=ROOT/'evidence/named-edge-installed-pair-001-notes';notes.mkdir();files=[];arms=[]
def copy(path,relative):
    raw=path.read_bytes();assert not path.is_symlink() and len(raw)<4*1024**2 and b'\0'not in raw;raw.decode()
    relative=Path(*(part if part!='.runs'else'owned-run-evidence'for part in Path(relative).parts))
    target=notes/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    files.append(dict(path=str(target.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
for name,wall,cpu in [('016',28.39,24.61),('017',29.02,25.47)]:
    outer=f.read_json(base/('arm'+name)/'result.json');arm=plan['arms'][name];runtime=Path(arm['runtime'])
    out=runtime/'.runs'/arm['child_output_name'];child=f.read_json(out/'result.json')
    assert outer['passed']is True and child['passed']is True and outer['child']==child
    assert outer['child_receipt_sha256']==p.sha(out/'result.json') and outer['protocol_sha256']==child['protocol_sha256']==p.sha(base/'PROTOCOL.frozen-001.json')
    assert [x['exit_code']for x in child['processes']]==[0]*6 and not outer['process']['cancel_requested'] and not outer['process']['log_truncated']
    source=out/'source'/plan['board_name'];original=sx.read(source)
    assert p.tree_hash(source.parent)==plan['fixture_sha256']==child['source_sha256']
    proof=[]
    for stage in ('route','export'):
        path=Path(child['workspace'])/stage/('result.json'if stage=='route'else'export.json');row=f.read_json(path)
        candidate=Path(row['candidate']);tree=sx.read(candidate)
        assert p.sha(candidate)==row['candidate_sha256'] and p.immutable(tree)==p.immutable(original)
        protected=p.protected_for_record(f.read_json(Path(child['workspace'])/'route/result.json'),original)
        assert len(protected)==1 and all(x in p.routes(tree)for x in protected)
        assert [row['native'][key]for key in('opens','blocking','warnings','exclusions')]==[0,0,6,0]and len(row['native']['ignored_checks'])==2
        assert row['metrics']['track_length_mm']==42.0 and row['metrics']['vias']==0
        proof.append(dict(stage=stage,candidate_sha256=row['candidate_sha256'],native=row['native'],metrics=row['metrics']))
    edge=child['edge_transport'];assert edge['applied']==(name=='017')
    if name=='017':assert edge['requested_clearance_um']=='300'and edge['loaded_named_matrix_qualified']is False
    arms.append(dict(arm=name,passed=True,external_whole_wall_seconds=wall,external_whole_full_cpu_seconds=cpu,
        inner_enclosure_samples={key:outer[key]for key in('inner_sample_wall_seconds','inner_sample_full_cpu_seconds')},
        child_inner_samples={key:child[key]for key in('inner_sample_wall_seconds','inner_sample_full_cpu_seconds')},
        child_receipt_sha256=outer['child_receipt_sha256'],own_final_candidates=proof,protected_routes=1,edge_transport=edge,
        raw_declared_global_clearance_um=child['raw_declared_global_clearance_um'],raw_declared_clearance_caveat=child['raw_declared_clearance_caveat']))
    for label,folder in [('workflow',out),('enclosure',base/('arm'+name))]:
        for path in sorted(folder.rglob('*')):
            if path.is_file()and not(set(path.relative_to(folder).parts)&{'kicad-config','kicad-cache','kicad-documents','engine-config','tmp'}):
                copy(path,Path('arm'+name)/label/path.relative_to(folder))
    for suffix in ('command.log','time.log'):copy(base/('arm'+name+'-'+suffix),Path('arm'+name)/suffix)
for name in('PROTOCOL.frozen-001.json','qualify-installed-arm.py','run-installed-arm.py'):
    copy(base/name,Path('controllers')/name)
copy(ROOT/'.runs/runtime-directory-016/runtime/.runs/gui-session065/gui-access-004.json',Path('GUI-access-004.json'))
r=dict(schema=1,kind='actual-frozen-installed016-017-named-edge-adapter-delivery-pair',accepted=False,passed=True,Native_executed=True,actual_GUI=False,human_review=False,
 protocol_sha256=p.sha(base/'PROTOCOL.frozen-001.json'),installed017_source=plan['arms']['017']['runtime_tools']['git_head'],
 exact_module_changes=['autorouter/pipeline.py'],unchanged_runtime_modules=43,board_tasks=1,exposed_owned_family=True,added_independent_families=0,
 arm_order=['016','017'],per_arm_route_seconds=90,per_arm_external_whole_wall_and_full_cpu_ceiling_seconds=260,
 total_external_whole_wall_seconds=57.41,total_external_whole_full_cpu_seconds=50.08,arms=arms,
 measured_outcome='Routing completion and reported quality tie: both42.0mm/0vias,0opens/0blocking,6warnings/2ignored/0exclusions.017 faithfully transports original0.30mm edge minimum in the qualified known-named scope;016keeps its original unapplied Default-only record.',
 original_source_and_design_unchanged=True,software_acceptance_intent_only=True,whole_project_drc_clean=False,C_over_B2_completion_gain_established=False,
 qualification_limits=['Exactly one already exposed owned2Cu/nozone literal-class task, one attempt per installed arm. No board-specific fix, policy/protocol/engine change or retry between arms.',
 'Both actual shipped six-stage CLI workflows use Request/Workflow/CliJob, including rendered review, test intent and fresh own Native export/current final check. Not actual current GUI or human PCB approval.',
 'Every final Route/export has its own actual Native/refill/fullSCH/field/class/dimension/original/protected proof. Source expected opens remain task incompleteness, not source-design conflicts.',
 'Per-input loaded_named_matrix_qualified remainsFalse because no extra full-manager probe runs inside each job. Prior004full-import and006threshold prerequisites are separately pinned; no repeated JVM/source export/sourceNative.',
 'Installed runtime remains same pinned Mac/apps/cachedJAR/copiedno-pipvenv/fixedpath; no cleanOS/relocation/standalone claim. Regular CLI interpreter bytes/version/coordinator and all selected product/tool fields were frozen before either arm.',
 'Actual whole external command costs include every startup/copy/CLI stage/conversion/engine/validation/render/choice/export/currentreadback/publication/exit. Inner timestamps remain samples. Prior research/tests/authoring/AIreview/curation/build/metadata costs are separately retained, not erased or called zero.',
 'No B0stock/B2tuned/Cstrategy comparison or superiority/completion/cleanup/electrical/physical/speed claim. All original breadth/holdout/platform/restoration/external review/release gates remain.'],files=files)
(ROOT/'evidence/named-edge-installed-pair-001.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(passed=True,files=len(files),bytes=sum(row['bytes']for row in files),Native_reexecuted=False)))
