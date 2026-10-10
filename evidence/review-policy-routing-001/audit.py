"""Independent stored-evidence consistency audit; never runs native/router jobs."""
import collections, copy, datetime, hashlib, json, math, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, sexpr as sx
OUT=Path(__file__).resolve().parent
checks=[];failures=[];summaries=[]
def require(ok,name):
    checks.append(name)
    if not ok:failures.append(name)
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def close(a,b,t=1e-6):return abs(a-b)<=t
def git_blob(commit,name):return subprocess.run(['git','-C',str(ROOT),'show',commit+':'+name],check=True,capture_output=True).stdout
def inventory(root):return {str(x.relative_to(root)):sha(x) for x in sorted(root.rglob('*')) if x.is_file()}
frozen='421ba64'
timings=[]
for name in ('policy-smoke-native-001','multichannel-native-001'):
    run=ROOT/'.runs'/name;public=ROOT/'evidence'/name;r=read(run/'result.json')
    source=Path(r['source']);candidate=Path(r['candidate']);original=sx.read(source);tree=sx.read(candidate)
    expected=dict(r['source_hashes']);expected[source.name]=r['candidate_sha256']
    require(candidate==run/'candidate'/source.name,name+'/candidate ownership')
    require(p.tree_hash(source.parent)==r['source_hashes'],name+'/source current immutable')
    require(p.tree_hash(run/'snapshot')==r['source_hashes'],name+'/complete original snapshot')
    require(p.tree_hash(candidate.parent)==expected,name+'/complete candidate project hash')
    require(p.immutable(tree)==p.immutable(original),name+'/immutable semantic geometry')
    protected=[x for x in p.routes(original) if p.locked(x)]
    require(all(x in p.routes(tree) for x in protected),name+'/protected routes')
    require(r['scope']=='whole_board_unlocked_routing' and r['adapter']=='both' and r['engine_profile']=='completion-only' and r['baseline']=='completion_only_probe',name+'/diagnostic scope')
    impl=r['tools']['implementation_sha256']
    require(inventory(run/'code')=={Path(n).name:h for n,h in impl.items()},name+'/retained implementation exact')
    for relative,digest in impl.items():
        require(hashlib.sha256(git_blob(frozen,relative)).hexdigest()==digest,name+'/committed code '+relative)
        require(sha(ROOT/relative)==digest,name+'/current verifier matches frozen '+relative)
    for path,digest in r['tools']['files'].items():require(sha(path)==digest,name+'/actual pinned tool '+Path(path).name)
    for label in ('source-drc','final-drc'):
        binding=read(run/(label+'-binding.json'));raw=p.parse_report(run/(label+'.json'),source.name)
        board=(run/'snapshot'/source.name) if label=='source-drc' else candidate
        wanted=r['source_hashes'] if label=='source-drc' else expected
        require(binding['source']==str(board) and binding['input']==str(run/(label+'-input')/source.name) and binding['saved'] is False,name+'/'+label+' paths')
        require(binding['before']==wanted,name+'/'+label+' before hash')
        require(all(binding['after'].get(k)==h for k,h in wanted.items()) and set(binding['after'])-set(wanted)<={source.with_suffix('.kicad_prl').name},name+'/'+label+' after unchanged')
        require(p.tree_hash(run/(label+'-input'))==binding['after'],name+'/'+label+' retained input hash')
        require(raw==r['source_drc' if label=='source-drc' else 'native'],name+'/'+label+' raw summary equality')
        process=read(run/(label+'-process.json'))
        argv=[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(run/(label+'.json')),binding['input']]
        require(process['argv']==argv and process['cwd']==str(run),name+'/'+label+' exact command')
        require(process['exit_code']==(5 if raw['findings'] else 0),name+'/'+label+' findings exit')
    require(sha(run/'final-drc.json')==r['native_report_sha256'],name+'/final report hash')
    require(p.native_rejection_reasons(r['native'])==r['native_rejection_reasons'],name+'/central policy reasons')
    require(p.native_accepted(r['native']) is r['accepted'],name+'/correct acceptance')
    require(r['whole_project_drc_clean'] is (r['accepted'] and r['native']['warnings']==0),name+'/cleanliness scope')
    require(r['native']['ignored_checks']==r['source_drc']['ignored_checks'],name+'/ignored checks unchanged')
    for step in r['steps']:
        process=read(run/(step['name']+'-process.json'))
        require(all(step.get(k)==v for k,v in process.items()),name+'/process receipt '+step['name'])
        require(step['cleanup_complete'] and not step['log_truncated'] and step['status'] in ('success','nonzero_exit'),name+'/cleanup '+step['name'])
        require(Path(step['log']).stat().st_size==step['log_bytes'],name+'/log bytes '+step['name'])
    require(close(sum(x['cpu_seconds'] for x in r['steps']),r['child_cpu_seconds']),name+'/child CPU')
    require(close(sum(x['monitor_cpu_seconds'] for x in r['steps']),r['monitor_cpu_seconds']),name+'/monitor CPU')
    require(close(r['parent_cpu_seconds']+r['child_cpu_seconds']+r['monitor_cpu_seconds'],r['total_cpu_seconds']),name+'/total CPU')
    require(sum(x['wall_seconds'] for x in r['steps'])<=r['wall_seconds']<=r['budget_seconds'] and r['total_cpu_seconds']<=r['cpu_budget_seconds'],name+'/wall CPU budgets')
    require(r['peak_child_rss_bytes']==max(x['max_rss_bytes'] for x in r['steps']),name+'/RSS max')
    engine=read(run/'engine-process.json');eb=r['engine_budget']
    settings=p.engine_profile_settings('completion-only',eb['remaining_outer_wall_seconds_at_assignment'])
    require([x for x in engine['argv'] if x.startswith('--router.')]==eb['argv']==settings['argv'],name+'/engine actual profile flags')
    require(engine['argv'][:3]==['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)'],name+'/engine network deny')
    require(sha(run/'task.dsn')==r['adapter_transformations']['output_sha256'],name+'/actual adapted DSN hash')
    task=copy.deepcopy(original);task[:]=[x for x in task if not isinstance(x,list) or not x or x[0] not in p.ROUTES or p.locked(x)]
    for z in sx.children(task,'zone'):z[:]=[x for x in z if not isinstance(x,list) or not x or x[0] not in p.DERIVED_ZONE]
    require(hashlib.sha256((sx.dump(task)+'\n').encode()).hexdigest()==r['task_sha256'],name+'/original stripped task hash')
    imported=p.transplant_routes(task,sx.read(run/'imported.kicad_pcb'))
    refill=read(run/'refill-drc-binding.json');prehash=hashlib.sha256((sx.dump(imported)+'\n').encode()).hexdigest()
    require(refill['saved'] is True and refill['before'][source.name]==prehash,name+'/refill exact imported routing input')
    require(p.tree_hash(run/'refill')==refill['after'],name+'/saved refill tree binding')
    require(p.transplant_fill(imported,sx.read(run/'refill'/source.name))==tree,name+'/final exact fill transplant')
    metrics=read(run/'metrics.json');routes=p.routes(tree)
    require(not any(x[0]=='arc' for x in routes),name+'/metric arc scope')
    length=sum(math.dist([float(v) for v in sx.one(x,'start')[1:]],[float(v) for v in sx.one(x,'end')[1:]]) for x in routes if x[0]=='segment')
    require(close(length,metrics['track_length_mm'],1e-5) and metrics['vias']==sum(x[0]=='via' for x in routes) and r['metrics']==metrics,name+'/analytic native metrics')
    try:
        checked=p.check_result(run/'result.json');check_error=None
    except p.Rejected as exc:checked=None;check_error=str(exc)
    require(bool(checked) is r['accepted'],name+'/public result verifier disposition')
    manifest=read(public/'public-files.json')['files'];listed={x['path'] for x in manifest}
    require(len(listed)==len(manifest),name+'/public manifest unique')
    for entry in manifest:
        relative=entry['path'];file=public/relative
        require(file.is_file() and not file.is_symlink() and sha(file)==entry['sha256'] and file.stat().st_size==entry['bytes'],name+'/public manifest '+relative)
        require(file.read_bytes()==(run/relative).read_bytes(),name+'/public exact raw copy '+relative)
    extra=set(inventory(public))-listed
    require(extra<=({'SCOPE.md','public-files.json','check-result.json'} if r['accepted'] else {'SCOPE.md','public-files.json'}),name+'/public only declared extras')
    if (public/'check-result.json').exists():require(read(public/'check-result.json')==checked,name+'/published verifier readback')
    types=lambda native:dict(collections.Counter(f['type']+' / '+f['severity'] for f in native['findings']))
    log=(run/'engine.log').read_text();state='TIMED_OUT' if 'finished with state: TIMED_OUT' in log else 'COMPLETED' if 'finished with state: COMPLETED' in log else 'unknown'
    require(state!='unknown',name+'/engine terminal log state')
    summaries.append({'run':name,'accepted':r['accepted'],'status':r['status'],'source_counts':{k:r['source_drc'][k] for k in ('opens','blocking','warnings','exclusions')},'final_counts':{k:r['native'][k] for k in ('opens','blocking','warnings','exclusions')},'final_finding_types':types(r['native']),'source_finding_types':types(r['source_drc']),'candidate_sha256':r['candidate_sha256'],'native_report_sha256':r['native_report_sha256'],'wall_seconds':r['wall_seconds'],'CPU_seconds':r['total_cpu_seconds'],'engine_wall_seconds':engine['wall_seconds'],'logged_engine_state':state,'assigned_internal_job_seconds':eb['assigned_job_timeout_seconds'],'metrics':metrics,'protected_route_count':len(protected),'public_raw_files':len(manifest),'public_raw_bytes':sum(x['bytes'] for x in manifest),'check_result_error':check_error})
    timings.append((datetime.datetime.fromisoformat(r['started_utc']),r['wall_seconds']))
