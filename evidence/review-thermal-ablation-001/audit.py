"""Independent stored paired thermal evidence audit; no native/engine execution."""
from pathlib import Path
import collections, copy, datetime, hashlib, importlib, json, math, re, subprocess, sys, types
from decimal import Decimal
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'.runs/thermal-ablation-001';OUT=Path(__file__).resolve().parent
HEAD='cc71a5103f32b97274fb82a9494501b0b823d541'
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

protocol=read(RUN/'protocol.json');summary=read(RUN/'summary.json');freeze=protocol['freeze']
initial_inventory=tree(RUN)
need(sha(RUN/'protocol.json')==summary['protocol_sha256'],'ablation protocol hash')
need(freeze['tools']['git_head']==HEAD,'expected committed ablation freeze')
need(tree(RUN/'frozen-code')==freeze['files_sha256'],'full frozen source inventory')
for name,digest in freeze['files_sha256'].items():
    blob=subprocess.run(['git','-C',str(ROOT),'show',HEAD+':'+name],capture_output=True,check=True).stdout
    need(hashlib.sha256(blob).hexdigest()==digest,'exact committed frozen file '+name)
for name,digest in freeze['tools']['files'].items():need(sha(name)==digest,'native tool file '+Path(name).name)
source=Path(protocol['source']);hashes=freeze['source_hashes'];need(tree(source.parent)==hashes,'original source unchanged')
package=types.ModuleType('ablation_audit_frozen');package.__path__=[str(RUN/'frozen-code/autorouter')];sys.modules[package.__name__]=package
p=importlib.import_module(package.__name__+'.pipeline');p.c.ROOT=ROOT;p.c.JAR=ROOT/'.tools/freerouting-2.5.0.jar';sx=p.sx
adapter=importlib.import_module(package.__name__+'.adapter')
original=p.preflight(source);protected=[r for r in p.routes(original) if p.locked(r)]
source_native=p.parse_report(RUN/'B0_standard120/source-drc.json',source.name)
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
def verify_route(directory,record,profile,variant,adapter_kind):
    label=str(directory.relative_to(RUN))
    need(record['source']==str(source) and record['source_hashes']==hashes and record['tools']==freeze['tools'],label+' exact source/tool/code freeze')
    need(tree(directory/'snapshot')==hashes and tree(directory/'code')=={Path(n).name:h for n,h in freeze['tools']['implementation_sha256'].items()},label+' retained exact source and implementation')
    need(record['scope']=='whole_board_unlocked_routing' and record['adapter']==adapter_kind and record['engine_profile']==profile and record.get('scoring_variant')==variant,label+' declared independent routing policy')
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

arms=[{'id':'B0_standard120','adapter':'none','engine_profile':'standard','operation':'route'},
      {'id':'B1_standard120','adapter':'both','engine_profile':'standard','operation':'route'},
      {'id':'B1_completion120','adapter':'both','engine_profile':'completion-only','operation':'route'}]
