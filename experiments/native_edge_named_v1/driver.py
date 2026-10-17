"""Finite phase-separated named-edge importer prerequisite; lead execution only.

SPDX-License-Identifier: GPL-3.0-or-later
No router is called. Pure source freeze and protocol freeze never start workers.
"""
import time
START = time.monotonic()
import resource

def cpu():
    return sum(r.ru_utime + r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import stat
import signal
from functools import wraps
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, floor_route as f, handoff as h
from autorouter import placement_clearance as pc, native_edge as edge, netclass as nc, adapter as a, sexpr as sx, padless_alias as alias
from autorouter.runner import run
from experiments.native_edge_named_v1 import fixture

BASE = ROOT / '.runs/native-edge-named-preparation-001'
PLAN = BASE / 'source-plan-003.json'
PRIOR_PLAN = BASE / 'source-plan-002.json'
PRIOR_PLAN_PIN = 'aa894a2385930c59f2dde55da4f01175391ef89b5aed661e62a4524875795b3b'
PREPARATION_PIN = '6580eaf8f83a7a60d007f6c8898b07260b3671137cd32c8ce13acedcc7f6cad5'
PURE_FREEZE_CORRECTION_FILES = frozenset((
    'experiments/native_edge_named_v1/driver.py',
    'experiments/native_edge_named_v1/test_controller.py'))
HERE = Path(__file__).resolve().parent
RETAINED = ROOT / '.runs/four-cu-class-native-001/native1000'
CASES = ('literal300', 'parent300', 'underscore300', 'literal250')
CAP = 60.0
LIMIT = 32 * 1024**2
FIXED_RETAINED = {
 'result.json': 'c2081d8692c53c5fbf5ebbf2adfb0149e68239583e34b9a13814e4820941e735',
 'route/result.json': '6d8ebfb93cf5d719400203e2c8af0696f1f297d7d65f9f333708f07655e38bf2',
 'route/native.dsn': '19d0e812dbc9bec9824c05910556f7a9a9b25ac041c4eabb4997f8351bb29e84',
 'route/export-netclasses.json': '58ac066f1d3f210eb5441be808293ce8039f7b0770791de815f12343b9285083',
 'route/export-process.json': 'a19e9e104f170d8e0973a4f19767c30dbe520239e9d7071793c6dd1b77341937',
 'route/export.log': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
 'control-code/autorouter/native.py': 'd7e3140cee40d0a618c5c699cdada4d833a04d76f8fe06e8b823b4f490f2e9b6',
}


def require(value, reason):
    if not value: raise p.Rejected(reason)


def read(path): return pc.read_bytes(path, LIMIT)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def inventory(path): return pc.inventory(path, max_bytes=LIMIT, max_files=512, max_entries=1024)
def write(path, raw):
    require(path.parent.is_dir(), 'existing owned parent required')
    with path.open('xb') as stream: stream.write(raw)
def save(path, value): write(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())
def pins(paths): return {str(path.relative_to(ROOT)): digest(read(path)) for path in paths}
def checked_pins(values):
    for relative, pin in values.items():
        path = ROOT / relative
        require(path.is_relative_to(ROOT) and '..' not in path.parts and digest(read(path)) == pin, 'frozen file changed: ' + relative)
def code_pins():
    paths = list((ROOT / 'autorouter').glob('*.py')) + list(HERE.glob('*.py')) + list(HERE.glob('*.java'))
    paths += [ROOT / 'toolchain.lock.json', ROOT / 'experiments/native_schematic_transport_v1/fixture.py']
    return pins(sorted(paths))
def tools_pins():
    lock = f.read_json(ROOT / 'toolchain.lock.json')['tools']; result = {}
    for pin in lock.values():
        path = c.resolve_tool_path(pin['path'])
        require(p.sha(path) == pin['sha256'], 'pinned dependency changed')
        result[str(path)] = pin['sha256']
    require(result.get(str(c.JAR)) == c.JAR_SHA256, 'pinned project JAR required')
    return result

def check_source_plan(plan):
    require(plan.get('schema') == 1 and plan.get('kind') == 'named-edge-source-plan-v1'
            and plan.get('production_admitted') is False and plan.get('accepted') is False, 'source plan scope changed')
    require(code_pins() == plan['code_sha256'] and tools_pins() == plan['tool_sha256'], 'source plan code/tool pins changed')
    checked_pins(plan['retained_sha256'])
    for name in fixture.CASES:
        source = BASE / 'sources' / name
        require(inventory(source) == plan['sources'][name], 'owned source packet changed')
        require({key: digest(raw) for key, raw in fixture.files(name).items()} == plan['sources'][name], 'owned source recipe changed')
    require(check_retained() == plan['retained_control'], 'retained original proof changed')
    if 'reused_native_preparation' in plan:
        _, link = check_preparation_reuse(plan)
        require(link == plan['reused_native_preparation'], 'reused Native preparation provenance changed')


def export_proof(directory, data, board, dsn, mapping, *, historical_source=None, sandboxed=True):
    raw = read(historical_source or board); project_raw = read((historical_source or board).with_suffix('.kicad_pro'))
    native = f.read_json(mapping); proof_path = alias.artifact_paths(dsn)['proof']; proof = f.read_json(proof_path)
    require(native['source'] == str(board) and native['board_sha256'] == digest(raw)
            and native['project_sha256'] == digest(project_raw) and native['board_saved'] is False, 'Native export input/class map binding differs')
    argv = [str(c.PYTHON), str(ROOT / 'autorouter/native.py'), 'export', str(board), str(dsn), str(mapping)]
    process = f.process_check(directory, data, 'export', [*f.SANDBOX, *argv] if sandboxed else argv)
    log = directory / 'export.log'
    require(process.get('log') == str(log) and process.get('log_bytes') == len(read(log))
            and process.get('log_truncated') is False and process.get('signal_cancellation_enabled') is True, 'export log/lifecycle differs')
    require(proof.get('policy') == alias.POLICY and proof.get('source') == str(board)
            and proof.get('output') == str(dsn) and proof.get('source_sha256') == digest(raw)
            and proof.get('project_sha256') == digest(project_raw) and proof.get('native_classmap') == native
            and proof.get('dsn_sha256') == digest(read(dsn)) and proof.get('board_saved') is False
            and proof.get('routing_accepted') is False and proof.get('zero_alias') is True
            and proof.get('observation') is None and proof.get('binding') == alias.plan(raw), 'Native exact zero-alias export proof differs')
    require(read(directory / proof['source_copy']) == raw, 'retained actual export source copy differs')
    alias.dsn_aliases(read(dsn), raw, proof['binding'])
    project = json.loads(project_raw)
    parent = edge._named_scope(project_raw)['source_policy'] == nc.PARENT_POLICY
    audited = nc.audit_dsn(dsn, native, project, parent_policy=parent)
    require(audited['passed'] is True and audited['routing_accepted'] is False, 'Native class transport not proven')
    return dict(dsn_sha256=digest(read(dsn)), map_sha256=digest(read(mapping)), source_sha256=digest(raw),
                project_sha256=digest(project_raw), alias_sha256=digest(read(proof_path)), class_audit=audited,
                process_sha256=digest(read(directory / 'export-process.json')), log_sha256=digest(read(log)))


def check_retained():
    checked_pins({str((RETAINED / name).relative_to(ROOT)): pin for name, pin in FIXED_RETAINED.items()})
    route = RETAINED / 'route'; data = f.read_json(route / 'result.json'); source = Path(data['source'])
    require(source == RETAINED / 'source/owned-four-copper-forced-inner.kicad_pcb'
            and inventory(source.parent) == data['source_hashes'], 'retained immutable original source differs')
    child = f.read_json(RETAINED / 'result.json')
    require(child.get('passed') is True and child.get('route_receipt_sha256') == digest(read(route / 'result.json'))
            and data.get('accepted') is True and data.get('native_dsn_sha256') == digest(read(route / 'native.dsn'))
            and data['tools']['implementation_sha256']['autorouter/native.py'] == FIXED_RETAINED['control-code/autorouter/native.py'], 'retained source/export provenance differs')
    # task.dsn subsequently receives adapter edits. Native exact bytes survive in
    # native.dsn; the alias/process record names historical task.dsn. Reuse that
    # proof without claiming a new Native operation or reading overwritten PCB.
    proof = export_proof(route, data, route / 'candidate' / source.name, route / 'task.dsn',
                         route / 'export-netclasses.json', historical_source=source, sandboxed=False)
    return dict(source=str(source), source_hashes=data['source_hashes'], export=proof,
                reused_actual_native=True, fresh_native_execution=False, full_candidate_revalidation=False)


def check_preparation_reuse(plan):
    """Replay the exact completed exports; only the pure freeze driver changed.

    No old receipt selects tools or excuses changed Native code, source packets,
    process evidence, alias observations or class semantics. The full runtime,
    Java observer, owned generator and lock pin populations must remain exact.
    """
    prior = frozen(PRIOR_PLAN, PRIOR_PLAN_PIN)
    require(prior.get('schema') == 1 and prior.get('kind') == 'named-edge-source-plan-v1'
            and prior.get('accepted') is False and prior.get('production_admitted') is False,
            'prior Native source plan scope differs')
    old, current = prior['code_sha256'], plan['code_sha256']
    require(set(old) == set(current), 'Native prerequisite code population changed')
    changed = sorted(name for name in old if old[name] != current[name])
    require(set(changed) <= PURE_FREEZE_CORRECTION_FILES,
            'only the pure freeze driver and its regression may change for export reuse')
    require(plan['sources'] == prior['sources'] and plan['tool_sha256'] == prior['tool_sha256']
            and plan['retained_sha256'] == prior['retained_sha256']
            and plan['retained_control'] == prior['retained_control'],
            'original source/tool/retained prerequisite changed')
    checked_pins({name: pin for name, pin in old.items() if name not in PURE_FREEZE_CORRECTION_FILES})
    prepared = frozen(BASE/'native-preparation/result.json', PREPARATION_PIN)
    require(prepared.get('schema') == 1 and prepared.get('kind') == 'named-edge-native-preparation-v1'
            and prepared.get('passed') is True and prepared.get('status') == 'completed'
            and prepared.get('accepted') is False and prepared.get('production_admitted') is False
            and prepared.get('routing_executed') is False and prepared.get('budget_seconds') == CAP
            and prepared.get('source_plan_sha256') == PRIOR_PLAN_PIN,
            'exact completed Native preparation required')
    require(all(type(prepared.get(key)) in (int, float) and 0 <= prepared[key] < CAP
                for key in ('wall_seconds', 'full_cpu_seconds')), 'Native preparation exceeded its budget')
    require(prepared['tools']['kicad'] == '10.0.0'
            and prepared['tools']['files'] == prior['tool_sha256']
            and prepared['tools']['implementation_sha256'] ==
                {name: pin for name, pin in old.items() if name.startswith('autorouter/')},
            'completed Native helper/tool provenance differs')
    require(len(prepared['rows']) == 3
            and [row['case'] for row in prepared['rows']] == list(fixture.CASES),
            'exact three completed Native exports required')
    proofs = {}
    for row in prepared['rows']:
        folder = BASE/'native-preparation'/row['case']
        board = next((BASE/'sources'/row['case']).glob('*.kicad_pcb'))
        require(inventory(board.parent) == prior['sources'][row['case']], 'completed export source packet changed')
        observed = export_proof(folder, row, board, folder/'native.dsn', folder/'native-netclasses.json')
        require(observed == row['proof'], 'completed Native export process/source/alias/class proof changed')
        proofs[row['case']] = observed
    return prepared, dict(prior_source_plan=str(PRIOR_PLAN), prior_source_plan_sha256=PRIOR_PLAN_PIN,
                         native_preparation=str(BASE/'native-preparation/result.json'),
                         native_preparation_sha256=PREPARATION_PIN,
                         native_preparation_material_sha256=inventory(BASE/'native-preparation'),
                         permitted_changed_pure_files=changed, export_proofs=proofs,
                         unchanged_all_runtime_helpers_observer_generator_lock_and_tools=True,
                         native_exports_reused=3, native_exports_rerun=False)


def source_freeze():
    require(not PLAN.exists() and not PLAN.is_symlink(), 'fresh source-plan003 required')
    h.real_path(BASE, existing=BASE.exists())
    BASE.mkdir(exist_ok=True); (BASE / 'sources').mkdir(exist_ok=True)
    result = dict(schema=1, kind='named-edge-source-plan-v1', accepted=False, production_admitted=False,
                  code_sha256=code_pins(), tool_sha256=tools_pins(), sources={}, retained_control=check_retained(),
                  native_exports_required=[], native_export_budget_seconds=CAP,
                  importer_budget_seconds=CAP, importer_loads=9, cases=list(CASES),
                  phase_separation='Native export preparation and importer execution separately frozen/costed. No routing, no product acceptance.')
    for name in fixture.CASES:
        folder = BASE / 'sources' / name; expected = fixture.files(name)
        if folder.exists():
            require(inventory(folder)=={key:digest(raw) for key,raw in expected.items()}, 'existing owned packet differs; preserve unfinished work')
        else:
            folder.mkdir()
            for key, raw in expected.items(): write(folder / key, raw)
        result['sources'][name] = inventory(folder)
    retained_paths = [RETAINED / path for path in FIXED_RETAINED]
    retained_paths += list((RETAINED / 'source').iterdir())
    retained_paths += [RETAINED / 'route/task.dsn', RETAINED / 'route/task.alias-export.json', RETAINED / 'route/task.alias-source.kicad_pcb']
    result['retained_sha256'] = pins(retained_paths)
    _, result['reused_native_preparation'] = check_preparation_reuse(result)
    check_source_plan(result)
    result.update(preparation_wall_seconds=time.monotonic()-START, preparation_full_cpu_seconds=cpu()-CPU0)
    draft=PRIOR_PLAN
    if draft.exists():result['supersedes_source_plan_after_pure_freeze_failure']=dict(path=str(draft),sha256=digest(read(draft)))
    save(PLAN, result)
    return dict(source_plan=str(PLAN), sha256=digest(read(PLAN)), workers_executed=False)


def remaining(): return min(CAP - (time.monotonic()-START), CAP - (cpu()-CPU0))
def lane():
    path = ROOT / '.runs/quality-experiment.lock'
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    handle = os.fdopen(fd, 'r+'); info = os.fstat(handle.fileno())
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'ordinary existing shared lane lock required')
    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return handle

