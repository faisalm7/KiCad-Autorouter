"""Read retained installed controls with installed shared validators; no workers."""
import time,resource
START=time.monotonic();u=resource.getrusage(resource.RUSAGE_SELF);CPU0=u.ru_utime+u.ru_stime
from pathlib import Path
import json,subprocess,sys
PRIMARY=Path(__file__).resolve().parents[2]
INSTALLED=PRIMARY/'.runs/installation-021-current965/checkout'
sys.path.insert(0,str(INSTALLED));sys.dont_write_bytecode=True
def forbidden(*args,**kwargs):raise AssertionError('readback forbids Native/JVM/test/GET/Git subprocess')
subprocess.run=forbidden;subprocess.Popen=forbidden
from autorouter import pipeline as p,floor_route as f,sexpr as sx,placement_clearance as pc,native_edge as edge,config as c
OUT=Path(__file__).resolve().parent;BASE=INSTALLED/'.runs/installed-edge-controls-001'
read=f.read_json;protocol=read(BASE/'protocol.json');controls=read(BASE/'result.json')
source=BASE/'source/smoke.kicad_pcb';original=sx.read(source)
before=pc.inventory(BASE,max_bytes=16*1024**2,max_files=512,max_entries=1024,with_directories=True)
smoke=INSTALLED/'.runs/install-native-smoke/candidate';smoke_before=p.tree_hash(smoke)
pins={str(path):p.sha(path) for path in (BASE/'result.json',BASE/'protocol.json',Path(__file__).resolve())}
checks=[];failures=[]
def stable():
    if (pc.inventory(BASE,max_bytes=16*1024**2,max_files=512,max_entries=1024,with_directories=True)!=before
            or p.tree_hash(smoke)!=smoke_before or smoke_before!=protocol['base']
            or p.tree_hash(source.parent)!=protocol['source']):raise p.Rejected('installed controls/source/smoke changed')
    for path,digest in pins.items():
        if p.sha(Path(path))!=digest:raise p.Rejected('installed retained input changed')
    for name,digest in protocol['tools']['implementation_sha256'].items():
        if p.sha(INSTALLED/name)!=digest:raise p.Rejected('installed runtime changed')
    for name,digest in protocol['tools']['files'].items():
        if p.sha(Path(name))!=digest:raise p.Rejected('installed/native tool bytes changed')
