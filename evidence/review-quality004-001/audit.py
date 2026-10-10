"""Read-only quality004 evidence consistency audit; no native/routing execution."""
from pathlib import Path
import collections, copy, hashlib, importlib, json, math, re, subprocess, sys, types
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / '.runs/quality-comparison-004'
PUBLIC = ROOT / 'evidence/quality-comparison-004'
OUT = Path(__file__).resolve().parent
checks, failures = [], []

def require(ok, label):
    checks.append(label)
    if not ok:
        failures.append(label)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def read(path):return json.loads(Path(path).read_text())

def inventory(path):
    path=Path(path)
    require(path.is_dir() and not path.is_symlink(),f'real directory: {path.relative_to(ROOT)}')
    result={}
    for f in sorted(path.rglob('*')):
        require(not f.is_symlink(),f'no symlink: {f.relative_to(ROOT)}')
        if f.is_file():result[f.relative_to(path).as_posix()]=sha(f)
    return result

def close(a,b,tol=1e-6):return type(a) in (float,int) and type(b) in (float,int) and math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol

protocol=read(RUN/'protocol.json');summary=read(RUN/'summary.json');freeze=protocol['freeze'];head=freeze['tools']['git_head']
require(sha(RUN/'protocol.json')==summary['protocol_sha256'],'summary protocol hash')
require(inventory(RUN/'frozen-code')==freeze['files_sha256'],'complete frozen source inventory')
for name,digest in freeze['files_sha256'].items():
    blob=subprocess.run(['git','-C',str(ROOT),'show',f'{head}:{name}'],capture_output=True,check=True).stdout
    require(hashlib.sha256(blob).hexdigest()==digest,f'frozen code matches committed blob: {name}')
for name,digest in freeze['tools']['files'].items():require(sha(name)==digest,f'actual pinned tool unchanged: {Path(name).name}')
require(inventory(Path(protocol['source']).parent)==freeze['source_hashes'],'original source project unchanged since freeze')

# Reuse the exact frozen bounded syntax reader/invariant helper for semantic
# comparison and independently check hashes, raw JSON, arithmetic and settings.
package=types.ModuleType('quality004_frozen');package.__path__=[str(RUN/'frozen-code/autorouter')];sys.modules[package.__name__]=package
p=importlib.import_module('quality004_frozen.pipeline');p.c.ROOT=ROOT
sx=p.sx;source=Path(protocol['source']);original=sx.read(source);original_hashes=freeze['source_hashes']
protected=[route for route in p.routes(original) if p.locked(route)]
rows={row['id']:row for row in summary['results']};records={}

# Public pack is an intentionally incomplete exact-byte subset, not a complete
# locally checkable run. Its extra attribution/manifest are not native evidence.
manifest=read(PUBLIC/'subset-manifest.json');public_files=inventory(PUBLIC)
require(set(public_files)==set(manifest['files'])|{'ATTRIBUTION.md','subset-manifest.json'},'public subset exact declared file set')
require(manifest['source']=='.runs/quality-comparison-004' and manifest['complete_run'] is False,'public subset source and incompleteness declared')
public_bytes=sum((PUBLIC/name).stat().st_size for name in manifest['files'])
for name,digest in manifest['files'].items():
    require(public_files[name]==digest and sha(RUN/name)==digest,f'public/local/manifest exact hash: {name}')

