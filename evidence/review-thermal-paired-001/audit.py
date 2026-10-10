"""Independent stored paired thermal evidence audit; no native/engine execution."""
from pathlib import Path
import collections, copy, datetime, hashlib, importlib, json, math, re, subprocess, sys, types
from decimal import Decimal
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'.runs/thermal-paired-001';OUT=Path(__file__).resolve().parent
HEAD='cbae1254f00d3470d98ba18d24a09e99874f0cc2'
checks=[];failures=[];native_outcomes=[];engine_outcomes=[];metrics_outcomes=[];path_outcomes=[]
def need(ok,label):
    checks.append(label)
    if not ok:failures.append(label)
def read(path):return json.loads(Path(path).read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def tree(path):
    path=Path(path);need(path.is_dir() and not path.is_symlink(),'real directory '+str(path.relative_to(ROOT)))
    result={}
    for f in sorted(path.rglob('*')):
        need(not f.is_symlink(),'not symlink '+str(f.relative_to(ROOT)))
        if f.is_file():result[f.relative_to(path).as_posix()]=sha(f)
    return result
def close(a,b,tol=1e-6):return type(a) in (int,float) and type(b) in (int,float) and math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol
def finite(v):return type(v) in (int,float) and math.isfinite(v) and v>=0
def duration(a,b):return (datetime.datetime.fromisoformat(b)-datetime.datetime.fromisoformat(a)).total_seconds()

protocol=read(RUN/'protocol.json');summary=read(RUN/'paired-summary.json');freeze=protocol['freeze']
initial_inventory=tree(RUN)
need(sha(RUN/'protocol.json')==summary['protocol_sha256'],'pair protocol hash')
need(freeze['tools']['git_head']==HEAD,'frozen expected commit')
need(tree(RUN/'frozen-code')==freeze['files_sha256'],'complete frozen code inventory')
for name,digest in freeze['files_sha256'].items():
    raw=subprocess.run(['git','-C',str(ROOT),'show',HEAD+':'+name],capture_output=True,check=True).stdout
    need(hashlib.sha256(raw).hexdigest()==digest,'committed frozen source '+name)
for name,digest in freeze['tools']['files'].items():need(sha(name)==digest,'pinned tool '+Path(name).name)
source=Path(protocol['source']);hashes=freeze['source_hashes'];need(tree(source.parent)==hashes,'original source full inventory unchanged')
package=types.ModuleType('thermal_audit_frozen');package.__path__=[str(RUN/'frozen-code/autorouter')];sys.modules[package.__name__]=package
p=importlib.import_module(package.__name__+'.pipeline');p.c.ROOT=ROOT;p.c.JAR=ROOT/'.tools/freerouting-2.5.0.jar';sx=p.sx
adapter=importlib.import_module(package.__name__+'.adapter')
original=p.preflight(source);protected=[r for r in p.routes(original) if p.locked(r)]
source_native=p.parse_report(RUN/'B2_portfolio/01-via_default/source-drc.json',source.name)
need(protocol['arm_order']==['B2_portfolio','C_thermal'] and protocol['system_contract']=={'id':'C_thermal','adapter':'both','engine_profile':'completion-only','operation':'recover','strategy':'native_validated_thermal_bridge'},'predeclared independent thermal policy')
need(protocol['wall_budget_per_arm_seconds']==protocol['cpu_budget_per_arm_seconds']==120,'equal total120 wall and CPU budgets')
rows={r['id']:r for r in summary['results']}

def verify_steps(directory,record):
    label=str(directory.relative_to(RUN));steps=record['steps']
    for s in steps:
        d=Path(s['cwd']);need(RUN in d.parents,'process belongs to paired run '+s['name'])
        raw=read(d/(s['name']+'-process.json'))
        need(all(s.get(k)==v for k,v in raw.items()),label+' retained process '+s['name']+' '+d.name)
        need(s.get('cleanup_complete') is True and s.get('log_truncated') is False,label+' clean process '+s['name'])
        need(Path(s['log']).stat().st_size==s['log_bytes'],label+' log bytes '+s['name'])
    if 'total_cpu_seconds' in record:
        child=sum(s['cpu_seconds'] for s in steps);monitor=sum(s['monitor_cpu_seconds'] for s in steps)
        need(close(record['child_cpu_seconds'],child) and close(record['monitor_cpu_seconds'],monitor),label+' exact child/monitor totals')
        need(close(record['total_cpu_seconds'],child+monitor+record['parent_cpu_seconds']+record.get('control_child_cpu_seconds',0)),label+' complete CPU arithmetic')
        need(sum(s['wall_seconds'] for s in steps)<=record['wall_seconds']+1e-6,label+' sequential child wall contained')
        need(record['peak_child_rss_bytes']==max([s['max_rss_bytes'] or 0 for s in steps]+[0]),label+' peak direct child RSS')
        if record.get('accepted'):
            need(record['wall_seconds']<=record['budget_seconds'] and record['total_cpu_seconds']<=record['cpu_budget_seconds'],label+' accepted only within both caps')

def verify_native(directory,record):
    label=str(directory.relative_to(RUN));candidate=Path(record['candidate']) if record.get('candidate') else directory/'candidate'/source.name
    final_hash=record['candidate_sha256'];expected=dict(hashes);expected[source.name]=final_hash
    need(candidate==directory/'candidate'/source.name and tree(candidate.parent)==expected,label+' exact candidate/rules inventory')
    ct=sx.read(candidate);need(p.immutable(ct)==p.immutable(original),label+' original immutable board geometry')
    need(all(r in p.routes(ct) for r in protected),label+' protected source routes')
    binding=read(directory/'final-drc-binding.json');inp=directory/'final-drc-input'/source.name
    need(binding['source']==str(candidate) and binding['input']==str(inp) and binding['saved'] is False,label+' final native input paths')
    need(binding['before']==expected and all(binding['after'].get(k)==v for k,v in expected.items()) and set(binding['after'])-set(expected)<={source.with_suffix('.kicad_prl').name},label+' final exact native board/rules hashes')
    need(tree(inp.parent)==binding['after'],label+' retained native input tree')
    native=p.parse_report(directory/'final-drc.json',source.name)
    need(native['ignored_checks']==source_native['ignored_checks'],label+' ignored native checks exactly original settings')
    refill_native=p.parse_report(directory/'refill-drc.json',source.name)
    need(refill_native['ignored_checks']==source_native['ignored_checks'],label+' refill ignored checks unchanged')
    need(sha(directory/'final-drc.json')==record['native_report_sha256'] and native==record['native'],label+' raw native report bound to receipt')
    process=read(directory/'final-drc-process.json');argv=process['argv']
    if argv[:1]==['/usr/bin/sandbox-exec']:
        need(argv[:3]==['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)'],label+' network-denied validation')
        argv=argv[3:]
    enriched=[s for s in record['steps'] if s['name']=='final-drc' and s['cwd']==str(directory)]
    need(argv==[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(directory/'final-drc.json'),str(inp)] and len(enriched)==1 and enriched[0].get('validated_input_sha256')==final_hash,label+' exact final DRC flags/hash')
    need(process['exit_code']==(5 if native['findings'] else 0),label+' native process violation exit')
    if record.get('accepted') or record.get('validation_passed'):need(p.native_accepted(native),label+' accepted native policy')
    mapping=read(directory/'final-netclasses.json');audit=p.audit_candidate_netclasses(candidate,protected,mapping)
    need(mapping['board_sha256']==final_hash and mapping['project_sha256']==hashes[source.with_suffix('.kicad_pro').name],label+' exact strict class map candidate/project')
    if (directory/'final-netclass-audit.json').exists():
        audit['native_map_file_sha256']=sha(directory/'final-netclasses.json');need(audit==read(directory/'final-netclass-audit.json'),label+' recomputed original class/route dimension audit')
    if record.get('final_map_sha256'):need(record['final_map_sha256']==sha(directory/'final-netclasses.json'),label+' repair class map receipt hash')
    if (directory/'metrics.json').exists():
        metrics=read(directory/'metrics.json');need(record['metrics']==metrics,label+' metrics receipt equals native output')
        rs=p.routes(ct);need(not any(r[0]=='arc' for r in rs),label+' no unsupported analytic arcs')
        length=sum(math.dist(list(map(float,sx.one(r,'start')[1:3])),list(map(float,sx.one(r,'end')[1:3]))) for r in rs if r[0]=='segment');vias=sum(r[0]=='via' for r in rs)
        need(close(length,metrics['track_length_mm'],1e-4) and vias==metrics['vias'],label+' independently recomputed route length/vias')
        metrics_outcomes.append({'run':label,'length_mm':length,'vias':vias})
    native_outcomes.append({'run':label,'candidate_sha256':final_hash,'native_report_sha256':record['native_report_sha256'],**{k:native[k] for k in ('opens','blocking','warnings','exclusions')}})
    return ct,native

dsns=[]
def verify_route(directory,record,profile,variant):
    label=str(directory.relative_to(RUN))
    need(record['source']==str(source) and record['source_hashes']==hashes and record['tools']==freeze['tools'],label+' exact source/tool/code freeze')
    need(tree(directory/'snapshot')==hashes and tree(directory/'code')=={Path(n).name:h for n,h in freeze['tools']['implementation_sha256'].items()},label+' retained exact source and implementation')
    need(record['scope']=='whole_board_unlocked_routing' and record['adapter']=='both' and record['engine_profile']==profile and record.get('scoring_variant')==variant,label+' declared independent routing policy')
    need(p.parse_report(directory/'source-drc.json',source.name)==source_native,label+' exact original native source findings/settings')
    verify_steps(directory,record)
    if record.get('native_report_sha256'):verify_native(directory,record)
    for name,field in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
        if record.get(field):need(sha(directory/name)==record[field],label+' retained export hash '+name)
    if 'engine_budget' in record:
        b=record['engine_budget'];settings=p.engine_profile_settings(profile,b['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=record.get('netclass_policy') is not None,scoring_variant=variant)
        need(all(b.get(k)==v for k,v in settings.items()),label+' exact engine settings')
        need(0<b['remaining_outer_wall_seconds_at_assignment']<=record['budget_seconds'] and b['outer_task_wall_budget_seconds']==b['outer_task_cpu_budget_seconds']==record['budget_seconds'],label+' engine allowance nested within actual assignment')
        steps=[s for s in record['steps'] if s['name']=='engine'];need(len(steps)==1,label+' exactly one independent engine attempt')
        step=steps[0]
        argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(p.c.JAVA),'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(p.c.JAR),'--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(directory/'engine-config'),'--logging.file.enabled=false',*settings['argv'],'-de',str(directory/'task.dsn'),'-do',str(directory/'routes.ses')]
        need(step['argv']==argv and step['cwd']==str(directory),label+' exact command/executable/inputs/options')
        log=(directory/'engine.log').read_text();timeout_lines=[line for line in log.splitlines() if 'TIMED_OUT' in line or 'timed out' in line.lower() or 'timeout' in line.lower()]
        engine_outcomes.append({'run':label,'status':step['status'],'exit_code':step['exit_code'],'wall_seconds':step['wall_seconds'],'cpu_seconds':step['cpu_seconds'],'assigned_job_seconds':b['assigned_job_timeout_seconds'],'assigned_optimizer_seconds':b['assigned_optimizer_timeout_seconds'],'timeout_log_lines':timeout_lines[-20:]})
    if (directory/'task.dsn').exists():
        dsn=adapter._parse_dsn((directory/'task.dsn').read_text());dsn[1]='OWN_OUTPUT_PATH'
        for node in sx.children(sx.one(dsn,'structure'),'keepout'):
            m=re.fullmatch(r'kicad_autorouter_graphic_[0-9a-f]{12}_([0-9]+)',node[1])
            if m:node[1]='GENERATED_GRAPHIC_'+m.group(1)
        dsns.append(dsn)

bp=read(RUN/'B2_portfolio/protocol.json');b=read(RUN/'B2_portfolio/portfolio-summary.json')
need(b['protocol_sha256']==sha(RUN/'B2_portfolio/protocol.json') and bp['freeze']['tools']==freeze['tools'] and bp['freeze']['source_hashes']==hashes,'portfolio same frozen source and tools')
need(bp['variants']==['via_default','via_low','via_high'] and bp['fixed_order'] and bp['wall_budget_seconds']==bp['cpu_budget_seconds']==120 and bp['root_finalization_reserve_seconds']==15,'portfolio prospective variants and total budgets')
need(tree(RUN/'B2_portfolio/frozen-code')==bp['freeze']['files_sha256'],'portfolio preserved code freeze')
baseline_records={}
for i,row in enumerate(b['trials']):
    need(row['index']==i and row['id']==bp['variants'][i],'baseline ordered retained attempt '+str(i))
    need(41<=row['assigned_seconds']<=105,'baseline attempt assignment includes required reserves '+str(i))
    if row.get('result'):
        file=Path(row['result']);r=read(file);baseline_records[row['id']]=r
        need(file.parent.parent==RUN/'B2_portfolio' and sha(file)==row['result_sha256'],'baseline receipt path/hash '+row['id'])
        verify_route(file.parent,r,'tuned',row['id'])
        need(r['budget_seconds']==r['cpu_budget_seconds']==row['assigned_seconds'],'baseline exact assigned wall/CPU '+row['id'])
        need(row['status']==r['status'] and row['accepted_in_trial_receipt']==r['accepted'],'baseline failed/successful status retained '+row['id'])
        need(row['invocation_wall_seconds']>=r['wall_seconds'] and row['invocation_cpu_seconds']>=r['total_cpu_seconds'],'baseline enclosing cost includes receipt '+row['id'])
        if row['eligible']:need(r['accepted'] and max(row['invocation_wall_seconds'],row['invocation_cpu_seconds'])<=row['assigned_seconds'],'baseline eligible iff native acceptance and invocation caps '+row['id'])
        if r.get('metrics'):need(row['length_mm']==r['metrics']['track_length_mm'] and row['vias']==r['metrics']['vias'] and row['native']==r['native'],'baseline actual metric/native index '+row['id'])
    else:need(row['eligible'] is False and row['status'] in ('invocation_error','cancelled'),'missing receipt is explicit failed attempt')
    if i:need(duration(b['trials'][i-1]['finished_utc'],row['started_utc'])>=0,'baseline attempts sequential '+str(i))
need(sum(r['invocation_wall_seconds'] for r in b['trials'])<=b['wall_seconds']<=120 and sum(r['invocation_cpu_seconds'] for r in b['trials'])<=b['total_cpu_seconds']<=120,'portfolio totals contain every attempt within120')
eligible=[r for r in b['trials'] if r['eligible']]
frontier=[r['id'] for r in eligible if not any(x['vias']<=r['vias'] and x['length_mm']<=r['length_mm'] and (x['vias']<r['vias'] or x['length_mm']<r['length_mm']) for x in eligible)]
need(frontier==b['pareto_frontier'] and bool(eligible)==b['comparison_eligible'],'independent frontier/completion outcome')
if eligible:
    selected=min(eligible,key=lambda r:(r['vias'],r['length_mm'],r['index']))
    need(all(b['selected'][k]==selected[k] for k in ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm')),'unchanged selected native trial')
else:need(b['selected'] is None and b['status']=='no_valid_candidate','no valid baseline candidate stays explicit')
if len(b['trials'])<3:
    need(b.get('stop_reason') is not None,'unstarted variants have retained budget stop reason')
    # Even ignoring every setup cost, already spent attempt CPU leaves too little
    # for the 15-second portfolio reserve plus engine grace/native/minimum41.
    need(120-sum(x['invocation_cpu_seconds'] for x in b['trials'])-15<41,'unstarted variants cannot fit even optimistic remaining CPU allowance')
need(rows['B2_portfolio']['trials']==b['trials'] and rows['B2_portfolio']['selected']==b['selected'] and rows['B2_portfolio']['result_sha256']==sha(RUN/'B2_portfolio/portfolio-summary.json'),'parent portfolio index matches every outcome')

C=RUN/'C_thermal';c=read(C/'result.json');inc=read(C/'incumbent/result.json')
verify_route(C/'incumbent',inc,'completion-only',None);verify_steps(C,c)
need(c['strategy']=='native_validated_thermal_bridge' and c['engine_profile']=='completion-only' and c['adapter']=='both' and c['scope']=='whole_board_unlocked_routing','root C thermal policy contract')
need(c['source_hashes']==hashes and c['source']==str(source) and c['tools']==freeze['tools'] and tree(C/'snapshot')==hashes,'root C own source/tool snapshot')
need(tree(C/'code')=={Path(n).name:h for n,h in freeze['tools']['implementation_sha256'].items()},'root C exact implementation snapshot')
need(c['incumbent']['receipt']==str(C/'incumbent/result.json') and c['incumbent']['receipt_sha256']==sha(C/'incumbent/result.json') and c['incumbent']['status']==inc['status'] and c['incumbent']['accepted']==inc['accepted'],'independent fresh C incumbent receipt binding')
need(inc['budget_seconds']==inc['cpu_budget_seconds']==c['incumbent_assigned_seconds']<=80 and c['recovery_reserve_seconds']==40 and c['finalization_reserve_seconds']==15,'C incumbent and finalization reserve assignment')
need(all(d==dsns[0] for d in dsns),'baseline and C same adapted input problem after cosmetic labels')
if c.get('candidate_sha256'):final_tree,final_native=verify_native(C,c)
repair=c.get('repair');geometry_summary=None
if repair:
    need(repair==read(C/'recovery/repair.json'),'root C repair result equals retained helper receipt')
    geometry_summary={'status':repair['status'],'trials':len(repair['trials']),'validation_passed':repair['validation_passed']}
    need(not repair['routing_accepted'] and not repair['comparison_eligible'] and not repair['whole_body_certificate_qualified'],'helper result remains intermediate scoped evidence')
    recovery=C/'recovery';base_tree=sx.read(inc['candidate']);g=read(recovery/'geometry.json');proposals=read(recovery/'proposals.json')
    need(g['board_sha256']==inc['candidate_sha256'] and g['project_sha256']==hashes[source.with_suffix('.kicad_pro').name] and g['source_unchanged'] and not g['board_saved'] and g['api_error_count']==0,'fresh own-incumbent geometry binding')
    need(g['finding'] in inc['native']['findings'] and g['finding']['type']=='starved_thermal' and inc['native']['blocking']==1 and inc['native']['opens']==inc['native']['exclusions']==0,'sole exact triggering thermal finding')
    expected=dict(hashes);expected[source.name]=inc['candidate_sha256']
    need(tree(recovery/'input')==expected and sha(recovery/'input-drc.json')==inc['native_report_sha256'] and read(recovery/'request.json')=={'schema':1,'candidate_files':expected,'final_drc_sha256':inc['native_report_sha256']},'fresh worker complete input request/report')
    need(tree(recovery/'code')=={Path(n).name:h for n,h in freeze['tools']['implementation_sha256'].items()} and sha(recovery/'worker.py')==freeze['tools']['implementation_sha256']['autorouter/thermal_worker.py'],'worker code exactly frozen implementation')
    for tr in repair['trials']:
        d=Path(tr['candidate']).parent.parent;need(read(d/'trial.json')==tr,'retained thermal trial '+tr['id']);verify_steps(d,tr)
        trial_tree,trial_native=verify_native(d,tr)
        added=p.routes(trial_tree)[len(p.routes(base_tree)):]
        need(p.routes(trial_tree)[:len(p.routes(base_tree))]==p.routes(base_tree) and len(added)==1 and added[0][0]=='segment','one exact generated track; original routes unchanged '+tr['id'])
        deleted=copy.deepcopy(trial_tree);deleted.remove(added[0])
        need(deleted==base_tree and hashlib.sha256((sx.dump(deleted)+'\n').encode()).hexdigest()==inc['candidate_sha256'],'removing added track restores exact fresh failed bytes '+tr['id'])
        proposal=proposals['path_certificate_candidates'][tr['proposal_index']];node=added[0]
        def nm(v):return int(Decimal(v)*1000000)
        need(list(map(nm,sx.one(node,'start')[1:3]))==proposal['start_nm'] and list(map(nm,sx.one(node,'end')[1:3]))==proposal['end_nm'] and nm(sx.one(node,'width')[1])==proposal['width_nm'] and int(sx.one(node,'net')[1])==proposal['net_code'] and sx.unquote(sx.one(node,'layer')[1])==proposal['layer'],'exact proposed added track '+tr['id'])
        oldwarnings={(f['type'],tuple(sorted(i['uuid'] for i in f['items']))) for f in inc['native']['findings'] if f['severity']=='warning'}
        newwarnings={(f['type'],tuple(sorted(i['uuid'] for i in f['items']))) for f in trial_native['findings'] if f['severity']=='warning'}
        need(tr['validation_passed']==(p.native_accepted(trial_native) and newwarnings<=oldwarnings),'thermal native+no-new-warning decision '+tr['id'])
    if repair['validation_passed']:
        need(c['candidate_sha256']==repair['candidate_sha256']==sha(repair['candidate']),'root final candidate exact validated repair incl fill')
    # Independent exact-rational geometric audit, separate from proposal code.
    import geometry_audit
    geometry_summary['independent_paths']=geometry_audit.audit(base_tree,g,proposals,sx,need)
    nested=[dict(s,phase='incumbent') for s in inc['steps']]
    nested+=[dict(read(recovery/'thermal-geometry-process.json'),name='thermal-geometry')]
    nested+=[s for t in repair['trials'] for s in t['steps']]
    need(c['steps'][:len(nested)]==nested,'C charges own incumbent+geometry+all trials exactly once')
    need(all(Path(s['cwd'])==C for s in c['steps'][len(nested):]),'remaining C steps only final native delivery')

for arm,row in rows.items():
    invocation=read(RUN/(arm+'-invocation.json'))
    need(all(row.get(k)==v for k,v in invocation.items()),arm+' retained enclosing invocation')
    for key in ('wall','cpu'):
        raw=row['invocation_'+key+'_seconds'];shared=summary['shared_overhead_'+key+'_seconds'];charged=row['charged_'+key+'_seconds']
        need(finite(shared) and close(raw+shared,charged) and charged<=120,arm+' all shared '+key+' charged within120')
    need(close(duration(row['started_utc'],row['finished_utc']),row['invocation_wall_seconds'],.005),arm+' UTC/enclosing monotonic timing')
    for suffix in ('begin','end'):need(len(row['host_load_average_1_5_15_minutes_'+suffix])==3 and all(finite(x) for x in row['host_load_average_1_5_15_minutes_'+suffix]),arm+' host load observed '+suffix)
need(duration(rows['B2_portfolio']['finished_utc'],rows['C_thermal']['started_utc'])>=0,'baseline then C nonoverlapping native schedule')
for key in ('wall','cpu'):need(close(summary['batch_'+key+'_seconds'],sum(r['invocation_'+key+'_seconds'] for r in rows.values())+summary['shared_overhead_'+key+'_seconds']),'batch '+key+' all raw+shared arithmetic')
need(rows['C_thermal']['result_sha256']==sha(C/'result.json') and rows['C_thermal']['accepted_in_receipt']==c['accepted'],'root C indexed receipt/hash outcome')
need(rows['C_thermal']['invocation_wall_seconds']>=c['wall_seconds'] and rows['C_thermal']['invocation_cpu_seconds']>=c['total_cpu_seconds'],'C enclosing charge includes entire recovery')
need(rows['B2_portfolio']['invocation_wall_seconds']>=b['wall_seconds'] and rows['B2_portfolio']['invocation_cpu_seconds']>=b['total_cpu_seconds'],'B2 enclosing charge includes all attempts')
if not rows['B2_portfolio']['accepted'] or not rows['C_thermal']['accepted']:need(summary['comparisons']==[],'no invalid-route quality comparison; completion outcomes retained separately')
else:need(len(summary['comparisons'])==len(frontier),'quality compares all valid baseline frontier points')
# Separate historical repair-only positive/removal counterfactual linkage.
positive_root=ROOT/'.runs/thermal-auto-control-draft-001/native-001'
positive_summary=read(positive_root/'summary.json');positive_trial=read(positive_root/positive_summary['selected']/'diagnostic-result.json')
negative_root=ROOT/'.runs/thermal-auto-negative-001';negative=read(negative_root/'negative-summary.json')
positive_candidate=Path(positive_trial['candidate']);negative_candidate=Path(negative['candidate'])
need(positive_summary['validation_passed'] and not positive_summary['routing_accepted'] and sha(positive_root/positive_summary['selected']/'diagnostic-result.json')==positive_summary['selected_trial_receipt_sha256'],'separate repair-only positive receipt bound')
need(sha(positive_candidate)==positive_trial['candidate_sha256'] and sha(positive_candidate.parent.parent/'final-drc.json')==positive_trial['native_report_sha256'],'historical positive candidate/report unchanged')
need(negative['control_passed'] and negative['original_inputs_unchanged'] and not negative['candidate_accepted'] and not negative['routing_accepted'],'separate actual negative remains expected rejection')
need(sha(negative_candidate)==negative['candidate_sha256']=='922c6ce93556732940b5bccc06794c84b35fd164f86abd0ac3f6faf5b76e3f41' and sha(negative_root/'trial/final-drc.json')==negative['native_report_sha256'],'negative candidate/report exact historical failed bytes')
neg_native=p.parse_report(negative_root/'trial/final-drc.json',source.name)
need(neg_native==negative['native'] and neg_native==inc['native'],'fresh incumbent reproduces independently counterfactually qualified sole thermal')
route_geometry=lambda t:collections.Counter(sx.dump([n for n in r if not isinstance(n,list) or n[0]!='uuid']) for r in p.routes(t))
need(route_geometry(sx.read(negative_candidate))==route_geometry(sx.read(inc['candidate'])),'fresh incumbent geometry equals historical negative ignoring generated UUIDs')
need(inc['candidate_sha256']!=negative['candidate_sha256'],'fresh incumbent is separately generated/bound, not historical candidate receipt')
historical={'positive_receipt_sha256':sha(positive_root/'summary.json'),'negative_receipt_sha256':sha(negative_root/'negative-summary.json'),'positive_native_report_sha256':positive_trial['native_report_sha256'],'negative_native_report_sha256':negative['native_report_sha256'],'negative_candidate_sha256':negative['candidate_sha256'],'fresh_incumbent_candidate_sha256':inc['candidate_sha256'],'qualification_scope':'historical repair-only positive/removal counterfactual; equal-budget completion evidence comes solely from this fresh pair'}
# Public subset is a selected byte-identical copy, not complete restoration data.
public=ROOT/'evidence/thermal-paired-001';public_summary={'present':public.is_dir(),'verified':False}
if public.is_dir():
    manifest=read(public/'public-files.json');actual=tree(public)
    indexed={f['path']:f for f in manifest['files']}
    need(len(indexed)==len(manifest['files']) and manifest['raw_root']=='.runs/thermal-paired-001','public manifest unique paths/raw identity')
    need(set(actual)==set(indexed)|{'SCOPE.md','public-files.json'},'public exact selected-file inventory')
    for name,row in indexed.items():
        need(actual[name]==row['sha256']==sha(RUN/name) and (public/name).stat().st_size==row['bytes'],'public exact raw bytes '+name)
    scope=(public/'SCOPE.md').read_text()
    need('Complete immutable project snapshots, native input trees and frozen code remain in the local raw run' in scope and 'no valid B2 quality comparator' in scope,'public limitations distinguish subset and completion outcome')
    public_summary.update(verified=True,raw_files=len(indexed),raw_bytes=sum(r['bytes'] for r in indexed.values()))
need(tree(source.parent)==hashes,'original source remains unchanged after audit')
need(tree(RUN)==initial_inventory,'complete raw paired run unchanged during audit')
report={'passed':not failures,'check_count':len(checks),'failures':failures,'frozen_commit':HEAD,'native_executed_by_reviewer':False,'native_outcomes':native_outcomes,'engines':engine_outcomes,'metrics':metrics_outcomes,'geometry':geometry_summary,'historical_controls':historical,'public_subset':public_summary,'original_ignored_checks_unchanged':source_native['ignored_checks'],'outcomes':{arm:{k:r.get(k) for k in ('status','accepted','charged_wall_seconds','charged_cpu_seconds','opens','blocking','warnings','exclusions','length_mm','vias')} for arm,r in rows.items()},'baseline_attempted':[r['id'] for r in b['trials']],'baseline_not_started':[v for v in bp['variants'] if v not in {r['id'] for r in b['trials']}],'baseline_stop_reason':b.get('stop_reason'),'baseline_frontier':frontier,'quality_comparisons':summary['comparisons'],'scope':['Stored raw consistency and independent exact geometry audit, not a fresh native run or human PCB review.','One exposed development board/family and one sequential pair; no population superiority or statistical/generalization claim.','A valid C completion with no valid B2 completion is a completion outcome; invalid B2 length/via metrics are not quality comparators.','Measured wall/CPU caps include shared setup and failed work; CPU acceptance caps are postcompletion, polling resource limits may overshoot.','Prior repair-only positive/removal counterfactual supports mechanism qualification but is distinct from this newly generated incumbent and full-budget run.','B2 reached cooperative internal timeout, emitted an SES, and failed actual native thermal validation; it did not exhaust every possible tuned configuration.','C uses a different declared engine allocation/profile; completion-only and other baseline ablations are needed to isolate repair contribution.','The public subset omits complete project/native-input trees; full raw evidence remains local.'],'script_sha256':sha(__file__)}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('passed','check_count','failures','outcomes','baseline_attempted','baseline_not_started','baseline_stop_reason')},indent=2))
raise SystemExit(bool(failures))
