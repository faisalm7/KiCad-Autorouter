"""Read-only quality003 evidence consistency audit; no native/routing execution."""
from pathlib import Path
import collections, copy, hashlib, importlib, json, math, re, subprocess, sys, types
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / '.runs/quality-comparison-003'
PUBLIC = ROOT / 'evidence/quality-comparison-003'
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
package=types.ModuleType('quality003_frozen');package.__path__=[str(RUN/'frozen-code/autorouter')];sys.modules[package.__name__]=package
p=importlib.import_module('quality003_frozen.pipeline');p.c.ROOT=ROOT
sx=p.sx;source=Path(protocol['source']);original=sx.read(source);original_hashes=freeze['source_hashes']
protected=[route for route in p.routes(original) if p.locked(route)]
rows={row['id']:row for row in summary['results']};records={}

# Public pack is an intentionally incomplete exact-byte subset, not a complete
# locally checkable run. Its extra attribution/manifest are not native evidence.
manifest=read(PUBLIC/'subset-manifest.json');public_files=inventory(PUBLIC)
require(set(public_files)==set(manifest['files'])|{'ATTRIBUTION.md','subset-manifest.json'},'public subset exact declared file set')
require(manifest['count']==len(manifest['files']),'public subset count')
require(manifest['bytes']==sum((PUBLIC/name).stat().st_size for name in manifest['files']),'public subset byte count')
for name,digest in manifest['files'].items():
    require(public_files[name]==digest and sha(RUN/name)==digest,f'public/local/manifest exact hash: {name}')

standard=['--router.autorouter.max_passes=30','--router.optimizer.max_threads=1','--router.optimizer.max_passes=10','--router.job_timeout=60s','--router.optimizer.timeout=30s']
tuned=['--router.autorouter.max_passes=100','--router.optimizer.max_threads=1','--router.optimizer.max_passes=50','--router.job_timeout=100s','--router.optimizer.timeout=90s','--router.optimizer.improvement_threshold=0.001','--router.optimizer.enable_preflight_guards=false','--router.optimizer.max_consecutive_failures=100','--router.optimizer.max_consecutive_failures_pass1=100']
probe=ROOT/'.runs/optimizer-profile-probe-001';probe_result=read(probe/'result.json');probe_actual=read(probe/'actual-settings.json')
require(sha(probe/'actual-settings.json')==probe_result['actual_settings_sha256'],'timeout parser probe binding')
require(probe_result['jar_sha256']==freeze['tools']['files'][str(ROOT/'.tools/freerouting-2.5.0.jar')],'timeout parser probe same JAR')
require(probe_result['pipeline_sha256']==freeze['tools']['implementation_sha256']['autorouter/pipeline.py'],'timeout parser probe same pipeline')
for value in ('60s','30s','100s','90s'):require(probe_actual['timespans_to_seconds'][value] is None,f'malformed timer confirmed: {value}')

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

for arm in ('B0','B1','B2','C','C/incumbent'):
    directory=RUN/arm;r=read(directory/'result.json');records[arm]=r;verify_native(directory,r);verify_steps(directory,r)
    require(inventory(directory/'snapshot')==original_hashes,arm+' frozen source snapshot unchanged')
    require(r['source']==str(source) and r['source_hashes']==original_hashes,arm+' common source identity')
    require(r['tools']==freeze['tools'],arm+' exact frozen tool/code provenance')
    require(inventory(directory/'code')=={Path(n).name:h for n,h in freeze['tools']['implementation_sha256'].items()},arm+' exact retained worker implementation')
    require(r['scope']=='whole_board_unlocked_routing',arm+' scope')
    if r['accepted']:
        try:p.check_result(directory/'result.json');verified=True
        except Exception as exc:verified=False;failures.append(arm+' frozen check_result: '+repr(exc))
        require(verified,arm+' frozen check_result accepted')
    if arm in rows:
        row=rows[arm];inv=read(RUN/(arm+'-invocation.json'))
        require(sha(directory/'result.json')==row['result_sha256'],arm+' summary receipt hash')
        require(row['accepted']==r['accepted'],arm+' acceptance summary')
        for key in ('wall_seconds','parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','total_cpu_seconds','peak_child_rss_bytes','candidate_sha256','native_report_sha256'):
            require(row[key]==r[key],arm+' summary '+key)
        require(row['length_mm']==r['metrics']['track_length_mm'] and row['vias']==r['metrics']['vias'],arm+' summary quality')
        require(inv['cpu_seconds']>=r['total_cpu_seconds']-1e-6 and inv['wall_seconds']>=r['wall_seconds']-1e-6,arm+' invocation accounts complete receipt')
        require(inv['cpu_seconds']<=120 and inv['wall_seconds']<=120,arm+' full invocation within equal budgets')
        require(row['invocation_cpu_seconds']==inv['cpu_seconds'] and row['invocation_wall_seconds']==inv['wall_seconds'],arm+' invocation summary equality')
    if arm!='C':
        engine=read(directory/'engine-process.json');log=(directory/'engine.log').read_text();flags=[x for x in engine['argv'] if x.startswith('--router.')]
        expected=tuned if arm in ('B2','C/incumbent') else standard
        require(flags==expected,arm+' exact engine profile settings')
        require(engine['exit_code']==0 and engine['status']=='success',arm+' engine exit success')
        tuned_profile=arm in ('B2','C/incumbent');require(r['engine_profile']==('tuned' if tuned_profile else 'standard'),arm+' receipt engine profile')
        require(r['adapter']==('none' if arm=='B0' else 'both'),arm+' receipt adapter')
        thresholds=[float(x) for x in re.findall(r'threshold \(([0-9.]+)%\)',log)]
        require(thresholds and all(close(x,.1 if tuned_profile else 2.5) for x in thresholds),arm+' logged optimizer threshold')
        opt=float(re.search(r'Optimization stage completed:.*?completed in ([0-9.]+) seconds',log).group(1))
        job=float(re.search(r'finished with state: COMPLETED \(elapsed: ([0-9.]+) seconds',log).group(1))
        intended_job,intended_opt=(100,90) if tuned_profile else (60,30)
        require(engine['wall_seconds']<min(intended_job,intended_opt) and opt<intended_opt and job<intended_job,arm+' finished below intended internal time caps')
        engines.append({'run':arm,'worker_wall_seconds':engine['wall_seconds'],'worker_cpu_seconds':engine['cpu_seconds'],'logged_job_seconds':job,'logged_optimizer_seconds':opt,'intended_job_cap_seconds':intended_job,'intended_optimizer_cap_seconds':intended_opt,'actual_timeout_parser_values':None,'observed_threshold_percent':thresholds})