engines=[];native_checks=[];metrics_recomputed=[]
def verify_native(directory,record):
    label=directory.relative_to(RUN).as_posix();candidate=directory/'candidate'/source.name
    expected=dict(original_hashes);expected[source.name]=record['candidate_sha256']
    require(inventory(candidate.parent)==expected,label+' candidate immutable project file inventory/hash')
    candidate_tree=sx.read(candidate)
    require(p.immutable(candidate_tree)==p.immutable(original),label+' immutable semantic geometry')
    require(all(route in p.routes(candidate_tree) for route in protected),label+' protected source routes')
    binding=read(directory/'final-drc-binding.json');native_input=directory/'final-drc-input'/source.name
    require(binding['source']==str(candidate) and binding['input']==str(native_input) and binding['saved'] is False,label+' native binding paths/save flag')
    require(binding['before']==expected,label+' native binding before equals exact candidate/project')
    require(all(binding['after'].get(k)==v for k,v in expected.items()),label+' native binding after original files unchanged')
    require(set(binding['after'])-set(expected)<={source.with_suffix('.kicad_prl').name},label+' native-only permitted added preferences file')
    require(inventory(native_input.parent)==binding['after'],label+' retained native input exact hash')
    require(sha(directory/'final-drc.json')==record['native_report_sha256'],label+' raw native report bound')
    raw=read(directory/'final-drc.json');native=p.parse_report(directory/'final-drc.json',source.name)
    require(record['native']==native,label+' parsed raw report equals receipt')
    require(raw['ignored_checks']==read(RUN/'B2/source-drc.json')['ignored_checks'],label+' ignored checks equal original native report')
    process=read(directory/'final-drc-process.json')
    expected_argv=[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(directory/'final-drc.json'),str(native_input)]
    require(process['argv']==expected_argv and process['cwd']==str(directory),label+' actual final DRC command/input')
    require(process['exit_code']==(5 if native['findings'] else 0) and process['cleanup_complete'],label+' final DRC exit/cleanup')
    if (directory/'metrics.json').exists():
        metrics=read(directory/'metrics.json');require(record.get('metrics')==metrics,label+' native metric receipt binding')
        routes=p.routes(candidate_tree);require(not any(route[0]=='arc' for route in routes),label+' no arcs needing separate metric formula')
        length=sum(math.hypot(*(float(sx.one(route,'end')[i])-float(sx.one(route,'start')[i]) for i in (1,2))) for route in routes if route[0]=='segment')
        vias=sum(route[0]=='via' for route in routes)
        require(close(length,metrics['track_length_mm'],1e-4) and vias==metrics['vias'],label+' independently recomputed route geometry metrics')
        require(metrics.get('version')=='10.0.0',label+' metric native version')
        metrics_recomputed.append({'run':label,'native_length_mm':metrics['track_length_mm'],'analytic_segment_length_mm':length,'vias':vias})
    native_checks.append({'run':label,'candidate_sha256':record['candidate_sha256'],'native_report_sha256':record['native_report_sha256'],'opens':native['opens'],'blocking':native['blocking'],'warnings':native['warnings'],'exclusions':native['exclusions']})
    return native

def verify_steps(directory,record):
    label=directory.relative_to(RUN).as_posix()
    for step in record['steps']:
        step_dir=Path(step['cwd']);raw=read(step_dir/(step['name']+'-process.json'))
        require(all(step.get(k)==v for k,v in raw.items()),label+' step equals process: '+step['name']+' '+step_dir.name)
        require(step['cleanup_complete'] and not step['log_truncated'],label+' clean untruncated process: '+step['name']+' '+step_dir.name)
        require(Path(step['log']).stat().st_size==step['log_bytes'],label+' log byte binding: '+step['name']+' '+step_dir.name)
    child=sum(st['cpu_seconds'] for st in record['steps']);monitor=sum(st['monitor_cpu_seconds'] for st in record['steps'])
    if 'total_cpu_seconds' in record:
        require(close(child,record['child_cpu_seconds']) and close(monitor,record['monitor_cpu_seconds']),label+' child and monitor CPU sums')
        require(close(record['parent_cpu_seconds']+child+monitor,record['total_cpu_seconds']),label+' total CPU arithmetic')
        require(sum(st['wall_seconds'] for st in record['steps'])<=record['wall_seconds']+1e-6,label+' sequential child wall contained in total')
        require(record['total_cpu_seconds']<=record['cpu_budget_seconds'] and record['wall_seconds']<=record['budget_seconds'],label+' receipt within both caps')

