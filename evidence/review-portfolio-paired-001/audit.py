"""Read-only paired portfolio evidence consistency audit; no native/routing execution."""
from pathlib import Path
import collections, copy, hashlib, importlib, json, math, re, subprocess, sys, types
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / '.runs/portfolio-paired-001'
PUBLIC = ROOT / 'evidence/portfolio-paired-001'
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

protocol=read(RUN/'protocol.json');summary=read(RUN/'paired-summary.json');freeze=protocol['freeze'];head=freeze['tools']['git_head']
require(sha(RUN/'protocol.json')==summary['protocol_sha256'],'paired protocol bound')
require(head=='2f36e2cba1c1fb580226a4a5d840f0290145f173','declared frozen commit')
require(inventory(RUN/'frozen-code')==freeze['files_sha256'],'full paired frozen source inventory')
for name,digest in freeze['files_sha256'].items():
    blob=subprocess.run(['git','-C',str(ROOT),'show',f'{head}:{name}'],capture_output=True,check=True).stdout
    require(hashlib.sha256(blob).hexdigest()==digest,'committed frozen file '+name)
for name,digest in freeze['tools']['files'].items():require(sha(name)==digest,'actual tool '+Path(name).name)
source=Path(protocol['source']);original_hashes=freeze['source_hashes']
require(inventory(source.parent)==original_hashes,'actual original source unchanged')
package=types.ModuleType('paired_frozen');package.__path__=[str(RUN/'frozen-code/autorouter')];sys.modules[package.__name__]=package
p=importlib.import_module('paired_frozen.pipeline');p.c.ROOT=ROOT;p.c.JAR=ROOT/'.tools/freerouting-2.5.0.jar'
strategy=importlib.import_module('paired_frozen.strategy');sx=p.sx;original=sx.read(source)
protected=[route for route in p.routes(original) if p.locked(route)]
rows={row['id']:row for row in summary['results']};records={}
require(protocol['arm_order']==['B2_portfolio','C_feedback'],'predeclared sequential pair')
require(protocol['wall_budget_per_arm_seconds']==protocol['cpu_budget_per_arm_seconds']==120,'equal120wallCPU')
require(summary['status']=='completed' and all(r['accepted'] for r in rows.values()),'pair completed with both accepted')
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
    require(raw['ignored_checks']==read(RUN/'B2_portfolio/01-via_default/source-drc.json')['ignored_checks'],label+' ignored checks equal original native report')
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
portfolio=read(RUN/'B2_portfolio/portfolio-summary.json');bp=read(RUN/'B2_portfolio/protocol.json')
require(bp['freeze']['tools']==freeze['tools'] and bp['freeze']['source_hashes']==original_hashes,'portfolio and pair same source/tools freeze')
require(bp['freeze']['files_sha256']=={k:v for k,v in freeze['files_sha256'].items() if k!='scripts/experiment_paired.py'},'portfolio source freeze is exact parent minus wrapper')
require(inventory(RUN/'B2_portfolio/frozen-code')==bp['freeze']['files_sha256'],'portfolio exact frozen source copy')
require(portfolio['protocol_sha256']==sha(RUN/'B2_portfolio/protocol.json'),'portfolio protocol binding')
require(bp['variants']==['via_default','via_low','via_high'] and bp['fixed_order'],'fixed ordered three variants')
require(bp['wall_budget_seconds']==bp['cpu_budget_seconds']==120 and bp['root_finalization_reserve_seconds']==15,'portfolio global120 and reserve15')
require(portfolio['status']=='completed' and portfolio['comparison_eligible'] and not portfolio['applied'] and not portfolio['physical_electrical_validation'],'eligible diagnostic-only portfolio')
require([r['id'] for r in portfolio['trials']]==bp['variants'] and [r['index'] for r in portfolio['trials']]==[0,1,2],'all predeclared attempts retained')
scoring={'via_default':(50,5),'via_low':(25,3),'via_high':(100,10)}
for variant,(via,plane) in scoring.items():
    require(bp['scoring'][variant]=={'variant':variant,'via_costs':via,'plane_via_costs':plane,'argv':[f'--router.scoring.via_costs={via}',f'--router.scoring.plane_via_costs={plane}']},variant+' exact preset')
