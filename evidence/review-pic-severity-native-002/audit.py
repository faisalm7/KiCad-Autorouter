"""Offline audit of actual severity002; never invokes native tools."""
import copy,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
RUN=ROOT/'.runs/pic-severity-controls-002';SOURCE=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
sys.path.insert(0,str(ROOT))
from autorouter import placement_clearance as io,sexpr as sx,pipeline as p
HELP=RUN/'code/experiments/pic_severity_controls_v1';sys.path.insert(0,str(HELP))
import fixture,checks
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda path:json.loads(path.read_text())
inventory=lambda path:io.inventory(path,max_bytes=20*1024**2,max_files=2048,max_entries=4096)
before=inventory(RUN);original_before=inventory(SOURCE.parent)
PRIOR=ROOT/'.runs/pic-severity-controls-001';prior_before=inventory(PRIOR)
s=read(RUN/'summary.json');execution=read(ROOT/'.runs/pic-severity-controls-002-execution.json')
checks_done=[]
def check(label,condition):
    if not condition:raise AssertionError(label)
    checks_done.append(label)
check('six completed diagnostic outcomes',s['status']=='controls_passed' and s['controls_passed'] is True and len(s['cases'])==6)
check('expected order',tuple(r['case'] for r in s['cases'])==fixture.CASES)
check('original full project preserved',original_before==s['source_hashes'] and len(original_before)==15 and s['original_inputs_unchanged'] is True)
check('all completed material hashes exact',{n:h for n,h in before.items() if n!='summary.json'}==s['completed_evidence'])
head=s['tools']['git_head'];check('execution commit matches',head=='2a987f2275c071c3788e46dfa17dcfb9bd4c80fb' and execution['git_head']==head)
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
check('wrapper/log exact',sha(ROOT/'.runs/run-pic-severity-controls-002.py')==execution['wrapper_sha256'] and sha(ROOT/'.runs/pic-severity-controls-002-command.log')==execution['log_sha256'])
check('root invocation matches expected',execution['argv']==['python3','-B','experiments/pic_severity_controls_v1/driver.py','--run-native','--output','.runs/pic-severity-controls-002'] and execution['cwd']==str(ROOT))
check('no outer cleanup/cancellation',execution['exit_code']==0 and execution['cleanup_signals']==[])
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
        check(name+' '+stage+' actual exit and status',step['exit_code']==(0 if stage=='observe' else 5) and step['status']==('success' if stage=='observe' else 'nonzero_exit'))
        check(name+' '+stage+' log size and bounded elapsed',step['log_bytes']==(folder/(stage+'.log')).stat().st_size and 0<=step['wall_seconds']<=30)
        check(name+' '+stage+' resource guards retained',step['resource_guards']['max_group_rss_bytes']==2*1024**3 and step['resource_guards']['max_workdir_bytes']==20*1024**2 and step['resource_guards']['os_enforced'] is False)
        expected=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)']
        if stage=='observe':
            expected += ['/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9',str(ROOT/'experiments/pic_severity_controls_v1/worker.py'),str(folder/'observe-input'/SOURCE.name),str(folder/'observation.json')]
        else:
            expected += ['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(folder/'original-drc.json'),str(folder/'original-drc-input'/SOURCE.name)]
        check(name+' '+stage+' exact nonsaving network-denied argv',step['argv']==expected)
    check(name+' all fixture/project bytes identical to failed001',all((folder/'observe-input'/filename).read_bytes()==(PRIOR/name/'observe-input'/filename).read_bytes() for filename in (SOURCE.name,SOURCE.with_suffix('.kicad_pro').name)))
    expected_texts={t['uuid']:{**t,'layer_id':checks.TEXT_LAYERS[t['layer']][0],'layer':checks.TEXT_LAYERS[t['layer']][1]} for t in scene['texts']}
    check(name+' actual native text ID/name witness exact',{t['uuid']:t for t in obs['texts']}==expected_texts and all(type(t['layer_id']) is int for t in obs['texts']))
    observed=checks.observe(obs,scene,pro)
    check(name+' native intent/geometry observation matches record',observed==row['observation'] and row['observation_verified'] is True)
    binding=read(folder/'original-drc-binding.json');after=inventory(folder/'original-drc-input')
    check(name+' DRC original byte preservation',binding['saved'] is False and binding['before']==row['input_hashes'] and binding['after']==after and all(after[k]==v for k,v in row['input_hashes'].items()) and set(after)-set(row['input_hashes'])=={'pic_programmer.kicad_prl'})
    check(name+' DRC original path association',binding['source']==str(folder/'observe-input'/SOURCE.name) and binding['input']==str(folder/'original-drc-input'/SOURCE.name))
    check(name+' DRC binding captured',all(sha(folder/k)==v for k,v in row['binding_evidence'].items()))
    actual_binding={'board_sha256':sha(folder/'original-drc-input'/SOURCE.name),'project_sha256':sha(folder/'original-drc-input'/SOURCE.with_suffix('.kicad_pro').name),'report_sha256':sha(folder/'original-drc.json'),'binding_sha256':sha(folder/'original-drc-binding.json')}
    check(name+' recorded native binding exact',row['native_binding']==actual_binding)
    raw=read(folder/'original-drc.json');native=p.parse_report(folder/'original-drc.json',SOURCE.name)
    check(name+' actual raw DRC summary exact',native==row['native'])
    pred=checks.predicate(name,native,raw,scene,ignored)
    check(name+' expected diagnostic matched positive gate',pred==row['predicate'] and pred['predicate_met'] is True and row['paired_positive_passed'] is True and row['control_passed'] is True and row['status']=='passed')
    ordinary=[v for v in raw['violations'] if v['type']=='missing_courtyard']
    check(name+' four ordinary missing_courtyard warnings',len(ordinary)==4 and all(v['severity']=='warning' for v in ordinary))
    check(name+' no opens/exclusions/parity and original effective ignored set',native['opens']==0 and native['exclusions']==0 and raw['schematic_parity']==[] and sorted(v['key'] for v in raw['ignored_checks'])==ignored)
    if name=='missing_default_profile':
        check('Default omission despite profiles in both loaded nets',all(n['tuning_profile']=='MissingOwnedProfile' and n['has_tuning_profile'] is True for n in obs['nets']) and pred['coverage_probe'] is True and pred['provider_detected'] is False and pred['coverage_outcome']=='finding_omitted_despite_loaded_intent' and native['blocking']==0 and native['warnings']==4)
    elif name=='missing_named_profile':
        check('named missing profile remains warning',native['warnings']==5 and native['blocking']==0 and len(pred['target_findings'])==1 and pred['target_findings'][0]['severity']=='warning')
    elif name!='positive':
        check(name+' exact native target remains error',native['blocking']==1 and native['warnings']==4 and len(pred['target_findings'])==1 and pred['target_findings'][0]['severity']=='error')
    else:check('positive no blocking findings but retains four warnings',native['blocking']==0 and native['warnings']==4)
    rows.append({'case':name,'status':row['status'],'stages':list(row['stages']),'native_text_layers':obs['texts'],'native_classes':[{k:n[k] for k in ('name','class','tuning_profile','width_nm','clearance_nm')} for n in obs['nets']],'native_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'finding_types':[{'type':v['type'],'severity':v['severity']} for v in raw['violations']],'predicate':pred,'control_passed':row['control_passed']})
check('six observes and six DRC stages',step_count==12)
check('worker CPU sum exact',abs(worker_cpu-s['child_step_cpu_seconds'])<1e-9)
check('stored and external measured budgets',s['within_budget'] is True and 0<s['wall_seconds']<execution['wall_seconds']<90 and 0<s['total_cpu_seconds']<execution['waited_child_cpu_seconds']<90)
check('run evidence within20MiB',sum((RUN/n).stat().st_size for n in before)<20*1024**2)
check('no support claim',all(s[k] is False for k in ('routing_accepted','geometry_qualified','format_support_qualified','production_support_changed','schematic_parity_qualified','default_profile_enforcement_qualified','new_engine_execution','board_saved')))
check('both full raw runs and original unchanged through audit',inventory(RUN)==before and inventory(SOURCE.parent)==original_before and inventory(PRIOR)==prior_before)
report={'schema':1,'status':'actual_diagnostic_run_consistency_verified','audit_passed':True,'native_run_passed':True,'native_executed_by_reviewer':False,'git_head':head,'summary_sha256':sha(RUN/'summary.json'),'execution_sha256':sha(ROOT/'.runs/pic-severity-controls-002-execution.json'),'raw_file_count':len(before),'raw_bytes':sum((RUN/n).stat().st_size for n in before),'original_source_files':len(original_before),'checks':checks_done,'check_count':len(checks_done),'cases':rows,'stored_wall_seconds':s['wall_seconds'],'stored_full_cpu_seconds':s['total_cpu_seconds'],'external_wall_seconds':execution['wall_seconds'],'external_waited_cpu_seconds':execution['waited_child_cpu_seconds'],'diagnostic_note':'All numeric layer IDs are actual fresh native002 observations. Six diagnostic predicates passed; Default omission remains unqualified enforcement, actual errors remain errors, and failed001 is unchanged.'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'audit_passed':True,'checks':len(checks_done),'raw_file_count':len(before),'native_diagnostic_passed':True,'exact_ordinary_warning':'missing_courtyard','old_run_unchanged':True},indent=2))