import datetime
ARM_NAMES=('B0','B1','B2','C_single','C_feedback')
require(protocol['arm_order']==list(ARM_NAMES),'five predeclared arms and order')
require(protocol['feedback_ablation'] is True,'feedback ablation declared before runs')
require(protocol['wall_budget_per_arm_seconds']==120 and protocol['cpu_budget_per_arm_seconds']==120,'equal declared wall and measured CPU ceilings')
require(summary['protocol_complete_and_unchanged'] is True,'protocol completed unchanged flag')
arm_settings={a['id']:a for a in protocol['arms']}
all_arms=list(ARM_NAMES)+['C_single/incumbent','C_feedback/incumbent']
for arm in all_arms:
    directory=RUN/arm;r=read(directory/'result.json');records[arm]=r
    verify_native(directory,r);verify_steps(directory,r)
    require(inventory(directory/'snapshot')==original_hashes,arm+' source snapshot frozen')
    require(r['source']==str(source) and r['source_hashes']==original_hashes,arm+' original source identity')
    require(r['tools']==freeze['tools'],arm+' exact frozen tool/code provenance')
    require(inventory(directory/'code')=={Path(n).name:h for n,h in freeze['tools']['implementation_sha256'].items()},arm+' exact retained worker implementation')
    require(r['scope']=='whole_board_unlocked_routing',arm+' scope')
    if r['accepted']:
        try:p.check_result(directory/'result.json');verified=True
        except Exception as exc:verified=False;failures.append(arm+' frozen check_result: '+repr(exc))
        require(verified,arm+' frozen check_result accepted')
    if arm in rows:
        row=rows[arm];inv=read(RUN/(arm+'-invocation.json'));config=arm_settings[arm]
        require(sha(directory/'result.json')==row['result_sha256'],arm+' summary receipt hash')
        require(row['accepted']==r['accepted'] and row['accepted_in_receipt']==r['accepted'],arm+' final acceptance summary')
        require(row['protocol_contract_verified'] and row['freeze_unchanged'] and row['within_equal_budgets'],arm+' explicit contract/freeze/budget gates')
        require(row['cancelled'] is False,arm+' no cancellation')
        require(r['adapter']==config['adapter'] and r['engine_profile']==config['engine_profile'],arm+' adapter/profile declaration exact')
        if config['operation']=='prune':require(r['proposal_policy']==config['proposal_policy'],arm+' exact proposal policy')
        for key in ('wall_seconds','parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','total_cpu_seconds','peak_child_rss_bytes','candidate_sha256','native_report_sha256'):
            require(row[key]==r[key],arm+' summary '+key)
        require(row['peak_child_rss_bytes']==max(x['max_rss_bytes'] for x in r['steps']),arm+' direct-child RSS max')
        require(row['peak_polled_group_rss_bytes']==max(x['sampled_peak_group_rss_bytes'] for x in r['steps']),arm+' group RSS max')
        require(row['length_mm']==r['metrics']['track_length_mm'] and row['vias']==r['metrics']['vias'],arm+' summary quality')
        require(inv['cpu_seconds']>=r['total_cpu_seconds']-1e-6 and inv['wall_seconds']>=r['wall_seconds']-1e-6,arm+' complete invocation >= inner receipt accounting')
        require(inv['cpu_seconds']<=120 and inv['wall_seconds']<=120,arm+' full invocation within equal caps')
        require(row['invocation_cpu_seconds']==inv['cpu_seconds'] and row['invocation_wall_seconds']==inv['wall_seconds'],arm+' invocation summary equality')
        for suffix in ['begin','end']:
            load=row['host_load_average_1_5_15_minutes_'+suffix]
            require(len(load)==3 and all(math.isfinite(v) and v>=0 for v in load),arm+' host load recorded '+suffix)
        if arm in ('B0','B1','B2'):
            require(len(row['observations'])==int(r['accepted']),arm+' only actual final native observation, no invented curve')
    if arm not in ('C_single','C_feedback'):
        eb=r['engine_budget'];engine=read(directory/'engine-process.json');log=(directory/'engine.log').read_text();flags=[x for x in engine['argv'] if x.startswith('--router.')]
        tuned=arm not in ('B0','B1');profile='tuned' if tuned else 'standard'
        jobcap=min(100 if tuned else 60,math.floor(eb['remaining_outer_wall_seconds_at_assignment']-40));optcap=min(90 if tuned else 30,jobcap)
        fmt=lambda n:f'{n//3600:02d}:{n//60%60:02d}:{n%60:02d}'
        expected=[f'--router.autorouter.max_passes={100 if tuned else 30}',f'--router.job_timeout={fmt(jobcap)}','--router.optimizer.max_threads=1',f'--router.optimizer.max_passes={50 if tuned else 10}',f'--router.optimizer.timeout={fmt(optcap)}']
        if tuned:expected+=['--router.optimizer.improvement_threshold=0.001','--router.optimizer.enable_preflight_guards=false','--router.optimizer.max_consecutive_failures=100','--router.optimizer.max_consecutive_failures_pass1=100']
        require(flags==eb['argv']==expected,arm+' repaired exact profile HH:mm:ss argv')
        require(eb['assigned_job_timeout_seconds']==jobcap and eb['assigned_optimizer_timeout_seconds']==optcap,arm+' profile timeout arithmetic and reserve')
        require(engine['exit_code']==0 and engine['status']=='success',arm+' engine normal completion')
        thresholds=[float(x) for x in re.findall(r'threshold \(([0-9.]+)%\)',log)]
        require(thresholds and all(close(x,.1 if tuned else 2.5) for x in thresholds),arm+' optimizer stop threshold observed')
        opt=float(re.search(r'Optimization stage completed:.*?completed in ([0-9.]+) seconds',log).group(1))
        elapsed=float(re.search(r'finished with state: COMPLETED \(elapsed: ([0-9.]+) seconds',log).group(1))
        require(opt<optcap and elapsed<jobcap and engine['wall_seconds']<jobcap,arm+' observed completion below internal deadlines')
        engines.append({'run':arm,'assigned_job_seconds':jobcap,'assigned_optimizer_seconds':optcap,'engine_wall_seconds':engine['wall_seconds'],'engine_CPU_seconds':engine['cpu_seconds'],'logged_job_seconds':elapsed,'logged_optimizer_seconds':opt,'observed_stop_threshold_percent':thresholds})
