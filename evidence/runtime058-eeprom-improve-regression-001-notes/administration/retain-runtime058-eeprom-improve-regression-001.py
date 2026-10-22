"""Retain only a successful fresh058 EEPROM singleton; run no Native/readers.

Port of the057 singleton IR retainer: reuse shared030 retention and public
custody, own-final, Improve lineage/auxiliary and complete-cost helpers.
Failed outcomes refuse before publication and must be retained separately.
"""
from pathlib import Path
import argparse, ast, datetime, hashlib, json, math, os, re, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io, provenance as pv, floor_route as f
from scripts import report_current_comparison as report
HEAD = '8f5e96b88dd22cd25919bb71ce47711612994efa'
TEMPLATE = 'eae806695d2bd18534ed81c8bc0f353d6562589a92f5aefd0e35f5bfb576cf69'
REPORT = '0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--protocol-sha256',required=True); ap.add_argument('--outer-sha256',required=True)
args = ap.parse_args(); assert all(pv._DIGEST.fullmatch(value) for value in vars(args).values())
base = ROOT/'.runs/runtime058-eeprom-improve-regression-001'
runtime = ROOT/'.runs/runtime-directory-058/runtime'
notes = ROOT/'evidence/runtime058-eeprom-improve-regression-001-notes'
target = ROOT/'evidence/runtime058-eeprom-improve-regression-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(target), 'Fresh packet only; preserve partial failure'
refs = {}; files = []; material = []; total = 0; pins = {}
def bind(path,expected=None):
    path = Path(path); raw = io.read_bytes(path,4*1024**2); pin = hashlib.sha256(raw).hexdigest()
    if expected is not None: assert pin == expected,str(path)
    if path in pins: assert pin == pins[path],str(path)
    else: pins[path] = pin
    return raw
def read(path,expected=None):
    bind(path,expected)
    return report.read(path)
def cost(path):
    bind(path); value = report.complete_cost(path)
    assert Path(value['source']) == Path(path) and value['time_log_sha256'] == pins[Path(path)]
    return value
bind(Path(__file__))
helper = ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
nodes = [n for n in ast.parse(bind(helper,'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1')).body
    if isinstance(n,ast.FunctionDef) and n.name == 'retain']
assert len(nodes) == 1
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared-retain','exec'),globals())
assert Path(report.__file__).resolve() == ROOT/'scripts/report_current_comparison.py'
bind(Path(report.__file__),REPORT)
dependencies = []
for name,pin in (
    ('evidence/runtime057-eeprom-development-001.json','d679f83e507225b83861e08d8380ecc3b28294aabdfd4475aea1aae11386ff79'),
    ('evidence/development-eeprom-001.json','3cdf0561e184daaac153de58a788c735332bdfd67c340f73756530b6171ca223')):
    data = read(ROOT/name,pin); index = data['files_index']; idx = read(ROOT/index['path'],index['sha256'])
    dependencies.append(dict(path=name,sha256=pin,files_index=index,historical=True,
        scope='Source provenance or unchanged057 cohort; no current058 execution authority.'))
    for row in idx['files']: refs.setdefault(row['sha256'],row['path'])
    for row in idx.get('material',[]): refs.setdefault(row['sha256'],row['retained'])
plan = read(base/'protocol.json',args.protocol_sha256); frozen = read(base/'frozen.json')
assert frozen['protocol_sha256'] == args.protocol_sha256 and frozen['template_protocol_sha256'] == TEMPLATE
assert frozen['prepared'] is True and frozen['executed'] is False and frozen['only_arm'] == 'Cimprove'
assert plan['kind'] == 'installed-native7-current-method-v2' and plan['arm'] == 'Cimprove' and plan['source_head'] == HEAD
assert plan['runtime'] == str(runtime) and plan['population_protocol_path'] is None and plan['population_protocol_sha256'] is None
MANIFEST = frozen['manifest_sha256']; assert plan['runtime_manifest_sha256'] == MANIFEST
manifest = runtime/pv.MANIFEST; bind(manifest,MANIFEST)
assert pv._runtime_identity(runtime,plan['tools']['implementation_sha256']) == plan['tools']['source_provenance']
assert plan['limits'] == dict(routing_seconds=420,method_wall_cpu_cap_seconds=450,
    delivery_wall_cpu_cap_seconds=600,export_validation_seconds=120)