need(protocol['arms']==arms and protocol['fixed_order'] and protocol['wall_budget_per_arm_seconds']==protocol['cpu_budget_per_arm_seconds']==120,'predeclared separate120 wall/CPU arms')
need(summary['status']=='completed' and [r['id'] for r in summary['results']]==[a['id'] for a in arms],'all three attempts completed and retained')
reference=protocol['prior_pair'];prior=Path(reference['prior_directory'])
need(prior==ROOT/'.runs/thermal-paired-001' and summary['prior_pair']==reference,'prior pair exact reference identity')
need(tree(prior)==reference['prior_tree_sha256'],'entire prior raw pair unchanged since cross-bind')
old_protocol=read(prior/'protocol.json');old_summary=read(prior/'paired-summary.json');old=old_protocol['freeze']
need(reference['results']==old_summary['results'] and old_summary['status']=='completed','original prior outcomes and accounting retained')
need(old['tools']['git_head']==reference['prior_git_head']=='cbae1254f00d3470d98ba18d24a09e99874f0cc2' and reference['current_git_head']==HEAD,'precise prior/new Git provenance')
need({k:v for k,v in old['tools'].items() if k!='git_head'}=={k:v for k,v in freeze['tools'].items() if k!='git_head'},'native tools/all production code exactly equal across separate runs')
need(old['source_hashes']==hashes and old_protocol['source']==str(source),'same entire original project and immutable problem')
harness='scripts/experiment_thermal_ablation.py'
need(set(freeze['files_sha256'])==set(old['files_sha256'])|{harness} and all(freeze['files_sha256'].get(k)==v for k,v in old['files_sha256'].items()),'only added harness beyond prior frozen protocol/source file set')
for name,digest in reference['bound_files_sha256'].items():need(sha(name)==digest,'cross-bound prior evidence '+str(Path(name).relative_to(prior)))
for name,expected in summary['completed_arm_and_frozen_code_trees'].items():need(tree(Path(name))==expected,'all completed/frozen evidence remains bound '+Path(name).name)
records={}
for arm,row in zip(arms,summary['results']):
    directory=RUN/arm['id'];r=read(directory/'result.json');records[arm['id']]=r
    need(row['result']==str(directory/'result.json') and row['result_sha256']==sha(directory/'result.json'),'raw result/index binding '+arm['id'])
    verify_route(directory,r,arm['engine_profile'],None,arm['adapter'])
    need(r['budget_seconds']==r['cpu_budget_seconds']==120,'raw equal120 assignment '+arm['id'])
    need(row['engine_contract_verified'] and row['engine_completed_successfully'] and row['protocol_contract_verified'],'actual executed intended contract '+arm['id'])
    need(row['accepted_in_receipt']==r['accepted'] and row['status']==r['status'],'native failure/success unchanged in index '+arm['id'])
    for key in ('opens','blocking','warnings','exclusions'):need(row[key]==r['native'][key],arm['id']+' native count '+key)
    for key in ('candidate_sha256','native_report_sha256','wall_seconds','parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','total_cpu_seconds'):need(row[key]==r[key],arm['id']+' indexed '+key)
    need(row['length_mm']==r['metrics']['track_length_mm'] and row['vias']==r['metrics']['vias'],arm['id']+' raw metrics retained without acceptance claim')
    need(row['invocation_wall_seconds']>=r['wall_seconds'] and row['invocation_cpu_seconds']>=r['total_cpu_seconds'],arm['id']+' invocation charges entire failed route')
    need(row['accepted'] is False and r['accepted'] is False and not p.native_accepted(r['native']),arm['id']+' actual native failure stays rejected')
    invocation=read(RUN/(arm['id']+'-invocation.json'))
    need(all(row.get(k)==v for k,v in invocation.items()),arm['id']+' enclosing invocation index exact')
    need(close(duration(row['started_utc'],row['finished_utc']),row['invocation_wall_seconds'],.005),arm['id']+' UTC/monotonic duration consistent')
    for suffix in ('begin','end'):need(len(row['host_load_average_1_5_15_minutes_'+suffix])==3 and all(finite(v) for v in row['host_load_average_1_5_15_minutes_'+suffix]),arm['id']+' observed desktop load '+suffix)
    for kind in ('wall','cpu'):
        raw=row['invocation_'+kind+'_seconds'];shared=summary['shared_overhead_'+kind+'_seconds'];charged=row['charged_'+kind+'_seconds']
        need(finite(shared) and close(raw+shared,charged) and raw<=charged<=120,arm['id']+' full shared '+kind+' charge within120')
    if arm['adapter']=='none':need(sha(directory/'native.dsn')==sha(directory/'task.dsn'),'B0 no adapter modification')
for a,b in zip(summary['results'],summary['results'][1:]):need(duration(a['finished_utc'],b['started_utc'])>=0,'new arm native workers strictly sequential '+a['id'])
for key in ('wall','cpu'):need(close(summary['batch_'+key+'_seconds'],sum(r['invocation_'+key+'_seconds'] for r in summary['results'])+summary['shared_overhead_'+key+'_seconds']),'all new shared '+key+' charged once in batch and in full to each arm')
need(dsns[1]==dsns[2],'B1 standard and completion-only exact adapted problem apart from cosmetic names')
def normalized(path):
    d=adapter._parse_dsn(path.read_text());d[1]='OWN_OUTPUT_PATH'
    for node in sx.children(sx.one(d,'structure'),'keepout'):
        m=re.fullmatch(r'kicad_autorouter_graphic_[0-9a-f]{12}_([0-9]+)',node[1])
        if m:node[1]='GENERATED_GRAPHIC_'+m.group(1)
    return d