labels=['B2_portfolio/'+Path(row['result']).parent.name for row in portfolio['trials']]+['C_feedback','C_feedback/incumbent']
for label in labels:
    directory=RUN/label;r=read(directory/'result.json');records[label]=r
    verify_native(directory,r);verify_steps(directory,r)
    require(inventory(directory/'snapshot')==original_hashes,label+' original snapshot exact')
    require(r['source']==str(source) and r['source_hashes']==original_hashes,label+' source identity')
    require(r['tools']==freeze['tools'],label+' tool/code/commit freeze')
    require(inventory(directory/'code')=={Path(n).name:h for n,h in freeze['tools']['implementation_sha256'].items()},label+' exact retained implementation')
    require(r['scope']=='whole_board_unlocked_routing' and r['adapter']=='both' and r['engine_profile']=='tuned',label+' fixed scope adapter profile')
    require(r['accepted'] and r['status']=='routing_accepted',label+' accepted receipt')
    try:verified=p.check_result(directory/'result.json');ok=True
    except Exception as exc:ok=False;failures.append(label+' frozen check_result exception '+repr(exc))
    require(ok,label+' frozen check_result passed')
    require(r['peak_child_rss_bytes']==max(st['max_rss_bytes'] for st in r['steps']),label+' RSS max arithmetic')
    if label=='C_feedback':continue
    eb=r['engine_budget'];engine=read(directory/'engine-process.json');flags=[x for x in engine['argv'] if x.startswith('--router.')]
    jobcap=min(100,math.floor(eb['remaining_outer_wall_seconds_at_assignment']-40));optcap=min(90,jobcap)
    span=lambda n:f'{n//3600:02}:{n//60%60:02}:{n%60:02}'
    expected=['--router.autorouter.max_passes=100','--router.job_timeout='+span(jobcap),'--router.optimizer.max_threads=1','--router.optimizer.max_passes=50','--router.optimizer.timeout='+span(optcap),'--router.optimizer.improvement_threshold=0.001','--router.optimizer.enable_preflight_guards=false','--router.optimizer.max_consecutive_failures=100','--router.optimizer.max_consecutive_failures_pass1=100']
    variant=r.get('scoring_variant')
    if variant is not None:expected+=bp['scoring'][variant]['argv']
    require(flags==eb['argv']==expected,label+' actual tuned profile/scoring argv')
    require(eb['assigned_job_timeout_seconds']==jobcap and eb['assigned_optimizer_timeout_seconds']==optcap,label+' internal caps arithmetic')
    require(eb['scoring']==({'variant':None,'argv':[]} if variant is None else bp['scoring'][variant]),label+' scoring declaration')
    require(eb['strict_class_targets'] is False,label+' original Default-class scope unchanged')
    require(engine['exit_code']==0 and engine['status']=='success',label+' normal engine completion')
    log=(directory/'engine.log').read_text();thresholds=[float(x) for x in re.findall(r'threshold \(([0-9.]+)%\)',log)]
    require(all(close(x,.1) for x in thresholds),label+' observed optimizer threshold never conflicts')
    match=re.search(r'finished with state: ([A-Z_]+) \(elapsed: ([0-9.]+) seconds',log)
    require(match is not None and match.group(1) in ('COMPLETED','TIMED_OUT'),label+' observed cooperative terminal job state')
    elapsed=float(match.group(2)) if match else None
    engines.append({'run':label,'variant':variant,'assigned_job_seconds':jobcap,'assigned_optimizer_seconds':optcap,'engine_wall_seconds':engine['wall_seconds'],'engine_cpu_seconds':engine['cpu_seconds'],'logged_job_seconds':elapsed,'logged_job_state':match.group(1) if match else None,'stop_threshold_percent':thresholds,'cooperative_job_cap_overshoot_seconds':max(0,elapsed-jobcap) if elapsed is not None else None})
