"""DRAFT ONLY: freeze/run eleven unchanged tasks plus one EEPROM Improve90.

No future HEAD, manifest or result is assumed. Freeze requires actual successful
runtime059 preparation/full211 hashes. Batch execution is a separate explicit
phase requiring the resulting frozen hash; never resume or retry a failed batch.
"""
from pathlib import Path
import argparse, ast, copy, fcntl, json, os, resource, shutil, stat, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv,gui
from autorouter.runner import run
from scripts import freeze_current_comparison as shared
RUNTIME=ROOT/'.runs/runtime-directory-059/runtime';BASE=ROOT/'.runs/runtime059-native-qualification-001'
MANIFEST=RUNTIME/'runtime-distribution.json';PREPARATION=RUNTIME.parent/'preparation.json'
FULL=ROOT/'.runs/full-integration-211/execution.json';SELF=Path(__file__).resolve()
PRIOR=ROOT/'.runs/runtime058-native-qualification-001/frozen.json'
NATURAL=ROOT/'.runs/runtime058-natural-expiry-001/protocol.json'
ENCLOSER=ROOT/'.runs/enclose-runtime044-workflow-001.py';DRIVER=ROOT/'scripts/qualify_runtime_workflow.py'
FIXED={
    PRIOR:'76b46e1b546090d4d2e54f98a28a1b97357d42aceaab118c2f5cb37afed41d8c',
    NATURAL:'5b8a83dd407087e4fa90f744837a162dfe43a6996df67e01d8e92a4ef2b7da03',
    ENCLOSER:'91cd6fb9e234132489754e667e54c70af3ffbd239d67616c2e4e1da0a5904a1a',
    DRIVER:'0b1a3bc61e576d6475a4c922a7727b7831ccf28f3e0a9d2d80b557e3c1964034',
    ROOT/'scripts/freeze_current_comparison.py':'9729687563f9dd23fcee7b85d1cb4835dd57f436a23626d7f07d93a9d07033bd',
    ROOT/'.runs/freeze-runtime058-native-qualification-001.py':'c69c66e8d20f567e5e346fc5ddaadc89adc17741a66d936b9a2eb1d68a4ba53e',
    ROOT/'.runs/qualify-runtime058-native-batch-001.py':'4b317c6c51946a042d5510ed71b6321cb72166927c234b8745ae1908fecbd851',
}
SCOPE='Current059 six-stage Request/Workflow/CliJob/CLI with own final Native/fullSCH/original PRO, source/Default/field/PRL/protected and fresh export/readback proofs. Eleven fixed058 source/settings/cost/scope/budget controls plus one unchanged exposed EEPROM Improve90; no old candidate or outcome transfer. Only return publication session/accounting, canonical-result identity and40s return-reserve repair are under qualification.900s complete batch wall/fullCPU, unchanged240s shared acceptance/255s child/270s dispatch caps. No actual GUI, comparison superiority, new family, human/electrical, cleanOS/Windows or release claim.'
POLICY=dict(historical_return_reserve_seconds=25,current_return_reserve_seconds=40,normal90_work_boundary_seconds=50,
    qualification='All twelve require the unchanged shared six-stage pass. A pass alone does not establish actual optional-trial expiry, pending proposals, at least one actual trial, exact incumbent return or literal50s observation. Inspect own completed trial/checkpoint/clock evidence separately; do not infer strict expiry from an admission stop before50s. No fake clock, increased global budget, retry, prior candidate adoption or semantic acceptance cache.')
