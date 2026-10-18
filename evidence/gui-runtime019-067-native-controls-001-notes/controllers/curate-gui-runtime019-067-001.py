"""Preserve actual GUI067 evidence with the existing readers/inventory helpers.

No Native, GUI, routing or historical experiment is rerun by this curator.
"""
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-019/runtime'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, review_export as ex, placement_clearance as io
started=time.monotonic();base=runtime/'.runs/gui-session067';resume=base/'resume-001'
launch=f.read_json(base/'launch.json');source=Path(launch['source'])
assert p.tree_hash(source.parent)==launch['source_sha256']
observations=f.read_json(resume/'observations-001.json')
main=base/'jobs'/observations['workspace'];pre=f.read_json(resume/'preopen-001.json')
snapshot=Path(pre['snapshot']);assert p.tree_hash(snapshot)==pre['snapshot_hashes']
with p.validation_readback_session():
    assert p.check_result(main/'route/result.json')['current']is True
try:ex.check_export(main/'export/export.json')
except p.Rejected as exc:stale=str(exc)
else:raise AssertionError('opened export must retain its natural stale refusal')
assert stale=='export inputs/runtime/evidence changed'
assert pre['route']['current']is True and pre['export']['current']is True and len(pre['snapshot_hashes'])==106
jobs={
 'positive':main,
 'cancel':base/'jobs/autorouter-gui-5a6f224fd1394dd7a4f5acf673b14f11',
 'reject':base/'jobs/autorouter-gui-14ef793bea55414e948dbfee5f337dc8',
 'source-control':base/'jobs/autorouter-gui-33dab37a52ed437d92198410814403e3',
 'settings-control':base/'jobs/autorouter-gui-af7d16d75f81483981cbe6b4e25b7894',
 'export-control':base/'jobs/autorouter-gui-73a2146d94f149e9966d1522dead232f',
}
route_rows=[];journals=[]
for label,work in jobs.items():
    data=f.read_json(work/'route/result.json')
    if label=='cancel':
        assert data['status']=='cancelled'and data['accepted']is False
        engine=next(s for s in data['steps']if s['name']=='engine')
        assert engine['status']=='cancelled'and engine['cleanup_complete']is True
    else:
        assert data['accepted']is True and data['invariants_unchanged']is True and p.native_accepted(data['native'])
        assert [data['native'][k]for k in ('opens','blocking','warnings','exclusions')]==[0,0,6,0]
        assert len(data['native']['ignored_checks'])==2
        original=p.sx.read(work/'route/snapshot'/source.name)
        candidate=p.sx.read(Path(data['candidate']))
        assert p.immutable(original)==p.immutable(candidate)
        protected=p.protected_for_record(data,original);assert len(protected)==10
        assert all(item in p.routes(candidate)for item in protected)
    route_rows.append(dict(label=label,result_sha256=p.sha(work/'route/result.json'),status=data['status'],accepted=data['accepted'],candidate_sha256=data.get('candidate_sha256'),native=data.get('native'),metrics=data.get('metrics'),current_scope='Original retained acceptance at completion; intentional control mutations are never reaccepted.' if 'control'in label else 'Own current route reader passed.'if label=='positive'else'Own recorded Native proof; no new current acceptance inferred.'))
    for path in sorted(work.glob('*.command.process.json')):
        proc=f.read_json(path);journals.append(dict(label=label,file=path.name,process=proc))
rejected=f.read_json(jobs['reject']/'choice/choice.json')
assert rejected['choice']=='reject'and rejected['choice_recorded']is True and not(jobs['reject']/'export').exists()
for label in ('source','settings','export'):
    fault=f.read_json(resume/'queued-open-controls'/label/'fault-001.json')
    assert fault['GUI_refusal_observed']is True and fault['queue_hold_qualified']is False