assert plan['whole_wall_full_cpu_seconds'] == 600 and frozen['source_head'] == HEAD
for name,pin in plan['prerequisite_sha256'].items(): bind(Path(name),pin)
freezer = ROOT/'.runs/freeze-runtime058-eeprom-improve-regression-001.py'
bind(freezer,frozen['controller_sha256'])
outer_path = base/'enclosure/result.json'; outer = read(outer_path,args.outer_sha256)
assert outer['protocol_sha256'] == args.protocol_sha256 and outer['accepted'] is False and outer['production_admitted'] is False
out = Path(plan['output']); producer = out/'result.json'
assert report.custody(out,plan,outer,'Cimprove') == []
child = read(producer,outer['child_sha256']); complete = cost(base/'outer-time.log')
classification = report.classify(outer,child,complete,'Cimprove')
assert classification['workflow_delivered'] is True and classification['attempt_qualified'] is True
assert outer['passed'] is True and outer['status'] == 'completed' and child['outcome'] == 'validated_delivery'
assert child['controls_passed'] is True and child['status'] == 'completed' and child['workflow_delivered'] is True
routepath = Path(child['selected_route_receipt']); route = read(routepath,child['selected_route_sha256'])
workspace = routepath.parent.parent
assert workspace.parent == out and re.fullmatch('autorouter-gui-[0-9a-f]{32}',workspace.name)
export_path = workspace/'export/export.json'; exported = read(export_path,child['export_sha256'])
assert child['export_receipt'] == str(export_path)
allowed = [out]
parent_proof = report.own_final(routepath,export=False,plan=plan,allowed=allowed,accepted=True,public_sanitize=True)
export_proof = report.own_final(export_path,export=True,plan=plan,allowed=allowed,accepted=True,public_sanitize=True)
improve = report.improve_facts(routepath,plan,allowed,qualified_parent=True,public_sanitize=True)
export_auxiliary = report.improve_auxiliary(export_path.parent/'validation',exported,plan)
assert parent_proof['Native_counts'] == export_proof['Native_counts']
counts = parent_proof['Native_counts']; assert counts[:2] == [0,0] and counts[3] == 0
assert len(route['trials']) <= 32
# A legal fresh refill may change derived-fill bytes: bind both own hashes,
# not an invented equality between pre-export and freshly refilled candidates.
assert exported['preview_board_sha256'] == route['candidate_sha256']
assert exported['candidate_sha256'] == child['candidate_sha256']
assert p.tree_hash(Path(plan['source']).parent) == plan['source_hashes']
review = read(workspace/'review/review.json'); choice = read(workspace/'choice/choice.json')
assert review['status'] == 'ready_for_manual_review' and choice['choice_recorded'] is True and choice['choice'] == 'accept'
assert choice['human_pcb_approval_observed'] is False and choice['applied'] is False
assert review['receipt_sha256'] == choice['receipt_sha256'] == pins[routepath]
assert choice['review_sha256'] == pins[workspace/'review/review.json']
assert all(type(v) in (int,float) and math.isfinite(v) and 0 <= v <= 30 for v in
    (review['wall_seconds'],review['total_cpu_seconds'],choice['wall_seconds'],choice['total_cpu_seconds']))
processes = {}; queue = {}; omitted = []
def add(path,name):
    path = Path(path); assert '.runs' not in name.parts and '..' not in name.parts
    bind(path); queue.setdefault(path,name)
for q in sorted(out.glob('*.process.json')):
    data = read(q)
    assert data['exit_code'] == 0 and data['cancel_requested'] is False and data['log_truncated'] is False
    processes[q.name] = dict(wall_seconds=data['wall_seconds'],exit_code=0,cancel_requested=False,
        cleanup_scope=data['cleanup_scope'],sha256=pins[q])
    add(q,Path('stage-processes')/q.name)