def frozen(path, pin):
    require(type(pin) is str and len(pin) == 64 and digest(read(path)) == pin, 'explicit exact frozen phase digest required')
    return f.read_json(path)


def cancellable_phase(action):
    # Same temporary whole-operation handlers as pipeline.route; runner.run
    # temporarily owns its active child and restores these handlers on return.
    @wraps(action)
    def guarded(*args, **kwargs):
        def interrupted(*_): raise KeyboardInterrupt
        previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        try:
            for sig in previous:signal.signal(sig,interrupted)
            return action(*args,**kwargs)
        finally:
            for sig,handler in previous.items():signal.signal(sig,handler)
    return guarded


@cancellable_phase
def prepare_native(pin):
    plan = frozen(PLAN, pin); check_source_plan(plan)
    require('reused_native_preparation' not in plan, 'completed Native exports must be reused, not rerun')
    out = BASE / 'native-preparation'; require(not out.exists(), 'fresh Native preparation required'); out.mkdir()
    owner = {}; h.capture_destination(owner, out); tools = p.tool_manifest(); rows = []
    record = dict(schema=1, kind='named-edge-native-preparation-v1', accepted=False, passed=False,
                  production_admitted=False, status='incomplete', source_plan_sha256=pin, tools=tools,
                  budget_seconds=CAP, rows=rows, routing_executed=False)
    def stable():
        h.owned_destination(owner); frozen(PLAN, pin); check_source_plan(plan)
        require(p.tool_manifest() == tools, 'Native preparation source/tool freeze changed')
        for row in rows:
            folder = out / row['case']; board = next((BASE / 'sources' / row['case']).glob('*.kicad_pcb'))
            require(export_proof(folder, row, board, folder/'native.dsn', folder/'native-netclasses.json') == row['proof'], 'Native export proof changed')
    def account():
        record.update(wall_seconds=time.monotonic()-START, full_cpu_seconds=cpu()-CPU0)
        if remaining() <= 0:record.update(status='budget_exceeded',passed=False)
        elif record['status'] in ('failed','invalidated','cancelled'):record['passed']=False
    with lane():
        try:
            for name in fixture.CASES:
                stable(); board = next((BASE/'sources'/name).glob('*.kicad_pcb'))
                job = f.FloorJob(out/name, CAP, remaining, protect_local_settings=True)
                job.native('export','export',board,job.out/'native.dsn',job.out/'native-netclasses.json')
                row = dict(case=name, steps=job.steps); row['proof'] = export_proof(job.out,row,board,job.out/'native.dsn',job.out/'native-netclasses.json'); rows.append(row)
            stable(); require(remaining()>2, 'Native preparation publication reserve exhausted')
            record.update(passed=True, status='completed')
        except (Exception, KeyboardInterrupt) as exc:
            record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed', reason=type(exc).__name__+': '+str(exc))
        f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    return record