# Retained same-JAR settings reflection verifies repaired syntax without rerunning engine.
probe=ROOT/'.runs/optimizer-profile-probe-002';pr=read(probe/'result.json')
require(pr['passed'] and pr['checks']==pr['checks_passed']==201,'retained actual-JAR profile probe passed')
require(sha(probe/'actual-settings.json')==pr['actual_settings_sha256'],'profile probe actual settings hash')
require(pr['input_hashes'][str(ROOT/'.tools/freerouting-2.5.0.jar')]==freeze['tools']['files'][str(ROOT/'.tools/freerouting-2.5.0.jar')],'profile probe same JAR')
require(pr['input_hashes'][str(ROOT/'autorouter/pipeline.py')]==freeze['tools']['implementation_sha256']['autorouter/pipeline.py'],'profile probe same frozen pipeline')

adapter=importlib.import_module('quality004_frozen.adapter');dsns=[];dsn_labels=[]
for arm in ('B2','C_single/incumbent','C_feedback/incumbent'):
    file=RUN/arm/'task.dsn';tree=adapter._parse_dsn(file.read_text());require(tree[0]=='pcb' and sx.unquote(tree[1])==str(file),arm+' DSN own output pathname')
    tree[1]='"OWN_OUTPUT_DSN"';names=[]
    for node in sx.children(sx.one(tree,'structure'),'keepout'):
        match=re.fullmatch(r'kicad_autorouter_graphic_[0-9a-f]{12}_([0-9]+)',node[1])
        if match:names.append(node[1]);node[1]='kicad_autorouter_graphic_IDENTICAL_'+match.group(1)
    require(len(names)==len(set(names))==8,arm+' eight exact generated keepout labels')
    dsns.append(tree);dsn_labels.append(names)
require(dsns[0]==dsns[1]==dsns[2],'B2 and both C incumbent DSN equality after cosmetic path/keepout-label normalization')
def geometry(path):return collections.Counter(sx.dump([n for n in route if not isinstance(n,list) or n[0]!='uuid']) for route in p.routes(sx.read(path)))
def route_key(route):return hashlib.sha256(sx.dump(route).encode()).hexdigest()
def warning_sigs(native):return {json.dumps({'type':x['type'],'items':sorted(i['uuid'] for i in x['items'])},sort_keys=True) for x in native['findings'] if x['severity']=='warning'}
def all_uuid_counts(node):
    counts=collections.Counter()
    def walk(n):
        if not isinstance(n,list):return
        if n and n[0]=='uuid':counts[sx.unquote(n[1])]+=1
        for x in n:walk(x)
    walk(node);return counts