for row in portfolio['trials']:
    label='B2_portfolio/'+Path(row['result']).parent.name;r=records[label];assigned=row['assigned_seconds']
    require(row['eligible'] and row['accepted_in_trial_receipt'] and r['accepted'],label+' actual trial eligible')
    require(sha(row['result'])==row['result_sha256'],label+' indexed receipt hash')
    require(r['scoring_variant']==row['id'] and r['budget_seconds']==r['cpu_budget_seconds']==assigned,label+' assigned variant/budgets')
    require(41<=assigned<=105,label+' allocation permits engine+reserves')
    for name in ['candidate','candidate_sha256','native_report_sha256','native','status']:
        require(row[name]==r[name],label+' indexed '+name)
    require(row['vias']==r['metrics']['vias'] and row['length_mm']==r['metrics']['track_length_mm'],label+' indexed metrics')
    require(r['wall_seconds']<=row['invocation_wall_seconds']<=assigned and r['total_cpu_seconds']<=row['invocation_cpu_seconds']<=assigned,label+' full invocation within assigned ceiling')
    require(row['peak_child_rss_bytes']==max(s['max_rss_bytes'] for s in r['steps']) and row['peak_polled_group_rss_bytes']==max(s['sampled_peak_group_rss_bytes'] for s in r['steps']),label+' indexed RSS exact')
    utc_duration=(datetime.datetime.fromisoformat(row['finished_utc'])-datetime.datetime.fromisoformat(row['started_utc'])).total_seconds()
    require(close(utc_duration,row['invocation_wall_seconds'],.005),label+' UTC elapsed matches invocation')
    spent_before_CPU=105-assigned
    prior_cpu=sum(other['invocation_cpu_seconds'] for other in portfolio['trials'][:row['index']])
    require(spent_before_CPU>=prior_cpu-1e-5,label+' allocation charges previous CPU attempts')
    require(spent_before_CPU<=portfolio['total_cpu_seconds'],label+' allocation consistent with global charge')
frontier=[row['id'] for row in portfolio['trials'] if not any(other['vias']<=row['vias'] and other['length_mm']<=row['length_mm'] and (other['vias']<row['vias'] or other['length_mm']<row['length_mm']) for other in portfolio['trials'])]
chosen=min(portfolio['trials'],key=lambda r:(r['vias'],r['length_mm'],r['index']))
require(portfolio['pareto_frontier']==frontier==['via_low'],'full frontier independently recomputed')
for key in ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm'):
    require(portfolio['selected'][key]==chosen[key],'selected unchanged best trial '+key)
require(sum(x['invocation_wall_seconds'] for x in portfolio['trials'])<=portfolio['wall_seconds']<=120,'global portfolio wall includes all attempts')
require(sum(x['invocation_cpu_seconds'] for x in portfolio['trials'])<=portfolio['total_cpu_seconds']<=120,'global portfolio CPU includes all attempts')
for a,b in zip(portfolio['trials'],portfolio['trials'][1:]):require(datetime.datetime.fromisoformat(a['finished_utc'])<datetime.datetime.fromisoformat(b['started_utc']),'sequential baseline attempts '+a['id'])
require(rows['B2_portfolio']['selected']==portfolio['selected'] and rows['B2_portfolio']['trials']==portfolio['trials'] and rows['B2_portfolio']['pareto_frontier']==portfolio['pareto_frontier'],'paired index exact portfolio selection and attempts')
require(rows['B2_portfolio']['result_sha256']==sha(RUN/'B2_portfolio/portfolio-summary.json'),'paired portfolio summary hash')
# Native inputs identical except emitted path and hash-named keepout identifiers.
adapter=importlib.import_module('paired_frozen.adapter');dsns=[]
for label in [x for x in labels if x!='C_feedback']:
    file=RUN/label/'task.dsn';tree=adapter._parse_dsn(file.read_text())
    require(tree[0]=='pcb' and sx.unquote(tree[1])==str(file),label+' DSN own path');tree[1]='OWN_OUTPUT_PATH'
    names=[]
    for node in sx.children(sx.one(tree,'structure'),'keepout'):
        match=re.fullmatch(r'kicad_autorouter_graphic_[0-9a-f]{12}_([0-9]+)',node[1])
        if match:names.append(node[1]);node[1]='SAME_GRAPHIC_'+match.group(1)
    require(len(names)==len(set(names))==8,label+' generated labels exact eight')
    dsns.append(tree)