notes=ROOT/'evidence/gui-runtime019-067-native-controls-001-notes';notes.mkdir();rows=[]
def copy(path,relative):
    raw=io.read_bytes(path,4*1024**2);dest=notes/relative;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb')as stream:stream.write(raw)
    rows.append(dict(path=str(dest.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
skip={'code','kicad-cache','kicad-config','kicad-documents','engine-config'}
for label,work in jobs.items():
    for name in io.inventory(work/'route',max_bytes=64*1024**2):
        if set(Path(name).parts)&skip:continue
        copy(work/'route'/name,Path(label)/'route'/name)
    for path in work.glob('*.command.*'):copy(path,Path(label)/'GUI-journals'/path.name)
    for name in ('settings.json','review/review.json','choice/choice.json'):
        path=work/name
        if path.exists():copy(path,Path(label)/name)
for name in io.inventory(snapshot,max_bytes=16*1024**2):copy(snapshot/name,Path('positive/preopen-export')/name)
for name in io.inventory(main/'review',max_bytes=16*1024**2):
    if set(Path(name).parts)&(skip|{'project','plot-work'}):continue
    copy(main/'review'/name,Path('positive/rendered-review')/name)
for name in io.inventory(resume/'queued-open-controls',max_bytes=32*1024**2):
    if 'preopen-export'in Path(name).parts or 'project'in Path(name).parts:
        copy(resume/'queued-open-controls'/name,Path('fault-controls')/name)
    elif Path(name).suffix in ('.json','.log','.kicad_pro'):
        copy(resume/'queued-open-controls'/name,Path('fault-controls')/name)
for name in ('launch.json','routing-settings-saved-GUI067-001.json','route-settings.json'):
    copy(base/name,Path('observations')/name)
for name in ('initial-state.json','observations-001.json','preopen-001.json','process-cleanup-001.json'):
    copy(resume/name,Path('observations')/name)
for name in launch['source_sha256']:copy(source.parent/name,Path('source')/name)
for path in (ROOT/'.runs/gui067-preopen-001.py',ROOT/'.runs/gui067-control-preopen.py',Path(__file__),ROOT/'.runs/gui067-preopen-001-command.log',ROOT/'.runs/gui067-preopen-001-time.log'):
    copy(path,Path('controllers')/path.name)
native_export=f.read_json(snapshot/'export.json')
assert native_export['export_accepted']is True and p.native_accepted(native_export['native'])
assert native_export['candidate_sha256']==p.sha(Path(native_export['candidate']))
assert p.tree_hash(source.parent)==launch['source_sha256']and p.tree_hash(snapshot)==pre['snapshot_hashes']
result=dict(schema=1,kind='actual-runtime019-GUI067-native-controls',project_complete=False,actual_GUI=True,human_review=False,full_release_qualified=False,runtime_manifest_sha256=p.sha(runtime/'runtime-distribution.json'),source_head=launch['source_git_head'],source_unchanged=True,source_hashes=launch['source_sha256'],observations=observations,route_rows=route_rows,positive_export=dict(preopen_current=True,complete_snapshot_files=106,current_after_KiCad_opening=False,current_refusal=stale,native=native_export['native'],metrics=native_export['metrics'],candidate_sha256=native_export['candidate_sha256']),GUI_process_journals=journals,queued_race_forced_in_actual_GUI=False,scope='Actual toolbar/settings/refusal/protected Route/rendered review/accept/reject/engine cancellation/fresh Native export/checked KiCad opening and pre-open stale controls. Exposed owned4Cu family; no routing quality, breadth, speedup, physical or human-review claim.',cost_scope='Actual stage process journals retained. Whole interactive wall/fullCPU including authoring, idle, curation and AI review unmeasured, not zero. Native completion proofs were not rerun by this curator.',curation_wall_seconds=time.monotonic()-started,files=rows)
(ROOT/'evidence/gui-runtime019-067-native-controls-001.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(files=len(rows),bytes=sum(r['bytes']for r in rows),actual_GUI=True,queued_race_forced=False,source_unchanged=True,whole_project_clean=False)))
