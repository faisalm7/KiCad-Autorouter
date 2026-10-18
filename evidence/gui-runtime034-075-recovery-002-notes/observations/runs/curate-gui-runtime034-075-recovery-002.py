"""PREPARED ONLY: retain exact034 GUI075 recovery delivery and missed cancel.

Never execute before lead review/authorization. No Native, GUI or process control.
Usage: python -B THIS --manifest FINAL --observations OBSERVATIONS
FINAL is gui-session075/final-controls-recovery-001.json: schema1, finalized,
source_head/runtime_manifest_sha256, jobs(no-repair,repair,missed_cancel),
preopen(no-repair,repair), postopen={'repair':receipt}, privacy and typed
public_additional_files with the ordinary075 allowlist. OBSERVATIONS requires
actual_GUI_recovery_delivery true, recovery_cancellation_qualified false,
full_GUI_qualification false, known_budget_summary_display_defect true and the
same three observed_roles. Neither missed observer may qualify cancellation.
The two delivered roles have own parent/final Native and separate exports;
the editor-stale repair export is historical preopen proof only. Ordinary075
is a separate immutable packet. Future fixed GUI source never upgrades034.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-034/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io, local_settings as local, review_export as ex

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--observations', type=Path, required=True)
args = parser.parse_args()
started = time.monotonic()
base = runtime / '.runs/gui-session075'
args.manifest = args.manifest.resolve(strict=True); args.observations = args.observations.resolve(strict=True)
assert args.manifest == base / 'final-controls-recovery-001.json'
assert args.observations == base / 'actual-GUI-recovery-observations-001.json'
manifest = f.read_json(args.manifest); observations = f.read_json(args.observations)
prepared_path = base / 'prepared-state.json'; prepared = f.read_json(prepared_path)
required_path = base / 'recovery-controls-001/protocol-required-001.json'
assert prepared['recovery_protocol'] == str(required_path)
assert p.sha(required_path) == prepared['recovery_protocol_sha256'] == 'e2c1f3b0deec7d535e140657456c5b7acced6e1c2608efbe1e9bb69a6ebdbf5c'
required = f.read_json(required_path)
head = 'd64e5f1c9e35552eb2eeca93c71c5683fd09c37c'
runtime_pin = '65aa2eb27ac5c61ce96a771bb6d8a65f923220e464886fb43d789377e4c61d5b'
for data in (manifest, observations, prepared, required):
    assert data['source_head'] == head and data['runtime_manifest_sha256'] == runtime_pin
assert type(manifest['schema']) is int and manifest['schema'] == 1 and manifest['finalized'] is True
assert observations['actual_GUI_recovery_delivery'] is True
assert observations['known_budget_summary_display_defect'] is True
for key in ('recovery_cancellation_qualified', 'full_GUI_qualification', 'actual_GUI_is_human_review',
            'physical_electrical_validation', 'project_complete', 'queued_race_forced_in_actual_GUI',
            'all_phase_cancellation_qualified'):
    assert observations[key] is False
privacy = dict(public_projection=True, raw_browser_screenshots_excluded=True,
    full_browser_AX_excluded=True, raw_capture_filenames_excluded=True, all_PNG_Mac_only=True)
assert manifest['privacy'] == observations['privacy'] == privacy
labels = ('no-repair', 'repair', 'missed_cancel')
assert set(manifest['jobs']) == set(observations['observed_roles']) == set(labels)
assert len(observations['observed_roles']) == len(labels)
jobs = {label:Path(manifest['jobs'][label]) for label in labels}
expected = dict(zip(labels, ('autorouter-gui-91c142febc9a4804846c18d67f3d116d',
    'autorouter-gui-702dbdd14b7d42879a269881e4531d5c', 'autorouter-gui-33ecf16ec64947419f7eb5aa319e213a')))
assert all(work == base/'jobs'/expected[label] and work.resolve(strict=True) == work for label, work in jobs.items())
ordinary_manifest_path = base / 'final-controls-ordinary-001.json'
ordinary_manifest = f.read_json(ordinary_manifest_path)
ordinary_packet_path = ROOT / 'evidence/gui-runtime034-075-ordinary-native-controls-001.json'
ordinary_packet = f.read_json(ordinary_packet_path)
assert p.sha(ordinary_manifest_path) == ordinary_packet['finalized_manifest_sha256']
assert ordinary_packet['actual_GUI_ordinary_qualification'] is True
assert ordinary_packet['source_head'] == head and ordinary_packet['runtime_manifest_sha256'] == runtime_pin
ordinary_jobs = {Path(path) for path in ordinary_manifest['jobs'].values()}
assert len(ordinary_jobs) == 7 and not ordinary_jobs.intersection(jobs.values())
assert {path for path in (base/'jobs').iterdir() if path.is_dir()} == ordinary_jobs | set(jobs.values())
tools = p.tool_manifest()
assert tools == prepared['tools'] and tools['git_head'] == head and tools['kicad'] == '10.0.7'
assert tools['source_provenance']['manifest_sha256'] == p.sha(runtime/'runtime-distribution.json') == runtime_pin
assert tools['implementation_sha256']['autorouter/gui.py'] == '1d5f4f6f776e970c9d78a33f1e116c16c3333e880f1e4328a25338226bf9f827'
assert tools['implementation_sha256']['autorouter/pipeline.py'] == '8a0276c178649ff76383865e125c63803a71a15b144ac29905a0c072c67480af'
input_pins = {path:p.sha(path) for path in (args.manifest, args.observations, prepared_path,
    required_path, ordinary_manifest_path, Path(__file__).resolve())}

# Reuse the exact existing bounded retain/tree/cost functions as source, never
# execute that historical curator's top level. Its16MiB/2000-new-file retention
# cap remains unchanged (and below ordinary075's64MiB cap).
helper_path = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper_path) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
helper_tree = ast.parse(helper_path.read_text())
definitions = [node for node in helper_tree.body if isinstance(node, ast.FunctionDef) and node.name in {'retain', 'tree', 'cost'}]
assert {node.name for node in definitions} == {'retain', 'tree', 'cost'}
for node in definitions:
    if node.name in {'retain', 'tree'}: node.name = '_shared_' + node.name
exec(compile(ast.fix_missing_locations(ast.Module(body=definitions, type_ignores=[])), str(helper_path), 'exec'))
notes = ROOT / 'evidence/gui-runtime034-075-recovery-002-notes'
packet_path = ROOT / 'evidence/gui-runtime034-075-recovery-002.json'
assert not notes.exists() and not packet_path.exists()
refs = {}; files = []; material = []; total = 0; reference_records = []
# Failed001 partial text is immutable retained evidence, never overwritten.
# Reuse its exact bytes without raising the shared new-file cap.
partial_receipt=ROOT/'.runs/gui075-recovery-curation-failed001.json'
partial_pin=p.sha(partial_receipt);partial=f.read_json(partial_receipt)
assert partial['passed'] is False and partial['Native_rerun'] is False
assert len(partial['partial_files'])==314 and partial['logical_bytes']==16810741
for row in partial['partial_files']:
    path=ROOT/row['path']
    assert path.resolve().is_relative_to(ROOT/'evidence/gui-runtime034-075-recovery-001-notes')
    assert p.sha(path)==row['sha256'] and len(io.read_bytes(path,4*1024**2))==row['bytes']
    refs.setdefault(row['sha256'],row['path'])
reference_records.append(dict(kind='failed001-partial-exact-public-text',files=partial['partial_files'],scope=partial['decision']))


def reference(path, purpose):
    record = f.read_json(path)
    reference_records.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path), purpose=purpose))
    rows = record.get('files', [])
    if record.get('files_index'):
        index = ROOT / record['files_index']['path']
        assert p.sha(index) == record['files_index']['sha256']
        reference_records.append(dict(path=str(index.relative_to(ROOT)), sha256=p.sha(index), purpose='Exact-file index only.'))
        stored = f.read_json(index); rows = rows + stored.get('files', []) + stored.get('material', [])
    assert len(rows) < 4000
    for row in rows:
        public = row.get('path', row.get('retained'))
        assert (ROOT/public).resolve().is_relative_to(ROOT/'evidence')
        refs.setdefault(row['sha256'], public)
    return record

reference(ROOT/'evidence/runtime034-ordinary-install-001.json', '034 installed source/tool references; not GUI recovery proof.')
reference(ordinary_packet_path, 'Separate completed ordinary075 packet and exact-byte references only.')
refusals = reference(ROOT/'evidence/gui-runtime034-075-recovery-refusals-001.json', 'Separate current actual preworkspace settings/class/layer refusals, including failed source-authoring001.')
assert refusals['actual_GUI_refusals'] is True and refusals['source_head'] == head and refusals['runtime_manifest_sha256'] == runtime_pin
interf = f.read_json(ROOT/'evidence/runtime033-current-interf-comparison-001.json')
reference_records.append(dict(path='evidence/runtime033-current-interf-comparison-001.json',
    sha256=p.sha(ROOT/'evidence/runtime033-current-interf-comparison-001.json'), purpose='Exact licensed Interf source/rights only; no inherited034 routing or GUI authority.'))
member = interf['packets'][0]; assert p.sha(ROOT/member['path']) == member['sha256']
reference(ROOT/member['path'], 'Exact licensed source, license/Tux attribution and file references only.')
assert required['recovery']['repair']['source_hashes'] == interf['population']['source_hashes']
assert required['repair_source_rights'] == interf['population']['source_rights']

approved = {}; public = manifest['public_additional_files']
assert type(public) is list and len(public) <= 80
allowed_kinds = {'owned_router_ax', 'owned_kicad_ax', 'owned_review_body_ax', 'owned_observation_receipt', 'owned_controller', 'owned_process_log'}
images = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
image_name = re.compile(r'(?i)[^\s"<>]+\.(?:png|jpe?g|webp|gif)(?:\b|[" ])')
for entry in public:
    assert set(entry) == {'path', 'sha256', 'kind'} and entry['kind'] in allowed_kinds
    path = Path(entry['path']); assert path.is_absolute() and path.resolve(strict=True) == path and path.is_relative_to(ROOT)
    assert path.suffix.lower() not in images | {'.bmp'} and path not in approved and p.sha(path) == entry['sha256']
    approved[path] = entry
for path in (args.manifest, args.observations):
    text = path.read_text()
    assert not image_name.search(text)
    assert not any(term in text for term in ('AXApplication', 'AXWindow', 'chrome://', 'Google Chrome'))

def retain(path, relative):
    path = Path(path); assert path.is_absolute() and path.resolve(strict=True) == path and path.is_relative_to(ROOT)
    assert path.suffix.lower() not in images, 'Pixel captures remain Mac-only.'
    if path.suffix.lower() == '.zip': return  # Postopen receipt retains its exact hash, not binary ZIP payload.
    if 'browser' in path.name.lower() or 'chrome' in path.name.lower():
        assert path in approved and approved[path]['kind'] == 'owned_review_body_ax'
    if path in approved:
        assert p.sha(path) == approved[path]['sha256']
        if approved[path]['kind'] == 'owned_review_body_ax':
            text = io.read_bytes(path).decode('utf-8')
            assert not image_name.search(text) and not any(term in text for term in ('AXApplication', 'AXWindow', 'chrome://', 'Google Chrome'))
    if path.suffix.lower() == '.bmp': assert p.sha(path) in refs, 'Only an exact already-public licensed binary reference is permitted.'
    _shared_retain(path, relative)

def tree(path, relative):
    _shared_tree(path, relative)

route_rows = []; export_rows = []; GUI_journals = []; prl_packets = []; prl_pairs = []; source_pins = {}
for label, work in jobs.items():
    role = 'repair' if label == 'missed_cancel' else label
    declared = required['recovery'][role]; source = Path(declared['source']); external = Path(declared['original_source'])
    hashes = declared['source_hashes']; settings = f.read_json(work/'settings.json')
    assert settings == declared['settings'] and p.sha(Path(declared['settings_path'])) == declared['settings_sha256']
    assert p.tree_hash(source.parent) == p.tree_hash(external.parent) == hashes
    source_pins[source.parent] = source_pins[external.parent] = hashes
    route_path = work/'route/result.json'; data = f.read_json(route_path)
    assert data['source'] == str(source) and data['source_hashes'] == hashes and data['tools'] == tools
    assert data['strategy'] == 'native_validated_thermal_bridge' and data['thermal_parent_policy'] == 'native-thermal-parent-selection-v1'
    assert data['scope'] == 'whole_board_unlocked_routing' and data['engine_profile'] == 'standard' and data['adapter'] == 'both'
    assert 'routing_preferences' not in data and 'scoring_variant' not in data
    assert data['budget_seconds'] == data['cpu_budget_seconds'] == settings['seconds'] == declared['whole_method_seconds']
    assert data['status'] == 'routing_accepted' and data['accepted'] is True and data['invariants_unchanged'] is True
    assert data['schematic_parity'] == 'checked by final native DRC'
    assert all(step['cleanup_complete'] is True and step['status'] != 'cancelled' and step['log_truncated'] is False for step in data['steps'])
    incumbent_path = work/'route/incumbent/result.json'; inc = f.read_json(incumbent_path)
    assert data['incumbent'] == dict(receipt=str(incumbent_path), receipt_sha256=p.sha(incumbent_path), status=inc['status'], accepted=inc['accepted'])
    assert inc['source'] == str(source) and inc['source_hashes'] == hashes and inc['tools'] == tools
    assert p.tree_hash(work/'route/snapshot') == p.tree_hash(work/'route/incumbent/snapshot') == hashes
    original = p.sx.read(source); candidate = Path(data['candidate']); current = p.sx.read(candidate)
    protected = p.protected_for_record(data, original)
    assert p.immutable(original) == p.immutable(current) and all(item in p.routes(current) for item in protected)
    assert len(protected) == (1 if label == 'no-repair' else 0)
    assert p.sha(candidate) == data['candidate_sha256'] and p.sha(work/'route/final-drc.json') == data['native_report_sha256']
    assert p.parse_report(work/'route/final-drc.json', source.name) == data['native']
    assert [data['native'][k] for k in ('opens', 'blocking', 'warnings', 'exclusions')] == ([0,0,0,0] if label == 'no-repair' else [0,0,22,0])
    if label == 'no-repair':
        assert data['recovery_needed'] is False and data['repair'] is None and inc['accepted'] is True
        assert data['candidate_sha256'] == inc['candidate_sha256'] and not (work/'route/recovery').exists()
        selection = dict(kind='accepted incumbent; no repair', candidate_sha256=inc['candidate_sha256'])
    else:
        repair = f.read_json(work/'route/recovery/repair.json'); assert data['repair'] == repair and data['recovery_needed'] is True
        assert inc['accepted'] is False and inc['status'] == 'drc_rejected'
        assert [inc['native'][k] for k in ('opens','blocking','warnings','exclusions')] == [0,1,22,0]
        trials = [trial for trial in repair['trials'] if trial['validation_passed'] is True]
        assert len(trials) == len(repair['trials']) == 1
        trial = trials[0]; assert trial['id'] == 'trial-01' and p.sha(trial['candidate']) == data['candidate_sha256'] == repair['candidate_sha256']
        assert repair['routing_accepted'] is False and repair['comparison_eligible'] is False
        selection = dict(kind='own selected thermal trial plus own parent final Native', selected_trial=trial['id'],
            repair_receipt_sha256=p.sha(work/'route/recovery/repair.json'), geometry_sha256=p.sha(work/'route/recovery/geometry.json'),
            proposals_sha256=p.sha(work/'route/recovery/proposals.json'), selected_candidate_sha256=trial['candidate_sha256'],
            selected_Native_report_sha256=trial['native_report_sha256'], selected_final_map_sha256=trial['final_map_sha256'])
    with p.validation_readback_session(): assert p.check_result(route_path)['current'] is True
    command = f.read_json(work/'route.command.process.json')
    assert command['argv'] == [str(runtime/'.venv/bin/python'), '-B', '-m', 'autorouter', 'recover', str(source), '--seconds', str(settings['seconds']), '--output', str(work/'route')]
    assert command['exit_code'] == 0 and command['cancel_requested'] is False and command['log_truncated'] is False
    route_rows.append(dict(label=label, result_sha256=p.sha(route_path), status=data['status'], accepted=True,
        source=str(source), source_hashes=hashes, captured_settings=settings, settings_sha256=p.sha(work/'settings.json'),
        candidate_sha256=data['candidate_sha256'], native=data['native'], native_report_sha256=data['native_report_sha256'],
        protected_locked_items=len(protected), original_nonrouting_design_preserved=True, schematic_parity=data['schematic_parity'],
        incumbent_receipt_sha256=p.sha(incumbent_path), incumbent_candidate_sha256=inc['candidate_sha256'],
        incumbent_native_report_sha256=inc['native_report_sha256'], selection=selection,
        whole_method_seconds=data['budget_seconds'], wall_seconds=data['wall_seconds'], total_CPU_seconds=data['total_cpu_seconds'],
        cancellation_qualified=False, scope='Missed timing attempt completed accepted; no cancel, delivery or comparative win.' if label == 'missed_cancel' else 'Own current parent readback; delivery separately bound below.'))
    prl_packets.append((work/'route', data)); tree(work/'route', Path(label)/'route')
    retain(work/'settings.json', Path(label)/'settings.json')
    for path in sorted(work.glob('*.command.*')):
        retain(path, Path(label)/'GUI-journals'/path.name)
        if path.name.endswith('.process.json'): GUI_journals.append(dict(label=label, file=path.name, process=f.read_json(path)))
    if label == 'missed_cancel':
        assert not any((work/name).exists() for name in ('review', 'choice', 'export'))
        continue
    review_path = work/'review/review.json'; review = f.read_json(review_path); choice = f.read_json(work/'choice/choice.json')
    assert review['receipt'] == str(route_path) and review['receipt_sha256'] == p.sha(route_path)
    assert choice['choice_recorded'] is True and choice['choice'] == 'accept'
    preview = review['preview']; plot = work/'review/plot-work'
    assert preview['layers'] == ['F.Cu','B.Cu'] and len(preview['steps']) == 4
    for step in preview['steps']:
        process = f.process_check(plot, preview, step['name'], step['argv'])
        prl_pairs.append((plot, f.read_json(plot/(step['name']+'-input-binding.json')), process))
    tree(work/'review', Path(label)/'rendered-review'); tree(work/'choice', Path(label)/'choice')

assert set(manifest['preopen']) == {'no-repair','repair'} and set(manifest['postopen']) == {'repair'}
for label, preopen_path in manifest['preopen'].items():
    work = jobs[label]; declared = required['recovery'][label]; source = Path(declared['source'])
    preopen_path = Path(preopen_path); assert preopen_path == base/'recovery-controls-001'/label/'preopen-001.json'
    pre = f.read_json(preopen_path); snapshot = Path(pre['snapshot']); exported = f.read_json(snapshot/'export.json')
    parent = f.read_json(work/'route/result.json')
    assert pre['workspace'] == str(work) and pre['source_hashes'] == declared['source_hashes'] and pre['source_unchanged'] is True
    assert pre['route']['current'] is True and pre['export']['current'] is True
    assert p.tree_hash(snapshot) == pre['snapshot_hashes'] and len(pre['snapshot_hashes']) == (83 if label == 'no-repair' else 173)
    assert pre['route']['candidate_sha256'] == parent['candidate_sha256'] == pre['export']['candidate_sha256'] == exported['candidate_sha256']
    assert exported['inputs']['source'] == str(source) and exported['inputs']['receipt'] == str(work/'route/result.json')
    assert exported['inputs']['receipt_sha256'] == p.sha(work/'route/result.json') and exported['source_hashes'] == declared['source_hashes']
    assert exported['export_accepted'] is True and exported['applied'] is False and exported['tools'] == tools
    assert exported['original_geometry_and_routing_unchanged'] is True and exported['schematic_parity'] == 'checked by final native DRC'
    assert exported['budget_seconds'] == exported['cpu_budget_seconds'] == declared['additional_export_seconds'] == (90 if label == 'no-repair' else 120)
    frozen = snapshot/'validation/candidate'/source.name
    assert p.sha(frozen) == exported['candidate_sha256'] and p.sha(snapshot/'validation/final-drc.json') == exported['native_report_sha256']
    assert p.parse_report(snapshot/'validation/final-drc.json', source.name) == exported['native'] == parent['native']
    assert p.immutable(p.sx.read(frozen)) == p.immutable(p.sx.read(source))
    protected = p.protected_for_record(parent,p.sx.read(source)); assert all(item in p.routes(p.sx.read(frozen)) for item in protected)
    if label == 'no-repair':
        with p.validation_readback_session(): assert ex.check_export(work/'export/export.json')['current'] is True
        prl_packets.append((work/'export/validation', exported))
    else:
        postpath = Path(manifest['postopen']['repair']); post = f.read_json(postpath)
        assert postpath == base/'recovery-controls-001/repair/postopen-001.json' and post['workspace'] == str(work)
        assert post['source_unchanged'] is True and post['candidate_PCB_unchanged'] is True
        assert p.tree_hash(Path(post['snapshot'])) == post['snapshot_hashes']
        assert p.sha(Path(exported['candidate'])) == exported['candidate_sha256']
        for suffix in ('.kicad_pro','.kicad_prl'):
            key = 'validation/candidate/' + source.with_suffix(suffix).name
            assert post['changed'][key]['before'] == pre['snapshot_hashes'].get(key)
            assert post['changed'][key]['after'] == post['snapshot_hashes'][key] != post['changed'][key]['before']
        assert len(post['changed']) == 3 and sum(name.endswith('.zip') for name in post['changed']) == 1
        assert observations['repair']['later_open_refused_as_stale'] is True
        retain(postpath, Path(label)/'observations/postopen.json')
    export_rows.append(dict(label=label, preopen_receipt_sha256=p.sha(preopen_path), snapshot_hashes=pre['snapshot_hashes'],
        candidate_sha256=exported['candidate_sha256'], native_report_sha256=exported['native_report_sha256'], native=exported['native'],
        additional_export_budget_seconds=exported['budget_seconds'], protected_locked_items=len(protected),
        current_export_reader_replayed=label=='no-repair', current_validation_PRL_replayed=label=='no-repair',
        scope='Own current no-repair export.' if label=='no-repair' else 'Frozen preopen proof only; editor changed PRO and added PRL/ZIP, PCB unchanged. Current export reacceptance/metadata replay excluded.'))
    retain(preopen_path, Path(label)/'observations/preopen.json'); tree(snapshot, Path(label)/'preopen-export')

observer_rows = []; extra_costs = []
for path, entry in approved.items():
    if entry['kind'] == 'owned_observation_receipt':
        data = f.read_json(path)
        if 'actual_recovery_process_observed' in data:
            assert data['role'] == 'recovery' and data['workspace'] == str(jobs['missed_cancel'])
            assert data['actual_process_observed'] is False and data['actual_recovery_process_observed'] is False
            assert data['source_head'] == head and data['runtime_manifest_sha256'] == runtime_pin
            if data.get('incumbent') is not None:
                inc = data['incumbent']; assert p.sha(Path(inc['path'])) == inc['sha256']
                assert hashlib.sha256(inc['raw_utf8'].encode()).hexdigest() == inc['sha256']
            observer_rows.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path), observation=data,
                cancellation_qualified=False, scope='Finite observation missed eligible repair/final worker; no cancel clicked.'))
    if entry['kind']=='owned_process_log' and path.name.endswith('-time.log'):
        extra_costs.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path), complete_cost=cost(path)))
    retain(path, Path('observations')/path.parent.name.lstrip('.')/path.name)
assert len(observer_rows) == 2
assert observations['missed_cancel']['GUI_cancel_clicked'] is False and observations['missed_cancel']['owned_repair_phase_observed'] is False
assert observations['missed_cancel']['parent_completed_accepted'] is True and observations['missed_cancel']['export_created'] is False
for label in ('no-repair','repair'):
    assert observations[label.replace('-','_')]['rendered_FCu_BCu'] is True
    assert observations[label.replace('-','_')]['explicit_accept_intent'] is True
for path in (args.manifest,args.observations,prepared_path,required_path,ordinary_manifest_path,Path(__file__).resolve()):
    retain(path, Path('observations')/path.parent.name.lstrip('.')/path.name)
for path, pin in ((ROOT/'.runs/gui-runtime034-075-recovery-interim-review-001.json','18433f14e75f717c9111e956698542070f5c6db7765ddccb7e9cbfaaa26bc39b'),
                  (ROOT/'.runs/gui-thermal-budget-display-review-001.json','2bbf797a20c21f1865da939db61cf3d28635dcd5cf2b1757bb56a07928547bb1')):
    assert p.sha(path)==pin; retain(path,Path('AI-reviews')/path.name)

for q in (partial_receipt,ROOT/'.runs/curate-gui-runtime034-075-recovery-001.py',
          ROOT/'.runs/curate-gui-runtime034-075-recovery-001-command.log',
          ROOT/'.runs/curate-gui-runtime034-075-recovery-001-time.log',
          ROOT/'.runs/finalize-gui075-recovery-records-001-command.log',
          ROOT/'.runs/finalize-gui075-recovery-records-001-time.log'):
    retain(q,Path('curation-failure-and-costs')/q.name)
assert p.sha(partial_receipt)==partial_pin

# No tool, inventory or other material callback may follow the last all-root
# metadata replay. All three parents completed; no cancelled Native row is
# passed to the shared allowed0/5 collector. A true cancellation is unqualified.
assert p.tool_manifest() == tools and p.sha(runtime/'runtime-distribution.json') == runtime_pin
for path, hashes in source_pins.items(): assert p.tree_hash(path) == hashes
for path, pin in input_pins.items(): assert p.sha(path) == pin
for item in material:
    assert p.sha(ROOT/item['original']) == p.sha(ROOT/item['retained']) == item['sha256']
index = dict(schema=1, files=files, material=material,
    scope='Bounded exact text copies/references only. Pixels/full browser/caches/ZIP payload stay Mac-only; licensed binary is an existing exact reference.')
notes.mkdir(parents=True,exist_ok=True)
with (notes/'files.json').open('x') as stream: json.dump(index,stream,indent=2); stream.write('\n')
record = dict(schema=1, kind='actual-runtime034-GUI075-recovery-delivery-with-missed-cancel', project_complete=False,
    actual_GUI=True, actual_GUI_recovery_delivery=True, recovery_cancellation_qualified=False, full_GUI_qualification=False,
    curation_attempt='002 retains failed001 source/log/cost and all314partialfiles; shared16MiB newfilecap unchanged.',
    known_budget_summary_display_defect=True, human_review=False, physical_electrical_validation=False,
    source_head=head, runtime_manifest_sha256=runtime_pin, finalized_manifest_sha256=input_pins[args.manifest],
    observations_sha256=input_pins[args.observations], curator_sha256=input_pins[Path(__file__).resolve()],
    source_projects_unchanged=True, observations=observations, observed_roles=list(labels), route_rows=route_rows,
    positive_exports=export_rows, GUI_process_journals=GUI_journals, missed_observations=observer_rows,
    privacy=privacy, reference_records=reference_records, additional_complete_costs=extra_costs,
    original_source_rights=dict(owned=required['owned_source_rights'],Interf=required['repair_source_rights']),
    known_defect='Immutable034 review/choice/export summaries mislabel stage budget as method budget; commands/parent420/export120 correct. Root patch is future source only.',
    cancellation='33ec completed accepted without eligible observed phase or Cancel. Both finite observers and complete extra attempt retained; no cancellation/comparative win claimed. Fresh cancellation belongs to future035 qualification.',
    metadata_scope='Final replay covers3 completed parent Route roots,1 current no-repair export validation and8 owned plot events. Editor-stale repair export has frozen preopen proof only, no current metadata/acceptance claim.',
    AI_review_scope='Prior interim and patch reviews retained; curator author also authored those receipts. They are AI-only, not an independent review of this resulting packet or human PCB review.',
    cost_scope='Parent and CLI command/worker times retained; nested costs are not separate additive runs. Both45second observers and preparation/readback logs additional. Whole interactive wall/fullCPU including authoring/idle/observation/AI/curation unmeasured, not zero; no speed claim.',
    scope='Two exposed functional sources, exact4/25 source files, locked1/0 under whole scope. Own current034 parent/incumbent/trial/final Native and exports only;22warnings/seven ignored checks remain. Ordinary075 and preworkspace refusals separate. No fullGUI, breadth/superiority, all-phase/SIGINT-only/forcedqueue, human/electrical/Windows/restoration/release claim.',
    curation_wall_seconds_before_publication=time.monotonic()-started,
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
assert len(prl_packets)==4 and len(prl_pairs)==8
local.check_final_events(prl_packets,p.c.CLI,pairs=prl_pairs)
with packet_path.open('x') as stream: json.dump(record,stream,indent=2); stream.write('\n')
print(json.dumps(dict(files=len(files),bytes=total,material=len(material),actual_GUI_recovery_delivery=True,
    recovery_cancellation_qualified=False,full_GUI_qualification=False)))