assert set(processes) == {name+'.process.json' for name in ('preview','route','review','choice','export','verify_export')}
for relative,pin in outer['completed_evidence'].items():
    q = out/relative
    if q.name.endswith(('-process.json','-binding.json','-local-settings.json')) or q.suffix == '.kicad_prl':
        bind(q,pin); add(q,Path('current-own-proof-metadata')/relative)
    else:
        omitted.append(dict(original=str(q.relative_to(ROOT)),sha256=pin,
            reason='Raw foreign CAD/findings/field values/transport/plots or unselected metadata stays local; sanitized bound facts retained.'))
for name in ('protocol.json','frozen.json','tools-defaults.json','tools-defaults-process.json',
        'enclosure/command.log','enclosure/process.json','enclosure/result.json','outer.log','outer-time.log'):
    add(base/name,Path('single-regression')/name)
full = ROOT/'.runs/full-integration-209'; execution = read(full/'execution.json')
prepared = read(runtime.parent/'preparation.json')
assert execution['passed'] is True and execution['sources_unchanged'] is True
assert execution['process']['status'] == 'success' and execution['process']['exit_code'] == 0
assert execution['process']['cleanup_complete'] is True and execution['process']['log_truncated'] is False
assert prepared['source_head'] == HEAD and prepared['manifest_sha256'] == MANIFEST
assert prepared['full209_execution_sha256'] == pins[full/'execution.json']
full_text = bind(full/'command.log').decode(); matches = re.findall(r'^Ran ([0-9]+) tests in ',full_text,re.M)
assert len(matches) == 1 and re.search(r'^OK \(skipped=1\)$',full_text,re.M)
for name in ('protocol.json','execution.json','command.log'): add(full/name,Path('integration/full209')/name)
for name in ('runtime-distribution.json','RUNTIME_README.txt'): add(runtime/name,Path('runtime')/name)
for name in ('preparation.json','venv-process.json','venv.log'): add(runtime.parent/name,Path('runtime/preparation')/name)
for name in ('run-full-integration-209.py','full-integration-209-controller-001.log','full-integration-209-time-001.log',
        'prepare-runtime058-002.py','prepare-runtime058-002.log','prepare-runtime058-002-time.log',
        freezer.name,'freeze-runtime058-eeprom-improve-regression-001.log','freeze-runtime058-eeprom-improve-regression-001-time.log'):
    add(ROOT/'.runs'/name,Path('controllers-and-costs')/name)
assert pins[ROOT/'.runs/prepare-runtime058-002.py'] == prepared['controller_sha256']
for q in (Path(__file__),helper,Path(report.__file__),ROOT/'scripts/enclose_current_comparison.py',
        ROOT/'scripts/qualify_current_method.py',ROOT/'scripts/qualify_installed_workflow.py'):
    add(q,Path('administration')/q.name)
full_cost = cost(ROOT/'.runs/full-integration-209-time-001.log')
build_cost = cost(ROOT/'.runs/prepare-runtime058-002-time.log')
prep_cost = cost(ROOT/'.runs/freeze-runtime058-eeprom-improve-regression-001-time.log')
def fresh():
    for path,pin in list(pins.items()): assert hashlib.sha256(io.read_bytes(path,4*1024**2)).hexdigest() == pin,str(path)
    assert report.custody(out,plan,outer,'Cimprove') == []
    assert p.tree_hash(Path(plan['source']).parent) == plan['source_hashes']
planned_refs = dict(refs); planned_files = []; planned_material = []; planned_bytes = 0
for path,name in queue.items():
    raw = bind(path); pin = pins[path]; destination = planned_refs.get(pin)
    if destination is None:
        assert b'\0' not in raw; raw.decode('utf8'); destination = str((notes/name).relative_to(ROOT))
        planned_refs[pin] = destination; planned_bytes += len(raw)
        planned_files.append(dict(path=destination,bytes=len(raw),sha256=pin))
    elif pin in refs: bind(ROOT/destination,pin)
    planned_material.append(dict(original=str(path.relative_to(ROOT)),retained=destination,bytes=len(raw),sha256=pin))