require(all(tree==dsns[0] for tree in dsns),'all four engines same adapted routing problem after cosmetic normalization')

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
for arm in ('C_feedback',):
    c=records[arm];inc=records[arm+'/incumbent'];base=Path(inc['candidate']);inc_geometry=geometry(base)
    require(c['incumbent_baseline']=='B2_tuned' and c['engine_profile']=='tuned' and c['adapter']=='both',arm+' exact tuned baseline')
    require(c['incumbent']['receipt']==str(RUN/arm/'incumbent/result.json') and c['incumbent']['accepted'] and inc['accepted'],arm+' accepted own incumbent')
    require(inc['budget_seconds']<=105 and inc['cpu_budget_seconds']<=105,arm+' incumbent leaves declared reserve')
    require(inc['baseline']=='B2_tuned' and c['incumbent_metrics']==inc['metrics'],arm+' incumbent metrics label')
    require(inc_geometry==geometry(Path(records['B2_portfolio/01-via_default']['candidate'])),arm+' actual incumbent geometry equals independent B2 ignoring UUIDs')
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
            require(strategy._improves(trial['metrics'],best_metrics,trial['native'],best_native),label+' accepted exact Pareto quality and warnings policy')
        expected_valid=trial['native']['opens']==trial['native']['blocking']==trial['native']['exclusions']==0
        expected_improvement=expected_valid and strategy._improves(trial['metrics'],best_metrics,trial['native'],best_native)
        require(trial['accepted']==expected_improvement,label+' every accepted/rejected decision recomputed')
        require(trial['status']==('improvement_validated' if expected_improvement else 'quality_rejected' if expected_valid else 'drc_rejected'),label+' exact decision status')
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

# Root comparison and conservative shared overhead arithmetic.
for arm,row in rows.items():
    inv=read(RUN/(arm+'-invocation.json'))
    require(all(row.get(k)==v for k,v in inv.items()),arm+' enclosing invocation receipt unchanged subset')
    require(row['accepted_before_shared_charge'] and row['within_enclosing_budgets'] and row['within_charged_budgets'],arm+' all enclosing gates true')
    for key in ('wall','cpu'):
        raw=row['invocation_'+key+'_seconds'];charged=row['charged_'+key+'_seconds'];shared=summary['shared_overhead_'+key+'_seconds']
        require(shared>=0 and close(charged,raw+shared),arm+' whole shared '+key+' charged')
        require(0<=raw<=charged<=120,arm+' charged '+key+' <=120')
    for suffix in ('begin','end'):
        load=row['host_load_average_1_5_15_minutes_'+suffix]
        require(len(load)==3 and all(math.isfinite(x) and x>=0 for x in load),arm+' recorded host load '+suffix)
    require(close((datetime.datetime.fromisoformat(row['finished_utc'])-datetime.datetime.fromisoformat(row['started_utc'])).total_seconds(),row['invocation_wall_seconds'],.005),arm+' matching enclosing UTC interval')
for key in ('wall','cpu'):
    require(close(summary['batch_'+key+'_seconds'],sum(row['invocation_'+key+'_seconds'] for row in rows.values())+summary['shared_overhead_'+key+'_seconds']),'batch '+key+' = both invocations + shared')
require(datetime.datetime.fromisoformat(rows['B2_portfolio']['finished_utc'])<datetime.datetime.fromisoformat(rows['C_feedback']['started_utc']),'paired outer UTC intervals sequential')
require(rows['B2_portfolio']['invocation_wall_seconds']>=portfolio['wall_seconds'] and rows['B2_portfolio']['invocation_cpu_seconds']>=portfolio['total_cpu_seconds'],'B2 enclosing measurements include portfolio cost')
cr=records['C_feedback'];crow=rows['C_feedback']
require(crow['result_sha256']==sha(RUN/'C_feedback/result.json'),'C root receipt hash')
require(crow['receipt_verified'] and crow['protocol_contract_verified'] and crow['within_equal_budgets'] and not crow['cancelled'],'C exact positive protocol/receipt gates')
require(crow['invocation_wall_seconds']>=cr['wall_seconds'] and crow['invocation_cpu_seconds']>=cr['total_cpu_seconds'],'C enclosing measurements include all pruning cost')
for key in ('wall_seconds','total_cpu_seconds','parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','candidate_sha256','native_report_sha256'):
    require(crow[key]==cr[key],'C indexed '+key)
