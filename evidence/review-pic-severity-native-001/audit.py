"""Offline audit of immutable failed severity001; never invokes native tools."""
import copy,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
RUN=ROOT/'.runs/pic-severity-controls-001';SOURCE=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
sys.path.insert(0,str(ROOT))
from autorouter import placement_clearance as io,sexpr as sx,pipeline as p
HELP=RUN/'code/experiments/pic_severity_controls_v1';sys.path.insert(0,str(HELP))
import fixture,checks
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda path:json.loads(path.read_text())
inventory=lambda path:io.inventory(path,max_bytes=20*1024**2,max_files=2048,max_entries=4096)
before=inventory(RUN);original_before=inventory(SOURCE.parent)
s=read(RUN/'summary.json');execution=read(ROOT/'.runs/pic-severity-controls-001-execution.json')
checks_done=[]
def check(label,condition):
    if not condition:raise AssertionError(label)
    checks_done.append(label)
check('honest failed batch, six denominator rows',s['status']=='failed_controls' and s['controls_passed'] is False and len(s['cases'])==6)
check('expected order',tuple(r['case'] for r in s['cases'])==fixture.CASES)
check('original full project preserved',original_before==s['source_hashes'] and len(original_before)==15 and s['original_inputs_unchanged'] is True)
check('all completed material hashes exact',{n:h for n,h in before.items() if n!='summary.json'}==s['completed_evidence'])
head=s['tools']['git_head'];check('execution commit matches',head=='59171d628b087a465d6e365fa31bba7e9ec2a225' and execution['git_head']==head)
tree=subprocess.run(['git','ls-tree','-rz','--full-tree',head],cwd=ROOT,capture_output=True,check=True).stdout
git_files={}
for row in tree.split(b'\0'):
    if row:
        meta,name=row.split(b'\t',1);mode,kind,digest=meta.decode().split();git_files[name.decode()]=(mode,kind,digest)
for rel,digest in s['runtime_sources'].items():
    path=RUN/'code'/rel;raw=path.read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    check('frozen committed runtime '+rel,sha(path)==digest and git_files[rel][1:] == ('blob',blob))