def original_rule_for_eager_control(structure):
    """Select the original rule from the exact original+edge rule pair."""
    rules = sx.children(structure, 'rule')
    expected = ['rule', *[['clearance', '300', ['type', pair]] for pair in
                         ('default_'+edge.CLASS, 'smd_'+edge.CLASS, edge.CLASS+'_'+edge.CLASS)]]
    require(len(rules) == 2 and rules[1] == expected, 'exact original and added edge rules required')
    original = rules[0]; clearances = sx.children(original, 'clearance'); width = sx.one(original, 'width')
    require(len(original) == 4 and width is not None and len(width) == 2
            and len(clearances) == 2 and len(clearances[0]) == 2
            and len(clearances[1]) == 3 and clearances[1][2] == ['type', 'smd_smd'],
            'exact original global width/default/SMD rule required')
    return original


def import_freeze(plan_pin, preparation_pin):
    plan = frozen(PLAN,plan_pin); check_source_plan(plan)
    prepared = frozen(BASE/'native-preparation/result.json',preparation_pin)
    require(prepared.get('passed') is True and prepared.get('status') == 'completed'
            and preparation_pin == plan['reused_native_preparation']['native_preparation_sha256']
            and prepared.get('source_plan_sha256') == plan['reused_native_preparation']['prior_source_plan_sha256']
            and prepared.get('accepted') is False
            and prepared.get('production_admitted') is False, 'Native preparation did not complete')
    require(len(prepared['rows']) == 3 and [r['case'] for r in prepared['rows']] == list(fixture.CASES), 'exact three Native prerequisites required')
    out = BASE/'import-inputs'; require(not out.exists(), 'fresh import freeze required'); out.mkdir(); cases=[]
    for name in CASES:
        if name == 'parent300':
            source=Path(plan['retained_control']['source']); directory=RETAINED/'route'; data=f.read_json(directory/'result.json')
            dsn=directory/'native.dsn'; mapping=directory/'export-netclasses.json'
            proof=check_retained()['export']
        else:
            source=next((BASE/'sources'/name).glob('*.kicad_pcb')); directory=BASE/'native-preparation'/name
            data=next(r for r in prepared['rows'] if r['case']==name); dsn=directory/'native.dsn'; mapping=directory/'native-netclasses.json'
            proof=export_proof(directory,data,source,dsn,mapping)
            require(proof==data['proof'], 'frozen Native preparation proof changed')
        raw=read(dsn); project_raw=read(source.with_suffix('.kicad_pro'))
        require(not source.with_suffix('.kicad_dru').exists(), 'custom rule companion outside named edge scope')
        context=edge.derive_context(read(source),project_raw,experimental_named_classes=True)
        changed, correction=edge.correct(raw,context)
        require(correction['applied'] is True and correction.get('loaded_named_matrix_qualified') is False, 'opt-in prototype did not apply')
        for options in ({},{'experimental_named_classes':False}):
            ordinary=edge.derive_context(read(source),project_raw,**options); unchanged, refusal=edge.correct(raw,ordinary)
            require(unchanged==raw and refusal['applied'] is False and ordinary['reason']=='outside Default-only unassigned project scope', 'ordinary named admission changed')
        before=a._parse_dsn(raw.decode()); restored=a._parse_dsn(changed.decode()); sx.one(sx.one(restored,'structure'),'boundary').pop(); sx.one(restored,'structure').pop()
        require(restored==before, 'nonedge AST changed')
        parent=context['named_class_scope']['source_policy']==nc.PARENT_POLICY
        after_audit=nc.audit_mapping(a._parse_dsn(changed.decode()),f.read_json(mapping),json.loads(project_raw),parent_policy=parent)
        for suffix,value in (('raw',raw),('corrected',changed)):write(out/(name+'-'+suffix+'.dsn'),value)
        save(out/(name+'-correction.json'),correction)
        cases.append(dict(case=name,source=str(source),source_hashes=inventory(source.parent),export_proof=proof,
                          original_edge_um=context['requested_clearance_um'], correction=correction,corrected_class_audit=after_audit))
        if name=='literal300':
            eager=a._parse_dsn(changed.decode()); structure=sx.one(eager,'structure')
            original_rule=original_rule_for_eager_control(structure)
            global_gap=edge._number(sx.children(original_rule,'clearance')[0][1])
            classes=sx.children(sx.one(eager,'network'),'class'); named=[cls for cls in classes if sx.unquote(cls[1])!='kicad_default']
            require(len(named)==1 and edge._number(sx.one(sx.one(named[0],'rule'),'clearance')[1])>global_gap, 'eager-row negative needs a named clearance above global')
            pair=sx.unquote(named[0][1])+'_'+edge.CLASS
            sx.children(structure,'rule')[-1].append(['clearance','300',['type',pair]])
            write(out/'literal300-eager-control.dsn',a._dump_dsn(eager).encode())
    record=dict(schema=1,kind='named-edge-import-protocol-v1',accepted=False,production_admitted=False,
                source_plan_sha256=plan_pin,native_preparation_sha256=preparation_pin,source_plan_code_sha256=plan['code_sha256'],
                native_preparation_source_plan_sha256=prepared['source_plan_sha256'],
                reused_native_preparation=plan['reused_native_preparation'],
                tool_sha256=plan['tool_sha256'],cases=cases,input_sha256=inventory(out),importer_loads=9,
                budget_seconds=CAP,max_log_bytes=512*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=LIMIT,
                scope='One actual full-manager inheritance prerequisite. Retained parent export reused without Native rerun; three new Native exports separate preparation cost. No routing or product admission.')
    save(BASE/'import-protocol.json',record)
    return dict(import_protocol=str(BASE/'import-protocol.json'),sha256=digest(read(BASE/'import-protocol.json')),workers_executed=False)