def sha_check(path,pin):
    assert type(pin) is str and pv._DIGEST.fullmatch(pin) and p.sha(path)==pin,str(path)
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
def freeze(args):
    self_pin=p.sha(SELF);pins=dict(FIXED);pins.update({SELF:self_pin,PREPARATION:args.preparation_sha256,FULL:args.full211_sha256})
    for path,pin in pins.items():sha_check(path,pin)
    assert not os.path.lexists(BASE) and shutil.disk_usage(ROOT).free>4*1024**3
    prepared=f.read_json(PREPARATION);full=f.read_json(FULL);head=prepared['source_head']
    assert type(head) is str and len(head)==40 and pv.git_head(ROOT)==head
    assert prepared['prepared'] is True and prepared['runtime']==str(RUNTIME)
    assert prepared['full211_execution_sha256']==args.full211_sha256
    assert full['passed'] is True and full['sources_unchanged'] is True
    assert full['process']['status']=='success' and full['process']['exit_code']==0
    assert full['process']['cleanup_complete'] is True and full['process']['log_truncated'] is False
    sha_check(Path(full['process']['log']),full['log_sha256']);pins[Path(full['process']['log'])]=full['log_sha256']
    manifest_pin=prepared['manifest_sha256'];sha_check(MANIFEST,manifest_pin);pins[MANIFEST]=manifest_pin
    # Read the actual immutable declaration, without importing the new runtime.
    declaration=RUNTIME/'autorouter/_improve_context.py'
    reserve=[ast.literal_eval(n.value) for n in ast.parse(declaration.read_bytes()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RESERVE_SECONDS' for t in n.targets)]
    assert reserve==[40];pins[declaration]=p.sha(declaration)
    prior=f.read_json(PRIOR);natural=f.read_json(NATURAL)
    assert len(prior['protocols'])==11 and prior['source_head']=='8f5e96b88dd22cd25919bb71ce47711612994efa'
    assert natural['method']=='improve' and natural['settings']['seconds']==90 and natural['budgets']==dict(route=90,export=90)
    assert natural['expected_counts'] is None and natural['warning_policy']=='retain_all_native_findings'
    assert natural['expected_exclusions']==0 and natural['expected_protected_count']==0 and len(natural['source_hashes'])==3
    templates=[]
    for row in prior['protocols']:
        path=Path(row['protocol']);sha_check(path,row['protocol_sha256']);pins[path]=row['protocol_sha256']
        plan=f.read_json(path);assert plan['source_head']==prior['source_head'] and plan['case']==row['case'] and plan['method']==row['method']
        templates.append((plan,row['protocol_sha256']))
    # Copy only source/task fields; historical25s/65s criteria and proofs stay historical.
    extra={key:copy.deepcopy(natural[key]) for key in ('schema','method','source','source_hashes','source_rights','source_split','settings','budgets','expected_counts','expected_exclusions','warning_policy','expected_protected_count')}
    extra.update(case='improve-eeprom90-return',qualification_role='One normal CLI Improve90 return repair regression on unchanged exposed EEPROM; no literal expiry or no-better claim is presumed.')
    templates.append((extra,FIXED[NATURAL]));assert len({plan['case'] for plan,_ in templates})==12
    def fresh():
        for path,pin in pins.items():sha_check(path,pin)
        assert pv.git_head(ROOT)==head
        for plan,_ in templates:assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
    fresh();BASE.mkdir(mode=0o700)
    query,query_pins=shared.query_runtime(RUNTIME,BASE);pins.update({Path(path):pin for path,pin in query_pins.items()});tools=query['tools']
    assert query['runtime']==str(RUNTIME) and query['prefix']==str(RUNTIME/'.venv')
    assert tools['source_provenance']['git_head']==head and tools['source_provenance']['manifest_sha256']==manifest_pin
    doctor=run([*f.SANDBOX,str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter','doctor'],cwd=RUNTIME,env=gui.child_environment(),log=BASE/'doctor.json',timeout=90,max_log_bytes=512*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=128*1024**2)
    p.save_json(BASE/'doctor-process.json',doctor)
    assert doctor['status']=='success' and doctor['exit_code']==0 and doctor['cleanup_complete'] is True and doctor['log_truncated'] is False and f.read_json(BASE/'doctor.json')['ready'] is True
    pins[BASE/'doctor.json']=p.sha(BASE/'doctor.json');pins[BASE/'doctor-process.json']=p.sha(BASE/'doctor-process.json')
    rows=[]
    for template,old_pin in templates:
        fresh();plan=copy.deepcopy(template);name=plan['case'];folder=BASE/name;folder.mkdir(mode=0o700)
        p.save_json(folder/'settings.json',plan['settings']);output=RUNTIME/'.runs'/(name+'-001');assert not os.path.lexists(output)
        plan.update(kind='runtime059-six-stage-native-and-return-CLI',runtime=str(RUNTIME),runtime_manifest_sha256=manifest_pin,source_head=head,output=str(output),tools=tools,settings_sha256=p.sha(folder/'settings.json'),driver_sha256=FIXED[DRIVER],enclosure_sha256=FIXED[ENCLOSER],source_protocol_sha256=old_pin,return_policy=POLICY,scope=SCOPE)
        if name!='improve-eeprom90-return':plan['qualification_role']='Unchanged fixed058 task definition, rebound to current059 return/canonical repair; no source/constraint/profile/scoring/budget tuning.'
        for key in ('method','source','source_hashes','settings','budgets','expected_counts','expected_protected_count'):assert plan[key]==template[key]
        path=folder/'protocol.json';p.save_json(path,plan);pins[path]=p.sha(path);pins[folder/'settings.json']=p.sha(folder/'settings.json')
        rows.append(dict(case=name,method=plan['method'],protocol=str(path),protocol_sha256=pins[path]))
    fresh()
    frozen=dict(schema=1,source_head=head,runtime=str(RUNTIME),runtime_manifest_sha256=manifest_pin,controller_sha256=self_pin,enclosure_sha256=FIXED[ENCLOSER],driver_sha256=FIXED[DRIVER],prior_frozen_sha256=FIXED[PRIOR],natural90_source_protocol_sha256=FIXED[NATURAL],prerequisite_sha256={str(path):pin for path,pin in pins.items()},protocols=rows,executed=False,whole_batch_seconds=900,return_policy=POLICY,scope=SCOPE)
    p.save_json(BASE/'frozen.json',frozen);fresh()
    print(json.dumps(dict(cases=[r['case'] for r in rows],frozen_sha256=p.sha(BASE/'frozen.json'),source_head=head,manifest_sha256=manifest_pin,executed=False)))
def batch(args):
    start=time.monotonic();cpu0=cpu();path=BASE/'frozen.json';sha_check(path,args.frozen_sha256);frozen=f.read_json(path)
    assert frozen['controller_sha256']==p.sha(SELF) and frozen['runtime']==str(RUNTIME) and len(frozen['protocols'])==12
    assert frozen['whole_batch_seconds']==900 and frozen['return_policy']==POLICY
    assert not os.path.lexists(BASE/'batch-result.json') and shutil.disk_usage(ROOT).free>4*1024**3
    def fresh():
        sha_check(path,args.frozen_sha256)
        for name,pin in frozen['prerequisite_sha256'].items():sha_check(Path(name),pin)
        assert pv.git_head(ROOT)==frozen['source_head']
    fresh();rows=[];cpu_complete=True
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lane:
        info=os.fstat(lane.fileno());assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_uid==os.getuid()
        fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for row in frozen['protocols']:
            left=900-max(time.monotonic()-start,cpu()-cpu0)
            if left<=0:break
            fresh();protocol=Path(row['protocol']);sha_check(protocol,row['protocol_sha256']);plan=f.read_json(protocol);folder=protocol.parent
            assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
            assert not os.path.lexists(Path(plan['output'])) and not os.path.lexists(folder/'execution.json') and not os.path.lexists(folder/'batch-process.json')
            process=run(['/usr/bin/time','-lp',str(ROOT/'.venv/bin/python'),'-B',str(ENCLOSER),'--protocol',str(protocol)],cwd=folder,env=gui.child_environment(),log=folder/'complete-command-and-time.log',timeout=min(270,left),max_log_bytes=128*1024,max_workdir_bytes=4*1024**2,max_group_rss_bytes=4*1024**3)
            p.save_json(folder/'batch-process.json',process);completed=f.read_json(folder/'execution.json') if (folder/'execution.json').is_file() else None
            passed=bool(completed and completed['controls_passed'] and completed['workflow_delivered'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
            # A killed time wrapper may lack worker rusage: never call that zero/full CPU.
            if process['status']!='success' or process['exit_code']<0:cpu_complete=False
            rows.append(dict(case=row['case'],status='passed' if passed else 'failed',passed=passed,execution_sha256=p.sha(folder/'execution.json') if completed else None,process_sha256=p.sha(folder/'batch-process.json'),complete_log_sha256=p.sha(folder/'complete-command-and-time.log')))
            print(json.dumps(rows[-1]),flush=True)
            fresh()
            if not passed:break
    completed_count=len(rows);rows.extend(dict(case=row['case'],status='unstarted',passed=False) for row in frozen['protocols'][completed_count:])
    wall=time.monotonic()-start;measured_cpu=cpu()-cpu0
    passed=completed_count==12 and all(row['passed'] for row in rows) and cpu_complete and max(wall,measured_cpu)<=900
    record=dict(schema=1,kind='twelve-fixed-current059-native-return-workflow-dispatch-v1',passed=passed,rows=rows,completed_cases=completed_count,unstarted_cases=12-completed_count,wall_seconds=wall,full_CPU_seconds=measured_cpu if cpu_complete else None,reported_waited_CPU_seconds=measured_cpu,full_CPU_complete=cpu_complete,frozen_sha256=args.frozen_sha256,controller_sha256=p.sha(SELF),accepted=False,project_complete=False,actual_GUI=False,human_review=False,return_policy=POLICY,scope=SCOPE,accounting='Complete external batch /usr/bin/time still required; nested case/method samples overlap and must not be added. If a time wrapper is killed, full worker CPU is unknown additional, not zero. No retry, old outcome stitching, actual GUI, literal expiry or general performance claim.')
    fresh();p.save_json(BASE/'batch-result.json',record);fresh();print(json.dumps(dict(passed=passed,completed_cases=completed_count,unstarted_cases=12-completed_count)))
    raise SystemExit(0 if passed else 2)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('freeze','batch'),required=True)
    ap.add_argument('--preparation-sha256');ap.add_argument('--full211-sha256');ap.add_argument('--frozen-sha256');args=ap.parse_args()
    if args.phase=='freeze':
        assert args.preparation_sha256 and args.full211_sha256 and args.frozen_sha256 is None
        freeze(args)
    else:
        assert args.frozen_sha256 and args.preparation_sha256 is None and args.full211_sha256 is None
        batch(args)