zone_nets={sx.one(z,'net')[1] for z in sx.children(original,'zone') if sx.one(z,'net') and sx.one(z,'net')[1]!='0'}
C_trials={};feedback_audit=[]
for arm in ('C_single','C_feedback'):
    c=records[arm];inc=records[arm+'/incumbent'];base=Path(inc['candidate']);inc_geometry=geometry(base)
    require(c['incumbent_baseline']=='B2_tuned' and c['engine_profile']=='tuned' and c['adapter']=='both',arm+' exact tuned baseline')
    require(c['incumbent']['receipt']==str(RUN/arm/'incumbent/result.json') and c['incumbent']['accepted'] and inc['accepted'],arm+' accepted own incumbent')
    require(inc['budget_seconds']<=105 and inc['cpu_budget_seconds']<=105,arm+' incumbent leaves declared reserve')
    require(inc['baseline']=='B2_tuned' and c['incumbent_metrics']==inc['metrics'],arm+' incumbent metrics label')
    require(inc_geometry==geometry(Path(records['B2']['candidate'])),arm+' actual incumbent geometry equals independent B2 ignoring UUIDs')
    trials=[];prior={};best_metrics=inc['metrics'];best_native=inc['native'];best_hash=sha(base)
    for entry in c['trials']:
        file=Path(entry['receipt']);trial=read(file);directory=file.parent;label=arm+'/'+trial['id']
        require(entry['id']==trial['id'] and entry['status']==trial['status'] and entry['accepted']==trial['accepted'],label+' parent index consistency')
        verify_native(directory,trial);verify_steps(directory,trial)
        require(trial['base_candidate_sha256']==best_hash,label+' proposal based on unchanged validated best')
        oldtree=sx.read(base);newtree=sx.read(directory/'candidate'/source.name);oldroutes={route_key(x):x for x in p.routes(oldtree)};newroutes={route_key(x):x for x in p.routes(newtree)};removed=set(trial['proposal']['route_ids'])
        require(len(oldroutes)==len(p.routes(oldtree)) and len(newroutes)==len(p.routes(newtree)),label+' unique route hashes')
        require(set(oldroutes)-set(newroutes)==removed and not(set(newroutes)-set(oldroutes)),label+' exact declared deletion and no route addition/modification')
        require(all(sx.one(oldroutes[x],'net')[1] in zone_nets and not p.locked(oldroutes[x]) and oldroutes[x] not in protected for x in removed),label+' only eligible original-zone tool-owned routes')
        require(trial['started_elapsed_seconds']<trial['finished_elapsed_seconds']<=c['wall_seconds'] and trial['finished_observed_cpu_seconds']<=c['total_cpu_seconds'],label+' trial elapsed/CPU contained by root')
        if trial['accepted']:
            require(trial['native']['opens']==trial['native']['blocking']==trial['native']['exclusions']==0,label+' accepted full native gate')
            require(warning_sigs(trial['native'])<=warning_sigs(best_native),label+' accepted no new warning identities')
            quality=lambda m:(m['vias'],m['track_length_mm'])
            require(quality(trial['metrics'])<quality(best_metrics),label+' accepted lexicographic quality improvement')
        if trial['proposal']['kind']=='native_warning_cleanup':
            parent=prior[trial['proposal']['parent_trial']];decision_path=Path(parent['path']).parent/'feedback-decision.json';decision=read(decision_path)
            require(arm=='C_feedback' and c['proposal_policy']=='feedback',label+' feedback only in declared arm')
            require(decision['proposed'] and decision['proposal']==trial['proposal'],label+' exact stored feedback decision')
            require(decision['failed_candidate_sha256']==parent['record']['candidate_sha256'] and decision['native_report_sha256']==parent['record']['native_report_sha256'] and decision['base_candidate_sha256']==best_hash,label+' feedback parent/raw report/base hashes')
            require(parent['record']['status']=='quality_rejected' and not parent['record']['accepted'],label+' failed parent retained')
            pn=parent['record']['native'];require(pn['opens']==pn['blocking']==pn['exclusions']==0,label+' feedback parent native legal')
            newwarn=[x for x in pn['findings'] if x['severity']=='warning' and json.dumps({'type':x['type'],'items':sorted(i['uuid'] for i in x['items'])},sort_keys=True) not in warning_sigs(best_native)]
            require(newwarn and all(x['type']=='track_dangling' for x in newwarn),label+' only new dangling-track warning trigger')
            uuids=[i['uuid'] for x in newwarn for i in x['items']]
            ft=sx.read(Path(parent['path']).parent/'candidate'/source.name);uc=all_uuid_counts(ft)
            require(len(uuids)==len(set(uuids)) and all(uc[x]==1 for x in uuids),label+' warning UUIDs unique among all candidate objects')
            lookup={sx.unquote(sx.one(x,'uuid')[1]):x for x in p.routes(ft)}
            require(set(uuids)==set(trial['proposal']['added_route_uuids']) and all(lookup[x][0] in ('segment','arc') and sx.one(lookup[x],'net')[1]==trial['proposal']['net'] for x in uuids),label+' warnings resolve exact same-net remaining route objects')
            expected=set(parent['record']['proposal']['route_ids'])|{route_key(lookup[x]) for x in uuids}
            require(removed==expected,label+' cumulative original deletion plus exact warning routes')
            require(trial['proposal']['feedback_depth']<=2 and trial['proposal']['feedback_added_routes']<=8,label+' bounded feedback depth/size')
            feedback_audit.append({'run':label,'parent':trial['proposal']['parent_trial'],'base_candidate_sha256':best_hash,'parent_candidate_sha256':parent['record']['candidate_sha256'],'trigger_native_report_sha256':parent['record']['native_report_sha256'],'trigger_UUIDs':uuids,'removed_segments':[{'uuid':sx.unquote(sx.one(oldroutes[x],'uuid')[1]),'route':sx.dump(oldroutes[x])} for x in sorted(removed)],'actual_length_saved_mm':best_metrics['track_length_mm']-trial['metrics']['track_length_mm'],'native':trial['native'],'decision_sha256':sha(decision_path)})
        if trial['accepted']:base=directory/'candidate'/source.name;best_hash=trial['candidate_sha256'];best_metrics=trial['metrics'];best_native=trial['native']
        prior[trial['id']]={'record':trial,'path':str(file)};trials.append(trial)
    require(len(trials)<=32 and sum(x['accepted'] for x in trials)==c['improvements'],arm+' trial count and improvements')
    expected_steps=[dict(st,phase='incumbent') for st in inc['steps']]+[st for t in trials for st in t['steps']]
    require(c['steps'][:len(expected_steps)]==expected_steps,arm+' charges own incumbent plus all failed and successful trials exactly once')
    require(all(st['phase']=='finalization' and st['cwd']==str(RUN/arm) for st in c['steps'][len(expected_steps):]),arm+' remaining stages only root finalization')
    require(geometry(Path(c['candidate']))==geometry(base) and c['metrics']==best_metrics,arm+' final output equals best actual validated trial')
    cps=[]
    for name in c['checkpoints']:
        cp=read(RUN/arm/name);require(sha(cp['candidate'])==cp['candidate_sha256'],arm+' checkpoint retained candidate '+name);cps.append(cp)
    require(all(a['elapsed_seconds']<=b['elapsed_seconds'] and a['observed_cpu_seconds']<=b['observed_cpu_seconds'] for a,b in zip(cps,cps[1:])),arm+' checkpoint wall/CPU monotonic')
    require(cps[-1]['candidate_sha256']==c['candidate_sha256'] and cps[-1]['metrics']==c['metrics'],arm+' final checkpoint exact output')
    for obs in rows[arm]['observations']:
        cp=read(RUN/arm/obs['checkpoint']);require(sha(RUN/arm/obs['checkpoint'])==obs['checkpoint_sha256'] and obs['elapsed_seconds']==cp['elapsed_seconds'] and obs['observed_cpu_seconds']==cp['observed_cpu_seconds'] and obs['metrics']==cp['metrics'],arm+' summary observation retained checkpoint')
    C_trials[arm]={'count':len(trials),'outcomes':dict(collections.Counter(x['status'] for x in trials)),'improvements':c['improvements'],'checkpoints':len(cps)}