try:
    assert c.ROOT==INSTALLED and Path(sys.prefix).resolve()==INSTALLED/'.venv'
    modules=(p,f,sx,pc,edge,c)
    assert all(Path(module.__file__).resolve().is_relative_to(INSTALLED) for module in modules)
    assert (INSTALLED/'.git/HEAD').read_text().strip()==protocol['tools']['git_head']=='965796670d2835e185938d52ef694333e5752356'
    assert p.sha(INSTALLED/'scripts/native_edge_controls.py')==protocol['controller_sha256']
    assert controls['protocol_sha256']==p.sha(BASE/'protocol.json') and controls['tools']==protocol['tools']
    assert controls['accepted'] is False and controls['all_passed'] is True
    assert protocol['cases']==['positive','edge_violation','rule_tamper']
    assert [row['case'] for row in controls['controls']]==protocol['cases']
    assert p.tree_hash(source.parent)==protocol['source'] and p.tree_hash(smoke)==protocol['base']
    context=edge.derive_context(pc.read_bytes(source),pc.read_bytes(source.with_suffix('.kicad_pro')))
    assert context['applicable'] is True and context['original_min_copper_edge_clearance_mm']=='0.3'
    protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
    for row in controls['controls']:
        folder=BASE/row['case'];assert read(folder/'control.json')==row
        candidate=folder/'candidate'/source.name;tree=sx.read(candidate)
        assert row['source_hashes']==protocol['source'] and row['passed'] is True
        assert p.immutable(tree)==p.immutable(original)
        assert all(route in p.routes(tree) for route in protected)
        assert all(route in p.routes(tree) for route in p.routes(original))
        item=dict(case=row['case'],immutable_original_design=True,protected_copper_exact=True,
            all_original_control_source_routes_retained=True,candidate_sha256=p.sha(candidate),workers=[])
        if row['case']!='rule_tamper':
            p.verify_candidate_files(candidate,protocol['source'],row['candidate_sha256'])
            before_final=dict(protocol['source']);before_final[source.name]=row['candidate_sha256']
            observed=f.check_drc_stage(folder,row,'final-drc',candidate,folder/'final-drc-input'/source.name,
                False,before_final,schematic_parity=False,sandboxed=False)
            assert observed==row['native']
            binding=read(folder/'refill-drc-binding.json')
            refill=f.check_drc_stage(folder,row,'refill-drc',folder/'refill'/source.name,folder/'refill'/source.name,
                True,binding['before'],schematic_parity=False,sandboxed=False)
            assert p.native_accepted(observed)==row['accepted']==row['expected_accepted']
            counts={key:observed[key] for key in ('opens','blocking','warnings','exclusions')}
            assert counts==dict(opens=0,blocking=0 if row['case']=='positive' else 1,warnings=0,exclusions=0)
            if row['case']=='edge_violation':
                assert len(observed['findings'])==1 and observed['findings'][0]['type']=='copper_edge_clearance'
                assert '0.3000 mm; actual 0.2500 mm' in observed['findings'][0]['description']
            item.update(original_companions_exact=True,native_counts=counts,
                native_report_sha256=p.sha(folder/'final-drc.json'),actual_refill_native_counts={key:refill[key]for key in ('opens','blocking','warnings','exclusions')})
        else:
            rejection=None
            try:p.verify_candidate_files(candidate,protocol['source'],p.sha(candidate))
            except p.Rejected as exc:rejection=type(exc).__name__+': '+str(exc)
            assert rejection==row['reason']=='Rejected: candidate project/rules/file set changed'
            before_relaxed=p.tree_hash(candidate.parent)
            diagnostic=f.check_drc_stage(folder,row,'relaxed-rule-diagnostic',candidate,
                folder/'relaxed-rule-diagnostic-input'/source.name,False,before_relaxed,
                schematic_parity=False,sandboxed=False)
            assert diagnostic==row['relaxed_rule_diagnostic_native'] and diagnostic['blocking']==0
            project=read(candidate.with_suffix('.kicad_pro'))
            assert project['board']['design_settings']['rules']['min_copper_edge_clearance']==0
            assert row['accepted'] is False and row['expected_accepted'] is False
            item.update(original_companion_rejection=rejection,relaxed_native_counts={key:diagnostic[key]for key in ('opens','blocking','warnings','exclusions')},
                relaxed_native_report_sha256=p.sha(folder/'relaxed-rule-diagnostic.json'),relaxed_native_not_acceptance=True)
        for step in row['steps']:
            process=f.process_check(folder,row,step['name'],step['argv'],allowed=(0,5))
            assert process['cleanup_complete'] is True and process['log_truncated'] is False
            item['workers'].append(dict(name=step['name'],process_sha256=p.sha(folder/(step['name']+'-process.json')),
                log_sha256=p.sha(Path(step['log'])),exit_code=step['exit_code'],cleanup_complete=True))
        checks.append(item)
    stable()
except BaseException as exc:failures.append(dict(type=type(exc).__name__,error=str(exc)))
u=resource.getrusage(resource.RUSAGE_SELF)
report=dict(schema=1,kind='actual installed021 edge native controls independent shared readback',accepted=False,
    passed=not failures,checks=checks,failures=failures,new_native_execution=False,new_engine_execution=False,new_tests=False,new_network_requests=0,
    installed_python=str(Path(sys.executable)),installed_prefix=str(Path(sys.prefix)),
    module_paths={module.__name__:str(Path(module.__file__).resolve())for module in modules},source_sha256=protocol['source'],
    prior_smoke_unchanged=smoke_before==protocol['base'],input_sha256=pins,tools=protocol['tools'],
    cost=dict(active_wall_seconds=time.monotonic()-START,active_full_cpu_seconds=u.ru_utime+u.ru_stime-CPU0,
        bootstrap_emission_allowance_seconds=2),
    limitations=['Actual PCB-only validation controls, not new routing, full schematic, GUI, physical/electrical or broad quality proof.',
        'Rule-tamper native report used intentionally relaxed rules; its zero findings are not acceptance. Original companions reject.',
        'Only retained control/smoke/runtime/tool evidence read; no entire historical source inventory was repeated.'])
(OUT/'result.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
if not failures:stable()
print(json.dumps({key:report[key]for key in ('passed','failures','cost','prior_smoke_unchanged')}))
raise SystemExit(0 if report['passed'] else 2)