c=records['C'];inc=records['C/incumbent'];require(c['incumbent_baseline']=='B2_tuned' and c['engine_profile']=='tuned' and c['adapter']=='both','C tuned baseline/adapter contract')
require(c['incumbent']['receipt']==str(RUN/'C/incumbent/result.json') and c['incumbent']['accepted'] and inc['accepted'],'C exact accepted nested incumbent')
require(inc['baseline']=='B2_tuned' and c['incumbent_metrics']==inc['metrics'],'C incumbent metrics and label')
require(inc['budget_seconds']<=105 and inc['cpu_budget_seconds']<=105,'C reserved incumbent caps')
adapter=importlib.import_module('quality003_frozen.adapter')
dsns=[];dsn_names=[]
for relative in ('B2/task.dsn','C/incumbent/task.dsn'):
    file=RUN/relative;tree=adapter._parse_dsn(file.read_text())
    require(tree[0]=='pcb' and sx.unquote(tree[1])==str(file),relative+' top-level DSN filename exact own output')
    tree[1]='"OWN_OUTPUT_DSN"';names=[]
    for node in sx.children(sx.one(tree,'structure'),'keepout'):
        match=re.fullmatch(r'kicad_autorouter_graphic_[0-9a-f]{12}_([0-9]+)',node[1])
        if match:
            names.append(node[1]);node[1]='kicad_autorouter_graphic_IDENTICAL_'+match.group(1)
    require(len(names)==8 and len(set(names))==8,relative+' eight unique generated graphic labels')
    dsns.append(tree);dsn_names.append(names)
require(dsns[0]==dsns[1],'B2/C DSN all geometry/rules/network atoms equal after exact output-path/generated-name normalization')
def geometry(path):
    return collections.Counter(sx.dump([n for n in route if not isinstance(n,list) or n[0]!='uuid']) for route in p.routes(sx.read(path)))
require(geometry(Path(b2_candidate:=records['B2']['candidate']))==geometry(Path(inc['candidate'])),'B2/C incumbent route geometry equal excluding only route UUIDs')
trials=[]
for row in c['trials']:
    file=Path(row['receipt']);r=read(file);require(row['id']==r['id'] and row['status']==r['status'] and row['accepted']==r['accepted'],'C trial index binding '+row['id']);verify_native(file.parent,r);verify_steps(file.parent,r);trials.append(r)
require(sum(r['accepted'] for r in trials)==c['improvements'],'C improvement count')
expected_steps=[dict(step,phase='incumbent') for step in inc['steps']]+[step for trial in trials for step in trial['steps']]
require(c['steps'][:len(expected_steps)]==expected_steps,'C charges incumbent and every failed/successful trial exactly once')
require(all(st['phase']=='finalization' and st['cwd']==str(RUN/'C') for st in c['steps'][len(expected_steps):]),'C remaining steps only root finalization')
checkpoint_rows=[]
for name in c['checkpoints']:
    cp=read(RUN/'C'/name);require(sha(cp['candidate'])==cp['candidate_sha256'],'C checkpoint candidate retained '+name);checkpoint_rows.append(cp)