for comp in summary['comparisons']:
    a=rows[comp['baseline']];b=rows[comp['system']]
    require(comp['comparable_valid_candidates'] and a['accepted'] and b['accepted'],comp['baseline']+'/'+comp['system']+' valid quality comparison')
    for field,key in [('length_delta_mm','length_mm'),('via_delta','vias'),('wall_delta_seconds','invocation_wall_seconds'),('cpu_delta_seconds','invocation_cpu_seconds')]:require(close(comp[field],b[key]-a[key]),comp['baseline']+'/'+comp['system']+' '+field+' arithmetic')
require(close(summary['batch_wall_seconds']-sum(rows[a]['invocation_wall_seconds'] for a in ARM_NAMES),summary['shared_freeze_and_summary_overhead_wall_seconds']),'shared batch wall overhead visible')
require(close(summary['batch_cpu_seconds']-sum(rows[a]['invocation_cpu_seconds'] for a in ARM_NAMES),summary['shared_freeze_and_summary_overhead_cpu_seconds']),'shared batch CPU overhead visible')
# UTC receipt creation follows preflight work; wall spans begin earlier. Never add these
# unlike anchors and infer worker overlap. Record the mismatch explicitly.
utc_nominal_gaps=[]
for a,b in zip(ARM_NAMES,ARM_NAMES[1:]):
    start_a=datetime.datetime.fromisoformat(records[a]['started_utc']);start_b=datetime.datetime.fromisoformat(records[b]['started_utc'])
    require(start_b>start_a,a+'/'+b+' receipt creation timestamps ordered')
    utc_nominal_gaps.append({'previous':a,'next':b,'next_created_minus_previous_created_plus_monotonic_duration_seconds':(start_b-start_a).total_seconds()-records[a]['wall_seconds']})