need(dsns[1]==normalized(prior/'C_thermal/incumbent/task.dsn'),'B1 adapted problem exactly prior C own engine input')
old_c=read(prior/'C_thermal/result.json');old_inc=read(prior/'C_thermal/incumbent/result.json')
need(records['B1_standard120']['native']==records['B1_completion120']['native']==old_inc['native'],'both adapter baselines retain exact prior C pre-repair sole thermal')
geometry=lambda board:collections.Counter(sx.dump([n for n in r if not isinstance(n,list) or n[0]!='uuid']) for r in p.routes(sx.read(board)))
need(geometry(Path(records['B1_completion120']['candidate']))==geometry(Path(old_inc['candidate'])),'completion-only fresh geometry equals prior C pre-repair ignoring generated UUIDs')
expected_comparisons=[]
prior_crow=next(r for r in old_summary['results'] if r['id']=='C_thermal')
for row in summary['results']:
    expected_comparisons.append({'baseline':row['id'],'system':'prior_C_thermal','baseline_accepted':False,'C_accepted':True,'completion_difference':1,'interpretation':'separately charged policies; completion/profile/allocation effects are not a thermal-only ablation'})
need(summary['comparisons']==expected_comparisons,'completion outcomes only; no invalid baseline quality deltas')
need(prior_crow['accepted'] and old_c['accepted'] and old_c['native']['opens']==old_c['native']['blocking']==old_c['native']['warnings']==old_c['native']['exclusions']==0,'prior accepted C native clean under unchanged configured checks')
public=ROOT/'evidence/thermal-ablation-001';public_result={'present':public.is_dir(),'verified':False}
if (public/'public-files.json').exists():
    manifest=read(public/'public-files.json');actual=tree(public);indexed={r['path']:r for r in manifest['files']}
    need(len(indexed)==len(manifest['files']) and manifest['raw_root']=='.runs/thermal-ablation-001','public exact manifest identity')
    need(set(actual)==set(indexed)|{'SCOPE.md','public-files.json'},'public exact selected file set')
    for name,row in indexed.items():need(actual[name]==row['sha256']==sha(RUN/name) and (public/name).stat().st_size==row['bytes'],'public exact raw copy '+name)
    public_result.update(verified=True,raw_files=len(indexed),raw_bytes=sum(r['bytes'] for r in indexed.values()))
need(tree(RUN)==initial_inventory,'raw ablation unchanged by audit')
need(tree(prior)==reference['prior_tree_sha256'] and tree(source.parent)==hashes,'prior complete evidence and original project remain unchanged')
report={'passed':not failures,'check_count':len(checks),'failures':failures,'native_executed_by_reviewer':False,'frozen_commit':HEAD,'prior_commit':reference['prior_git_head'],'production_tools_source_existing_protocol_exactly_equal':True,'native_outcomes':native_outcomes,'engine_outcomes':engine_outcomes,'analytical_metrics':metrics_outcomes,'public_subset':public_result,'outcomes':[{k:r[k] for k in ('id','status','accepted','opens','blocking','warnings','exclusions','charged_wall_seconds','charged_cpu_seconds','length_mm','vias')} for r in summary['results']],'original_ignored_checks':source_native['ignored_checks'],'comparisons':summary['comparisons'],'scope':['All three fresh baseline policies rejected under original native constraints, within their own120-second wall/CPU ceilings including full shared verification/freeze/publication overhead.','Prior accepted C is cross-bound by identical production code/tools/source/old protocol bytes; these are separately timed sequential runs, not a new randomized joint comparison.','B1 completion-only reproduces the prior C pre-repair route geometry up to generated UUIDs and the exact thermal report, strengthening the repair-mechanism explanation without a population claim.','Invalid baseline route metrics remain diagnostics only; no accepted-route length/via superiority claim follows.','Original ignored-check configuration is unchanged; zero findings under it is not physical/electrical/ampacity or human-review qualification.','Stored totals precede final freshness/publication work; the frozen harness checks full charged acceptance caps afterward.','No new native jobs were executed by this reviewer.'],'script_sha256':sha(__file__)}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('passed','check_count','failures','outcomes','public_subset')},indent=2))
raise SystemExit(bool(failures))