require(all(a['elapsed_seconds']<=b['elapsed_seconds'] and a['observed_cpu_seconds']<=b['observed_cpu_seconds'] for a,b in zip(checkpoint_rows,checkpoint_rows[1:])),'C checkpoints time and CPU monotonic')
require(checkpoint_rows[-1]['candidate_sha256']==c['candidate_sha256'] and checkpoint_rows[-1]['metrics']==c['metrics'],'C final checkpoint exact candidate and metrics')

b2=records['B2'];length_delta=c['metrics']['track_length_mm']-b2['metrics']['track_length_mm'];inv_b2=read(RUN/'B2-invocation.json');inv_c=read(RUN/'C-invocation.json')
comparison=next(x for x in summary['comparisons'] if x['baseline']=='B2')
require(close(comparison['length_delta_mm'],length_delta) and comparison['via_delta']==c['metrics']['vias']-b2['metrics']['vias'],'B2/C comparison arithmetic')
require(close(comparison['wall_delta_seconds'],inv_c['wall_seconds']-inv_b2['wall_seconds']) and close(comparison['cpu_delta_seconds'],inv_c['cpu_seconds']-inv_b2['cpu_seconds']),'B2/C reported cost deltas')
require(close(summary['batch_wall_seconds']-sum(read(RUN/(a+'-invocation.json'))['wall_seconds'] for a in rows),summary['shared_freeze_and_summary_overhead_wall_seconds']),'batch wall overhead arithmetic')
require(close(summary['batch_cpu_seconds']-sum(read(RUN/(a+'-invocation.json'))['cpu_seconds'] for a in rows),summary['shared_freeze_and_summary_overhead_cpu_seconds']),'batch CPU overhead arithmetic')
report={'schema':1,'audit':'read-only consistency, semantic invariants and metric arithmetic; no fresh native validation or cryptographic authenticity claim','source_commit':head,'audit_script_sha256':sha(__file__),'run_protocol_sha256':sha(RUN/'protocol.json'),'public_subset_manifest_sha256':sha(PUBLIC/'subset-manifest.json'),'public_attribution_sha256':sha(PUBLIC/'ATTRIBUTION.md'),'checks':len(checks),'failures':failures,'passed':not failures,'public_subset':{'files_verified':len(manifest['files']),'bytes_verified':manifest['bytes'],'complete_run':False,'omissions_disclosed_in_attribution':True},'source_project_unchanged':not any('source' in x for x in failures),'engine_configuration':engines,'native_bindings_verified':native_checks,'independent_metrics':metrics_recomputed,'DSN_comparison':{'raw_byte_equal':False,'allowed_differences':['top-level own output DSN filename','eight generated graphics keepout label hash prefixes'],'generated_labels':dsn_names,'all_other_atoms_equal':dsns[0]==dsns[1],'incumbent_geometry_equal_ignoring_route_UUIDs':geometry(Path(records['B2']['candidate']))==geometry(Path(inc['candidate']))},'C_trials':{'count':len(trials),'outcomes':dict(collections.Counter(t['status'] for t in trials)),'improvements':c['improvements']},'B2_vs_C':{'B2_length_mm':b2['metrics']['track_length_mm'],'C_length_mm':c['metrics']['track_length_mm'],'length_saved_mm':-length_delta,'length_saved_percent':-100*length_delta/b2['metrics']['track_length_mm'],'B2_vias':b2['metrics']['vias'],'C_vias':c['metrics']['vias'],'B2_invocation_wall_seconds':inv_b2['wall_seconds'],'C_invocation_wall_seconds':inv_c['wall_seconds'],'B2_invocation_CPU_seconds':inv_b2['cpu_seconds'],'C_invocation_CPU_seconds':inv_c['cpu_seconds']},'warnings':c['native']['findings'],'ignored_checks':read(RUN/'C/final-drc.json')['ignored_checks'],'issues':[{'severity':'configuration defect; does not invalidate stored outer-budget acceptance','finding':'All frozen arm internal job/optimizer timeout strings use unsupported s suffix; actual pinned JAR parser probe returns null. Actual engine and optimizer durations finished below intended limits, with normal COMPLETED/threshold stops. Cannot claim configured internal timer enforcement or equivalence to repaired profiles. Keep this evidence frozen and run corrected follow-up.'},{'severity':'scope limitation','finding':'One exposed family; quality proxy improves at materially higher wall/CPU, no completion advantage over B1/B2, no generalized superiority. One inherited library mismatch warning remains; connection_width and other listed checks remain originally ignored. Physical/electrical adequacy and schematic parity are unverified.'},{'severity':'artifact limitation','finding':'Public pack intentionally omits full original and retained native-input project trees/libraries, so local check-result is for the complete .runs run only. All published subset bytes match local evidence. A mutable receipt consistency audit is not proof against complete-history forgery.'}]}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'failures':failures,'public_files':len(manifest['files']),'native_receipts':len(native_checks),'C_trials':report['C_trials'],'comparison':report['B2_vs_C'],'engine_durations':engines},indent=2))
sys.exit(0 if report['passed'] else 1)