require(crow['vias']==cr['metrics']['vias'] and crow['length_mm']==cr['metrics']['track_length_mm'],'C final indexed metrics')
require(all(obs['final_delivery_accepted'] is True for obs in crow['observations']),'observations agree with actual positive final acceptance')
require(not any(row.get('paired_publication_budget_rejected') for row in rows.values()) and 'comparison_gate_reason' not in summary,'actual run never used publication rejection path')
delta=crow['length_mm']-chosen['length_mm'];via_delta=crow['vias']-chosen['vias']
require(summary['comparisons']==[{'baseline_variant':'via_low','system':'C_feedback','baseline_selected':True,'length_delta_mm':delta,'via_delta':via_delta,'C_dominates_with_1e_6mm_tolerance':True,'baseline_dominates_with_1e_6mm_tolerance':False}],'actual frontier comparison arithmetic')
require(delta < -1e-6 and via_delta==0,'measured length benefit without via increase')
# Source remains stable at the end of this read-only audit.
require(inventory(source.parent)==original_hashes,'source immutable through audit')
public_status={'present':PUBLIC.is_dir(),'verified':False}
if PUBLIC.is_dir() and (PUBLIC/'subset-sha256.json').is_file():
    manifest=read(PUBLIC/'subset-sha256.json');files=inventory(PUBLIC)
    require(set(files)==set(manifest)|{'subset-sha256.json'},'public exact manifest set')
    scope=(PUBLIC/'PUBLIC-SCOPE.md').read_text()
    require('not standalone check-result/restoration evidence' in scope and 'Complete original/native-input project trees' in scope,'public subset limitations declared')
    for name,digest in manifest.items():
        require(files[name]==digest,'public manifest file hash '+name)
        if name!='PUBLIC-SCOPE.md':require(sha(RUN/name)==digest,'public exact retained bytes '+name)
    public_status.update(verified=True,raw_files=len(manifest)-1,generated_scope_files=1,raw_bytes=sum((PUBLIC/name).stat().st_size for name in manifest if name!='PUBLIC-SCOPE.md'))
report={'schema':1,'passed':not failures,'checks':len(checks),'failures':failures,'frozen_commit':head,'run':str(RUN),'native_bindings_checked':len(native_checks),'native_results':native_checks,'engine_settings_and_durations':engines,'C_trial_summary':C_trials,'feedback':feedback_audit,'public_subset':public_status,'comparison':{'B2_selected':chosen['id'],'B2_length_mm':chosen['length_mm'],'C_length_mm':crow['length_mm'],'length_delta_mm':delta,'length_reduction_percent':-delta/chosen['length_mm']*100,'B2_vias':chosen['vias'],'C_vias':crow['vias'],'B2_charged_wall_seconds':rows['B2_portfolio']['charged_wall_seconds'],'C_charged_wall_seconds':crow['charged_wall_seconds'],'B2_charged_cpu_seconds':rows['B2_portfolio']['charged_cpu_seconds'],'C_charged_cpu_seconds':crow['charged_cpu_seconds'],'wall_delta_seconds':crow['charged_wall_seconds']-rows['B2_portfolio']['charged_wall_seconds'],'cpu_delta_seconds':crow['charged_cpu_seconds']-rows['B2_portfolio']['charged_cpu_seconds']},'limitations':['Read-only consistency audit; no fresh native execution or human PCB/electrical review.','One exposed development family and one sequential pair; no population superiority or statistical/generalization claim.','Third via_high attempt reached its cooperative job timeout at 6.06 seconds against6 assigned seconds, then saved valid SES; outer48.867-second wall/CPU allocation was satisfied. This is a native-valid time-limited attempt, not complete optimizer convergence.','Fixed three-variant portfolio order/allocation is stronger than the previous single preset, but is not exhaustive tuning or proof of the strongest possible baseline.','Track length/vias are proxies. Both accepted candidates retain the inherited J2 library mismatch warning and original ignored checks.','Stored totals are sampled before final write; frozen code checks caps after publication. Values do not claim full continuous process-tree CPU/RSS enforcement.','A later paired-wrapper fix clears stale observation metadata on cancellation or publication cap rejection. Neither branch occurred in this frozen run; original source/evidence remains intact.','Mutable receipts demonstrate internal consistency, not cryptographic authenticity of execution.']}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'failures':failures,'native_bindings':len(native_checks),'trials':C_trials,'comparison':report['comparison'],'public_subset':public_status,'engine_durations':engines},indent=2))
raise SystemExit(0 if not failures else 1)