@cancellable_phase
def execute_import(pin):
    protocol=frozen(BASE/'import-protocol.json',pin); plan=frozen(PLAN,protocol['source_plan_sha256']);check_source_plan(plan)
    require(protocol.get('kind')=='named-edge-import-protocol-v1' and protocol.get('importer_loads')==9
            and protocol.get('accepted') is False and protocol.get('production_admitted') is False, 'import scope changed')
    frozen(BASE/'native-preparation/result.json',protocol['native_preparation_sha256'])
    inputs=BASE/'import-inputs';require(inventory(inputs)==protocol['input_sha256'],'frozen importer inputs changed')
    out=BASE/'import-execution';require(not out.exists(),'fresh importer execution required');out.mkdir();owner={};h.capture_destination(owner,out)
    tools=p.tool_manifest();argv=[*f.SANDBOX,str(c.JAVA),'-Xmx512m','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','--class-path',str(c.JAR),str(HERE/'NamedEdgeManagerProbe.java'),str(inputs),str(out/'observation.json')]
    record=dict(schema=1,kind='named-edge-import-execution-v1',accepted=False,passed=False,status='incomplete',production_admitted=False,
                routing_executed=False,native_executed=False,protocol_sha256=pin,tools=tools,budget_seconds=CAP,argv=argv,
                preparation_costs=f.read_json(BASE/'native-preparation/result.json'),source_freeze_costs={k:plan[k] for k in ('preparation_wall_seconds','preparation_full_cpu_seconds')})
    witness=None
    def stable():
        h.owned_destination(owner);frozen(BASE/'import-protocol.json',pin);check_source_plan(plan)
        frozen(BASE/'native-preparation/result.json',protocol['native_preparation_sha256'])
        require(p.tool_manifest()==tools and inventory(inputs)==protocol['input_sha256'],'importer tool/input freeze changed')
        if witness is not None:
            require({k:v for k,v in inventory(out).items() if k!='result.json'}==witness,'actual importer evidence changed')
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
        if remaining()<=0:record.update(status='budget_exceeded',passed=False)
        elif record['status'] in ('failed','invalidated','cancelled'):record['passed']=False
    with lane():
        try:
            stable();process=run(argv,cwd=out,log=out/'command.log',timeout=max(.001,remaining()-2),max_log_bytes=512*1024,
                                 max_group_rss_bytes=1024**3,max_workdir_bytes=LIMIT)
            process['name']='importer';save(out/'importer-process.json',process);record['steps']=[process]
            f.process_check(out,record,'importer',argv)
            require(process['log_truncated'] is False and process['signal_cancellation_enabled'] is True,'importer log/cancellation unavailable')
            observed=f.read_json(out/'observation.json')
            require(observed.get('matrix_checks_passed') is True and observed.get('routing_executed') is False
                    and observed.get('native_executed') is False and observed.get('production_admitted') is False,'actual semantic importer controls failed')
            rows=observed.get('cases',[]);require([r.get('case') for r in rows]==['literal300','eager_named_row_negative','parent300','underscore300','literal250'],'actual case population differs')
            for row in rows:
                name=row['case']
                if name=='eager_named_row_negative':
                    require(row.get('initialization_change_detected') is True and row['observation']['input_sha256']==protocol['input_sha256']['literal300-eager-control.dsn'],'qualified eager-row semantic negative absent')
                else:
                    require(row.get('matrix_checks_passed') is True and row['checks'] and all(value is True for value in row['checks'].values()),'actual matrix/assignment predicate failed')
                    for kind in ('raw','corrected'):require(row[kind]['input_sha256']==protocol['input_sha256'][name+'-'+kind+'.dsn'],'actual loaded bytes differ')
            require(remaining()>2,'importer publication reserve exhausted')
            record.update(passed=True,status='completed',observation_sha256=digest(read(out/'observation.json')),
                          actual_imports=9,log_sha256=digest(read(out/'command.log')))
            witness=inventory(out)
        except (Exception,KeyboardInterrupt) as exc:
            record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',reason=type(exc).__name__+': '+str(exc))
        f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('freeze-source','prepare-native','freeze-import','run-import'))
    parser.add_argument('--sha256');parser.add_argument('--preparation-sha256')
    parser.add_argument('--allow-native',action='store_true');parser.add_argument('--allow-jvm',action='store_true')
    args=parser.parse_args()
    if args.phase=='freeze-source':result=source_freeze()
    elif args.phase=='prepare-native':
        require(args.allow_native and not args.allow_jvm,'explicit --allow-native only required');result=prepare_native(args.sha256)
    elif args.phase=='freeze-import':result=import_freeze(args.sha256,args.preparation_sha256)
    else:
        require(args.allow_jvm and not args.allow_native,'explicit --allow-jvm only required');result=execute_import(args.sha256)
    print(json.dumps({k:v for k,v in result.items() if k in ('source_plan','import_protocol','sha256','workers_executed','passed','status','reason','wall_seconds','full_cpu_seconds')}))
    return 0 if result.get('passed',True) else 2
if __name__=='__main__':raise SystemExit(main())
