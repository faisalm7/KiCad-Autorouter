"""Stored positive repair audit. Importing this module never executes a job."""
from pathlib import Path
from decimal import Decimal
import ast,copy,hashlib,json,math,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
POSITIVE=ROOT/'.runs/thermal-auto-control-draft-001/native-001'
BASE=ROOT/'.runs/interf-native-003'
BASE_HASH='922c6ce93556732940b5bccc06794c84b35fd164f86abd0ac3f6faf5b76e3f41'
GOOD_HASH='d3d7acd394464cd670be574bfc78117a1604509b61e740bb8168b514996564c6'
REPORT_HASH='c173c5fb1fb353228614723399670a09cef6e5bd8fcf11938becbaa884fa358b'
UID='5f46c41d-abc3-5586-b349-38f2b4862fcd'
PAD='387e8928-4a73-4b3a-ae74-249440996e94'
ZONE='00000000-0000-0000-0000-00004cdec22b'
def read(path):return json.loads(Path(path).read_text())
def mm(value):return format(Decimal(value)/1000000,'f')
def verify_positive():
    checks=[]
    def need(ok,label):
        checks.append(label)
        if not ok:raise p.Rejected(label)
    summary=read(POSITIVE/'summary.json');protocol=read(POSITIVE/'protocol.json')
    need(summary['status']=='diagnostic_native_pass' and summary['validation_passed'] and summary['original_inputs_unchanged'],'positive diagnostic completed')
    need(all(summary[k] is False for k in ('routing_accepted','comparison_eligible','applied','whole_body_certificate_qualified','proposal_scene_qualified','physical_electrical_validation')),'limited repair-only claims')
    need(summary['selected']=='candidate-01' and len(summary['trials'])==1,'first bounded proposal selected')
    trial=summary['trials'][0];directory=POSITIVE/'candidate-01'
    need(p.sha(POSITIVE/'protocol.json')==summary['protocol_sha256'],'protocol hash')
    need(p.sha(directory/'diagnostic-result.json')==summary['selected_trial_receipt_sha256'] and read(directory/'diagnostic-result.json')==trial,'selected trial receipt exact')
    source=Path(protocol['source']);candidate=Path(trial['candidate']);original=p.preflight(source);base_receipt=read(BASE/'result.json')
    need(source==Path(base_receipt['source']) and candidate==directory/'candidate'/source.name,'source/candidate path ownership')
    hashes=protocol['source_hashes'];expected=dict(hashes);expected[source.name]=GOOD_HASH
    need(p.tree_hash(source.parent)==hashes==base_receipt['source_hashes'],'original full source current')
    need(p.tree_hash(POSITIVE/'snapshot')==hashes==p.tree_hash(BASE/'snapshot'),'positive/base full original snapshots')
    need(p.tree_hash(candidate.parent)==expected and p.sha(candidate)==GOOD_HASH==trial['candidate_sha256']==trial['proposed_candidate_sha256'],'positive complete project hash')
    need(protocol['candidate_sha256']==BASE_HASH==p.sha(BASE/'candidate'/source.name),'failed base candidate current')
    postrun_code_changes={}
    for path,digest in protocol['input_files'].items():
        relative=Path(path).relative_to(ROOT)
        if relative.parts[0]=='autorouter' and p.sha(path)!=digest:
            postrun_code_changes[str(relative)]={'during_run':digest,'current':p.sha(path)}
        else:need(p.sha(path)==digest,'watched file '+str(relative))
    for path,inventory in protocol['input_trees'].items():need(p.tree_hash(path)==inventory,'watched complete tree '+str(Path(path).relative_to(ROOT)))
    need(p.sha(POSITIVE/'driver.py')=='739570e78561ecd4f6bb8e71ab8192041266410d29f685cbc1abd8758e2f5bd8','reviewed driver version')
    for relative,digest in protocol['tools']['implementation_sha256'].items():
        need(p.sha(POSITIVE/'code'/relative)==digest,'frozen code '+relative)
        blob=subprocess.run(['git','-C',str(ROOT),'show',protocol['tools']['git_head']+':'+relative],check=True,capture_output=True).stdout
        need(hashlib.sha256(blob).hexdigest()==digest,'positive code exact recorded commit '+relative)
    # Current development can continue after a completed experiment. Require the
    # actual validation machinery used by this audit/control to retain semantics.
    for relative in ('autorouter/config.py','autorouter/native.py','autorouter/runner.py','autorouter/sexpr.py','autorouter/netclass.py'):
        need(p.sha(ROOT/relative)==protocol['tools']['implementation_sha256'][relative],'current validation dependency unchanged '+relative)
    names={'Job','sha','tree_hash','preflight','immutable','routes','locked','netclass_policy','convert_route_nets','transplant_routes','transplant_fill','parse_report','native_rejection_reasons','native_accepted','verify_candidate_files','audit_route_dimensions','audit_candidate_netclasses','validate_candidate'}
    functions=lambda path:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(path).read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names}
    need(functions(ROOT/'autorouter/pipeline.py')==functions(POSITIVE/'code/autorouter/pipeline.py'),'current native-validation function semantics match frozen run')
    constants={'ROUTES','DERIVED_ZONE','CRITICAL_CHECKS','KNOWN_CHECKS','CRITICAL_FINDINGS'}
    assignments=lambda path:{n.targets[0].id:ast.dump(n,include_attributes=False) for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constants}
    need(assignments(ROOT/'autorouter/pipeline.py')==assignments(POSITIVE/'code/autorouter/pipeline.py'),'current preservation/native-policy constants match frozen run')
    for path,digest in protocol['tools']['files'].items():need(p.sha(path)==digest,'pinned actual tool '+Path(path).name)
    tree=sx.read(candidate);base=sx.read(BASE/'candidate'/source.name)
    need(p.immutable(tree)==p.immutable(original)==p.immutable(base),'original immutable geometry')
    protected=[r for r in p.routes(original) if p.locked(r)]
    need(all(r in p.routes(tree) for r in protected),'protected source routing')
    proposal=protocol['proposals'][0]
    added=['segment',['start',*map(mm,proposal['start_nm'])],['end',*map(mm,proposal['end_nm'])],['width',mm(proposal['width_nm'])],['layer','"'+proposal['layer']+'"'],['net',str(proposal['net_code'])],['uuid','"'+UID+'"']]
    need(trial['added_track_uuid']==UID and trial['proposal_index']==0 and p.routes(tree)==p.routes(base)+[added],'exactly one declared generated bridge')
    removed=copy.deepcopy(tree);removed.remove(added)
    removed_sha=hashlib.sha256((sx.dump(removed)+'\n').encode()).hexdigest()
    need(removed==base and removed_sha==BASE_HASH,'exact bridge removal recreates original failed bytes and every fill')
    for label in ('refill-drc','final-drc'):
        raw=p.parse_report(directory/(label+'.json'),source.name)
        need(p.native_accepted(raw) and all(raw[k]==0 for k in ('opens','blocking','warnings','exclusions')),label+' clean actual native report')
    native=p.parse_report(directory/'final-drc.json',source.name)
    need(native==trial['native'] and p.sha(directory/'final-drc.json')==trial['native_report_sha256']==REPORT_HASH,'positive raw report bound')
    binding=read(directory/'final-drc-binding.json');input_dir=directory/'final-drc-input'
    need(binding['source']==str(candidate) and binding['input']==str(input_dir/source.name) and binding['saved'] is False,'final native input paths')
    need(binding['before']==expected and p.tree_hash(input_dir)==binding['after'] and all(binding['after'].get(k)==h for k,h in expected.items()),'final exact board/rules/native input trees')
    mapping=read(directory/'final-netclasses.json');audit=p.audit_candidate_netclasses(candidate,protected,mapping)
    audit['native_map_file_sha256']=p.sha(directory/'final-netclasses.json')
    need(audit==read(directory/'final-netclass-audit.json') and audit['native_map_file_sha256']==trial['final_netclass_map_sha256'],'fresh strict native class/route dimensions')
    need(next(x for x in mapping['nets'] if x['netcode']==100)['width_nm']==proposal['width_nm']==500000,'original Power class width')
    for step in trial['steps']:
        retained=read(directory/(step['name']+'-process.json'))
        need(all(step.get(k)==v for k,v in retained.items()),'step/process '+step['name'])
        need(step['status']=='success' and step['exit_code']==0 and step['cleanup_complete'] and not step['log_truncated'],'native clean process '+step['name'])
        need(step['argv'][:3]==['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)'] and step['cwd']==str(directory),'owned network-denied command '+step['name'])
        need(Path(step['log']).stat().st_size==step['log_bytes'],'native log size '+step['name'])
    final_step=trial['steps'][-1]
    need(final_step['argv'][3:]==[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(directory/'final-drc.json'),str(input_dir/source.name)] and final_step['validated_input_sha256']==GOOD_HASH,'exact final DRC flags and candidate binding')
    baseline=p.parse_report(BASE/'final-drc.json',source.name)
    need(baseline==base_receipt['native'] and p.sha(BASE/'final-drc.json')==base_receipt['native_report_sha256'],'negative baseline report bound')
    errors=[f for f in baseline['findings'] if f['severity']=='error']
    need(baseline['opens']==baseline['warnings']==baseline['exclusions']==0 and baseline['blocking']==1 and len(errors)==1 and errors[0]['type']=='starved_thermal' and {i['uuid'] for i in errors[0]['items']}=={PAD,ZONE},'negative expected exact thermal finding')
    proof_root=ROOT/'.runs/review-thermal-graph003-001';proof=read(proof_root/'audit.json');proof_manifest=read(proof_root/'sha256.json')
    need(p.sha(proof_root/'audit.json')==proof_manifest['audit.json'] and proof['passed'] and proof['check_count']==1313,'independent geometric certificate audit')
    need(proof['geometry_sha256']==p.sha(POSITIVE/'evidence/geometry.json') and proof['proposals_sha256']==p.sha(POSITIVE/'evidence/proposals.json'),'same independently audited geometry and proposals')
    need(summary['wall_seconds']<=60 and summary['total_cpu_seconds']<=60 and sum(s['wall_seconds'] for s in trial['steps'])<=summary['wall_seconds'] and sum(s['cpu_seconds']+s['monitor_cpu_seconds'] for s in trial['steps'])<=summary['total_cpu_seconds'],'repair-only bounded wall/CPU consistent')
    length=lambda t:sum(math.dist(list(map(float,sx.one(r,'start')[1:3])),list(map(float,sx.one(r,'end')[1:3]))) for r in p.routes(t) if r[0]=='segment')
    need(not sx.children(tree,'arc') and abs((length(tree)-length(base))-proposal['length_nm']/1e6)<1e-8,'exact bridge length delta')
    return {'passed':True,'check_count':len(checks),'checks':checks,'native_executed_by_reviewer':False,
            'source':str(source),'source_hashes':hashes,'candidate':str(candidate),'candidate_sha256':GOOD_HASH,
            'native_report_sha256':REPORT_HASH,'removed_uuid':UID,'exact_removed_sha256':removed_sha,
            'native':native,'baseline_native':baseline,'wall_seconds':summary['wall_seconds'],'total_cpu_seconds':summary['total_cpu_seconds'],
            'bridge_endpoints_nm':[proposal['start_nm'],proposal['end_nm']],'bridge_length_mm':proposal['length_nm']/1e6,
            'analytic_track_length_mm':length(tree),'vias':len(sx.children(tree,'via')),
            'positive_inventory':p.tree_hash(POSITIVE),'tools':protocol['tools'],'postrun_code_changes':postrun_code_changes,
            'scope':'positive repair-only native validation plus unchanged independently audited path witnesses; not accepted end-to-end C routing'}
if __name__=='__main__':
    report=verify_positive();report['audit_script_sha256']=p.sha(__file__)
    (Path(__file__).parent/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('passed','check_count','candidate_sha256','exact_removed_sha256','wall_seconds','total_cpu_seconds','analytic_track_length_mm','vias')}))