require((timings[1][0]-timings[0][0]).total_seconds()>timings[0][1],'sequential native runs')
sibling='evidence/multichannel-native-001/candidate/multichannel_mixer-unrouted.kicad_pcb'
old=git_blob('6fe00c4',sibling)
require(hashlib.sha256(old).hexdigest()==summaries[1].get('unrelated_sibling_sha256','149b2dce16e0f59adb78f87068f4137b7dafca0e991a0b21fdd967c873fd5ee9'),'historical public sibling exact licensed original')
require(not (ROOT/sibling).exists(),'unrelated sibling removed from current public subset')
result={'kind':'independent stored evidence audit, not fresh native validation','native_executed':False,'routing_executed':False,'frozen_implementation_commit':frozen,'audit_script_sha256':sha(Path(__file__)),'passed':not failures,'check_count':len(checks),'failures':failures,'checks':checks,'runs':summaries,'limits':['Raw Default-class native DSN before in-place adapter transformation was not retained; its input hash alone is not a reconstructable raw export.', 'Public subsets omit full snapshots/native inputs/code and cannot independently run strict check-result.', 'Partial routing metrics on rejected multichannel are not accepted-board quality; no comparative superiority is established.', 'Earlier licensed sibling copy is preserved in Git history and disclosed, not erased.']}
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'checks':len(checks),'failures':failures,'runs':summaries},indent=2))
sys.exit(1 if failures else 0)