gs=geometry(Path(records['C_single']['candidate']));gf=geometry(Path(records['C_feedback']['candidate']));extra=gs-gf;added=gf-gs
require(len(feedback_audit)==1,'exactly one feedback followup in stored experiment')
removed_geometry=collections.Counter(sx.dump([n for n in sx.parse(x['route']) if not isinstance(n,list) or n[0]!='uuid']) for x in feedback_audit[0]['removed_segments'])
require(not added and extra==removed_geometry,'final C_single/C_feedback geometry differs only by exact three feedback-removed routes')
require(inventory(RUN/'frozen-code')==freeze['files_sha256'],'frozen code still unchanged at audit end')
require(inventory(Path(protocol['source']).parent)==freeze['source_hashes'],'source project still unchanged at audit end')
require(sha(RUN/'protocol.json')==summary['protocol_sha256'],'protocol still unchanged at audit end')
report={'schema':1,'audit':'read-only stored-evidence consistency and geometry/arithmetic audit, no fresh native run or authenticity guarantee','source_commit':head,'audit_script_sha256':sha(__file__),'protocol_sha256':sha(RUN/'protocol.json'),'summary_sha256':sha(RUN/'summary.json'),'passed':not failures,'checks':len(checks),'failures':failures,'public_subset':{'files_verified':len(manifest['files']),'bytes_verified':public_bytes,'manifest_sha256':sha(PUBLIC/'subset-manifest.json'),'complete_run':False},'engines':engines,'native_bindings':native_checks,'independent_metrics':metrics_recomputed,'C_trials':C_trials,'feedback':feedback_audit,'final_difference_equals_exact_feedback_deletion':not added and extra==removed_geometry,'UTC_anchor_limitation':{'nominal_gaps':utc_nominal_gaps,'explanation':'started_utc is sampled after startup hashing/storage/code-copy; wall_seconds begins before those operations. UTC creation plus wall duration does not identify true completion. The frozen experiment loop is synchronous; this audit cannot prove absence of unrelated concurrent host workers.'},'arm_metrics':[{k:rows[a][k] for k in ['id','accepted','opens','blocking','warnings','exclusions','length_mm','vias','invocation_wall_seconds','invocation_cpu_seconds','peak_child_rss_bytes','peak_polled_group_rss_bytes']} for a in ARM_NAMES],'comparisons':summary['comparisons'],'warnings':records['C_feedback']['native']['findings'],'ignored_checks':records['C_feedback']['native']['ignored_checks'],'limitations':['One exposed development family and single trial/order per arm; no independent-family superiority, repeatability or confirmatory significance.','B2 is one fixed tuned profile, not exhaustive equal-budget portfolio; stronger baseline experiment remains important.','Feedback gives a measured route-length proxy improvement with same vias and inherited warning; total cost remains much higher than B2.','All arms stopped below repaired internal deadlines. Settings syntax/profile probe is verified; this is not a timeout enforcement exercise.','UTC receipt creation and elapsed wall measurements use different start anchors; their sum cannot prove exact no-overlap.','Host desktop/background contention uncontrolled; parent+reaped-child accounting and polling memory bounds do not prove complete orphan resource accounting.','Public subset deliberately omits full snapshots/native-input trees; full local check_result requires original .runs evidence.','Physical/electrical adequacy and schematic parity remain unverified; originally ignored DRC keys remain ignored.']}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'failures':failures,'public_subset':report['public_subset'],'native_receipts':len(native_checks),'C_trials':C_trials,'feedback':feedback_audit,'arm_metrics':report['arm_metrics'],'engines':engines},indent=2))
sys.exit(0 if not failures else 1)