check('frozen implementation manifest exact',all(s['runtime_sources'][k]==v for k,v in s['tools']['implementation_sha256'].items()))
lock=read(RUN/'code/toolchain.lock.json')
check('tool pins match saved lock',all(v['sha256'] in s['tools']['files'].values() for v in lock['tools'].values()))
for path,digest in s['tools']['files'].items():
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    check('current pinned tool bytes '+Path(path).name,h.hexdigest()==digest)
check('wrapper/log exact',sha(ROOT/'.runs/run-pic-severity-controls-001.py')==execution['wrapper_sha256'] and sha(ROOT/'.runs/pic-severity-controls-001-command.log')==execution['log_sha256'])
check('root invocation matches expected',execution['argv']==['python3','-B','experiments/pic_severity_controls_v1/driver.py','--run-native','--output','.runs/pic-severity-controls-001'] and execution['cwd']==str(ROOT))
check('no outer cleanup/cancellation',execution['exit_code']==2 and execution['cleanup_signals']==[])
project=read(SOURCE.with_suffix('.kicad_pro'));original=sx.read(SOURCE)
ignored=['footprint_filters_mismatch','silk_edge_clearance','track_not_centered_on_via','tuning_profile_track_geometries']
check('separate original/effective ignored lists',s['source_explicit_ignored_checks']==[v for v in ignored if v!='track_not_centered_on_via'] and s['original_observed_effective_ignored_checks']==ignored)
rows=[];step_count=0;worker_cpu=0
for row in s['cases']:
    name=row['case'];folder=RUN/name;obs=read(folder/'observation.json')
    pcb,pro,scene=fixture.prepare(original,project,name);delta=fixture.project_delta(project,pro,name)
    check(name+' exact recipe and profile delta',row['scene']==scene and row['project_delta']==delta and (folder/'observe-input'/SOURCE.name).read_bytes()==pcb)
    check(name+' copied project semantic identity',read(folder/'observe-input'/SOURCE.with_suffix('.kicad_pro').name)==pro)
    if not delta:check(name+' copied project byte identity',sha(folder/'observe-input'/SOURCE.with_suffix('.kicad_pro').name)==original_before[SOURCE.with_suffix('.kicad_pro').name])
    check(name+' setup and layer table immutable',sx.one(sx.parse(pcb.decode()),'setup')==sx.one(original,'setup') and sx.one(sx.parse(pcb.decode()),'layers')==sx.one(original,'layers'))
    check(name+' complete original companions preserved',all(row['input_hashes'][k]==v for k,v in original_before.items() if k not in (SOURCE.name,SOURCE.with_suffix('.kicad_pro').name)))
    check(name+' input/census binding',inventory(folder/'observe-input')==row['input_hashes']==obs['input_hashes_before']==obs['input_hashes_after'] and obs['source']==str(folder/'observe-input'/SOURCE.name) and obs['board_sha256']==row['input_hashes'][SOURCE.name] and obs['project_sha256']==row['input_hashes'][SOURCE.with_suffix('.kicad_pro').name])
    for stage,entries in row['stages'].items():
        check(name+' '+stage+' captured artifacts exact',all(sha(folder/k)==v for k,v in entries.items()))
    for step in row['steps']:
        step_count+=1;worker_cpu+=step['cpu_seconds'];stage=step['name'];receipt=read(folder/(stage+'-process.json'))
        check(name+' '+stage+' process receipt',all(step[k]==v for k,v in receipt.items()) and step['cleanup_complete'] is True and not step['log_truncated'] and step['cwd']==str(folder))
        expected=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)']
        if stage=='observe':
            expected += ['/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9',str(ROOT/'experiments/pic_severity_controls_v1/worker.py'),str(folder/'observe-input'/SOURCE.name),str(folder/'observation.json')]
        else:
            expected += ['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(folder/'original-drc.json'),str(folder/'original-drc-input'/SOURCE.name)]
        check(name+' '+stage+' exact nonsaving network-denied argv',step['argv']==expected)
    actual_by_id={t['uuid']:t for t in obs['texts']};expected_by_id={t['uuid']:t for t in scene['texts']}
    diffs=[{'uuid':uid,'expected':expected_by_id[uid],'actual':actual_by_id[uid]} for uid in expected_by_id if actual_by_id[uid]!=expected_by_id[uid]]
    check(name+' sole text-label mismatch or exact board target',len(diffs)==(0 if name=='board_edge_text' else 1) and all(d['expected']['layer']=='Dwgs.User' and d['actual']=={**d['expected'],'layer':'User.Drawings'} for d in diffs))
    try:checks.observe(obs,scene,pro);old_error=None
    except ValueError as exc:old_error=str(exc)
    check(name+' historical checker outcome reproduced',old_error==('native route/text identity differs' if name!='board_edge_text' else None))
    synthetic=copy.deepcopy(obs)
    for text in synthetic['texts']:
        if text['layer']=='User.Drawings':text['layer']='Dwgs.User'
    try:checks.observe(synthetic,scene,pro);after_alias=None
    except ValueError as exc:after_alias=str(exc)
    check(name+' exact secondary identity diagnosis',after_alias==('native effective class/profile differs' if name=='missing_default_profile' else None))
    if name=='missing_default_profile':
        ground=next(n for n in obs['nets'] if n['name']=='GND')
        check('Default inheritance exact observed composite',ground['class']=='POWER,Default' and ground['tuning_profile']=='MissingOwnedProfile' and ground['width_nm']==800000 and ground['clearance_nm']==280000)
    native=None
    if name=='board_edge_text':
        binding=read(folder/'original-drc-binding.json');after=inventory(folder/'original-drc-input')
        check('DRC original byte preservation',binding['saved'] is False and binding['before']==row['input_hashes'] and binding['after']==after and all(after[k]==v for k,v in row['input_hashes'].items()) and set(after)-set(row['input_hashes'])=={'pic_programmer.kicad_prl'})
        check('DRC binding file captured',all(sha(folder/k)==v for k,v in row['binding_evidence'].items()))
        native=p.parse_report(folder/'original-drc.json',SOURCE.name)
        check('only actual raw DRC summary exact',native==row['native'])
        pred=checks.predicate(name,native,read(folder/'original-drc.json'),scene,ignored)
        check('target observed but positive gate correctly fails',pred==row['predicate'] and pred['predicate_met'] is True and row['paired_positive_passed'] is False and row['control_passed'] is False)
    else:check(name+' DRC not reached, no invented counts',not (folder/'original-drc.json').exists() and 'native' not in row and row['control_passed'] is False)
    rows.append({'case':name,'status':row['status'],'stages':list(row['stages']),'historical_error':old_error,'text_mismatch':diffs,'secondary_after_synthetic_alias_only':after_alias,'native_classes':[{k:n[k] for k in ('name','class','tuning_profile','width_nm','clearance_nm')} for n in obs['nets']],'native_counts':None if native is None else {k:native[k] for k in ('opens','blocking','warnings','exclusions')},'control_passed':row['control_passed']})
check('six observes and one DRC',step_count==7)
check('worker CPU sum exact',abs(worker_cpu-s['child_step_cpu_seconds'])<1e-9)
check('stored and external measured budgets',s['within_budget'] is True and 0<s['wall_seconds']<execution['wall_seconds']<90 and 0<s['total_cpu_seconds']<execution['waited_child_cpu_seconds']<90)
check('run evidence within20MiB',sum((RUN/n).stat().st_size for n in before)<20*1024**2)
check('no support claim',all(s[k] is False for k in ('routing_accepted','geometry_qualified','format_support_qualified','production_support_changed','schematic_parity_qualified','default_profile_enforcement_qualified','new_engine_execution','board_saved')))
check('entire raw run and original unchanged through audit',inventory(RUN)==before and inventory(SOURCE.parent)==original_before)
report={'schema':1,'status':'failed_native_run_consistency_verified','audit_passed':True,'native_run_passed':False,'native_executed_by_reviewer':False,'git_head':head,'summary_sha256':sha(RUN/'summary.json'),'execution_sha256':sha(ROOT/'.runs/pic-severity-controls-001-execution.json'),'raw_file_count':len(before),'raw_bytes':sum((RUN/n).stat().st_size for n in before),'original_source_files':len(original_before),'checks':checks_done,'check_count':len(checks_done),'cases':rows,'stored_wall_seconds':s['wall_seconds'],'stored_full_cpu_seconds':s['total_cpu_seconds'],'external_wall_seconds':execution['wall_seconds'],'external_waited_cpu_seconds':execution['waited_child_cpu_seconds'],'diagnostic_note':'Alias-only recheck used a synthetic in-memory observation solely to expose secondary mismatch. Raw observations and failed outcome were not changed or relabelled.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'audit_passed':True,'checks':len(checks_done),'raw_file_count':len(before),'native_run_passed':False,'root_cause':'Dwgs.User vs User.Drawings','secondary':'Default inheritance POWER,Default'},indent=2))