index = notes/'files.json'; index_data = dict(schema=1,files=planned_files,material=planned_material,omitted_local_hash_only=omitted)
summary = dict(schema=1,kind='runtime058-single-fresh-exposed-EEPROM-Improve-delivery-regression-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,workflow_delivered=True,
    attempt_qualified=True,project_complete=False,actual_GUI=False,human_review=False,source_head=HEAD,
    runtime=str(runtime),runtime_manifest_sha256=MANIFEST,protocol_sha256=args.protocol_sha256,
    full209=dict(passed=True,tests=int(matches[0]),skips=1,complete_cost=full_cost),
    build=dict(complete_cost=build_cost),preparation=dict(complete_cost=prep_cost),
    single_fresh_exposed_EEPROM_Improve=dict(classification=classification,complete_cost=complete,
        outer_sha256=args.outer_sha256,outer_complete_wall_seconds=outer['complete_wall_seconds'],
        outer_complete_full_CPU_seconds=outer['complete_full_CPU_seconds'],child_sha256=pins[producer],
        route_receipt_sha256=pins[routepath],review_receipt_sha256=pins[workspace/'review/review.json'],
        choice_receipt_sha256=pins[workspace/'choice/choice.json'],export_receipt_sha256=pins[export_path],
        route_candidate_sha256=route['candidate_sha256'],candidate_sha256=exported['candidate_sha256'],
        Native_counts=counts,trials=len(route['trials']),metrics=route['metrics'],stages=processes,
        parent_own_final=parent_proof,export_own_final=export_proof,Improve_lineage=improve,export_auxiliary=export_auxiliary),
    source_hashes=plan['source_hashes'],source_rights=plan['source_rights'],source_unchanged=True,dependencies=dependencies,
    scope='One fresh058 exposed EEPROM single Improve delivery regression at unchanged420/450/600/export120,30s review/choice and existing32-trial cap/25s return reserve. Shared metadata helpers check own parent/export/incumbent/every completed trial Native/fullSCH/Default/fields/PRL/process/bindings; no Native or central reader rerun. No baseline rerun, six-arm result stitching, GUI, new family, independent ancestry, routing superiority, human or electrical claim.',
    all_prior_cohorts_and_failures_unchanged=True,not_a_comparison=True,
    costs='Complete external exits counted once; nested samples overlap. Full209/build/preparation are separate additional costs. Failed057 cohort, full208 failure, previous profiles/tests/intake/authoring/AI review/GUI/install/curation remain additional and partly unmetered, never zero or stitched into this new attempt. Curation complete exit must be recorded separately.',
    raw_scope='Sanitized owned facts and metadata/log/PRL only; foreign CAD/DSN/SES/plots/full findings/field values stay local. Raw Mac-only/outside010, no full raw restore, Windows/cleanOS/standalone/electrical qualification.',
    files_index=dict(path=str(index.relative_to(ROOT))))
index_raw = (json.dumps(index_data,indent=2)+'\n').encode(); index_pin = hashlib.sha256(index_raw).hexdigest()
summary['files_index']['sha256'] = index_pin
summary_raw = (json.dumps(summary,indent=2)+'\n').encode(); summary_pin = hashlib.sha256(summary_raw).hexdigest()
assert len(planned_files)+2 < 2000 and max(len(index_raw),len(summary_raw)) <= 4*1024**2
assert planned_bytes+len(index_raw)+len(summary_raw) < 16*1024**2,'Split before writing; never raise caps'
fresh()
for path,name in queue.items(): retain(path,name)
assert files == planned_files and material == planned_material and total == planned_bytes
for row in files: pins[ROOT/row['path']] = row['sha256']
fresh(); p.save_json(index,index_data); bind(index,index_pin); fresh()
fresh(); p.save_json(target,summary); bind(target,summary_pin); fresh()
print(json.dumps(dict(files=len(files),bytes=total,material=len(material),delivered=True,
    Native_rerun=False,project_complete=False,packet_sha256=summary_pin,index_sha256=index_pin)))
