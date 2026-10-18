"""Retain the two completed explicit1007 API controls; no Native or new reader."""
import datetime
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as pc, sexpr as sx

BASE = ROOT / '.runs/runtime-directory-023'
RUNTIME = BASE / 'runtime'
NOTES = ROOT / 'evidence/runtime023-explicit1007-delivery-cancel-001-notes'
SUMMARY = ROOT / 'evidence/runtime023-explicit1007-delivery-cancel-001.json'
SOURCE_HEAD = '8c0c8468823751d9b5dc4c9a9c51b1d622269a27'
MANIFEST = '3df808e340dbe8c01ddebafe5c5c12583dc8d4d0cfea407c9252b0a89c41de81'


def load(path):
    return json.loads(path.read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def publish(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, 'Existing curated evidence differs: ' + str(path)
    else:
        with path.open('xb') as stream:
            stream.write(raw)


def timing(path):
    values = dict(line.split() for line in path.read_text().splitlines() if line.strip())
    assert set(values) == {'real', 'user', 'sys'}
    values = {key: float(value) for key, value in values.items()}
    assert all(math.isfinite(value) and value >= 0 for value in values.values())
    return dict(wall_seconds=values['real'], user_CPU_seconds=values['user'],
                system_CPU_seconds=values['sys'], full_CPU_seconds=round(values['user'] + values['sys'], 2),
                resolution_seconds=0.01)


references, reference_records = {}, []
for name in ('runtime015-explicit1007-delivery-001.json', 'runtime023-installed-CLI-001.json',
             'runtime023-installed-partial-CLI-001.json'):
    path = ROOT / 'evidence' / name
    old = load(path)
    reference_records.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path)))
    for row in old['files']:
        references.setdefault(row['sha256'], row['path'])
files, material, omitted, cases = [], [], [], []
new_bytes = 0


def copy(path, target):
    global new_bytes
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    assert len(raw) < 4 * 1024 ** 2 and b'\0' not in raw
    raw.decode('utf-8')
    pin = sha(raw)
    public = references.get(pin)
    if public is None:
        destination = NOTES / target
        publish(destination, raw)
        public = str(destination.relative_to(ROOT))
        references[pin] = public
        files.append(dict(path=public, bytes=len(raw), sha256=pin))
        new_bytes += len(raw)
        assert new_bytes < 12 * 1024 ** 2 and len(files) < 1000
    else:
        assert p.sha(ROOT / public) == pin
    material.append(dict(original=str(path.relative_to(ROOT)), retained=public, bytes=len(raw), sha256=pin))


prerequisite = ROOT / '.runs/kicad-1007-bundle-qualification-001/result.json'
signature = load(prerequisite)
assert signature['signature_verified'] and signature['notarization_verified']
assert signature['installed_app_changed'] is False and signature['production_pins_changed'] is False
copy(prerequisite, Path('prerequisite/signed-bundle-result.json'))
copy(ROOT / '.runs/run-runtime023-explicit1007-delivery-001.py', Path('controllers/enclosure.py'))
first_curator = NOTES / 'controllers/curate.py'
if first_curator.is_file():
    copy(first_curator, Path('controllers/curate.py'))
copy(NOTES / 'controllers/curation-first-failure.json', Path('controllers/curation-first-failure.json'))
copy(Path(__file__).resolve(), Path('controllers/curate-final.py'))
for case in ('delivery', 'cancel'):
    stem = 'runtime023-explicit1007-' + case + '-001'
    protocol_path = BASE / (stem + '-protocol.json')
    plan = load(protocol_path)
    outer_path = BASE / (stem + '-enclosure/result.json')
    outer = load(outer_path)
    out = RUNTIME / '.runs' / stem
    child_path = out / 'result.json'
    child = load(child_path)
    assert p.sha(protocol_path) == outer['protocol_sha256'] == child['protocol_sha256']
    assert plan['source_head'] == outer['source_head'] == child['source_head'] == SOURCE_HEAD
    assert plan['runtime_manifest_sha256'] == MANIFEST
    assert p.sha(RUNTIME / 'runtime-distribution.json') == MANIFEST
    assert p.sha(prerequisite) == plan['signature_prerequisite_sha256']
    assert signature['experimental_native_toolchain'] == plan['native_toolchain']
    assert plan['runtime_tools'] == child['tools']
    assert all(row['accepted'] is False and row['production_admitted'] is False and row['actual_GUI'] is False
               for row in (outer, child))
    assert pc.inventory(out / 'source') == plan['fixture_sha256']
    source = out / 'source' / plan['board_name']
    original = sx.read(source)
    execution = timing(ROOT / '.runs' / (stem + '-time.log'))
    preparation = timing(ROOT / '.runs' / (stem + '-prepare-time.log'))
    assert plan['preparation_publication_budget_charge_seconds'] == 4
    for key in ('wall_seconds', 'full_cpu_seconds'):
        assert outer[key] <= plan['limits']['whole_wall_full_cpu_seconds']
    for name, pin in outer['completed_evidence'].items():
        assert p.sha(out / name) == pin
    copy(protocol_path, Path(case) / 'protocol.json')
    for path in sorted((BASE / (stem + '-enclosure')).iterdir()):
        if path.is_file():
            copy(path, Path(case) / 'enclosure' / path.name)
    for path in sorted((BASE / (stem + '-preparation')).iterdir()):
        if path.is_file():
            copy(path, Path(case) / 'preparation' / path.name)
    for suffix in ('-time.log', '-prepare-time.log', '.log', '-prepare.log'):
        copy(ROOT / '.runs' / (stem + suffix), Path(case) / 'enclosing' / (stem + suffix))
    copied_child = RUNTIME / '.runs' / (stem + '-child.py')
    assert p.sha(copied_child) == plan['child_sha256']
    copy(copied_child, Path(case) / 'controller-child.py')
    for path in sorted(out.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(out)
        if any(part in ('code', 'kicad-config', 'kicad-cache', 'kicad-documents') for part in relative.parts):
            omitted.append(dict(path=str(path.relative_to(ROOT)), sha256=p.sha(path),
                reason='Captured runtime code already pinned by source/manifest, or generated job configuration/cache/documents; not recopied. Raw bytes remain local.'))
            continue
        if path.suffix in ('.json', '.log', '.net', '.svg', '.html', '.kicad_pcb', '.kicad_pro', '.kicad_prl', '.kicad_sch', '.kicad_dru'):
            copy(path, Path(case) / 'delivery' / relative)
    record = dict(case=case, raw_parent_status=outer['status'], raw_parent_passed=outer['passed'],
        raw_parent_accepted=outer['accepted'], raw_child_status=child['status'], raw_child_passed=child['passed'],
        raw_child_accepted=child['accepted'], production_admitted=False, actual_GUI=False,
        source_hashes=plan['fixture_sha256'], original_source_project_bytes_unchanged=True,
        complete_execution=execution, complete_preparation=preparation,
        complete_measured_execution_plus_preparation=dict(wall_seconds=round(execution['wall_seconds'] + preparation['wall_seconds'], 2),
            full_CPU_seconds=round(execution['full_CPU_seconds'] + preparation['full_CPU_seconds'], 2)),
        stored_parent_sample={key:outer[key] for key in ('execution_wall_seconds', 'execution_full_cpu_seconds',
            'charged_preparation_wall_seconds', 'charged_preparation_full_cpu_seconds', 'wall_seconds', 'full_cpu_seconds')},
        conservative_publication_budget_charge_seconds=plan['preparation_publication_budget_charge_seconds'],
        publication_charge_is_actual_consumption=False,
        limits=plan['limits'], protocol_sha256=p.sha(protocol_path), parent_receipt_sha256=p.sha(outer_path), child_receipt_sha256=p.sha(child_path))
    if case == 'delivery':
        assert outer['passed'] is True and child['passed'] is True
        assert outer['status'] == child['status'] == 'completed'
        route_path = out / 'route/result.json'
        export_path = out / 'export/export.json'
        route = load(route_path)
        export = load(export_path)
        assert p.sha(route_path) == child['route_sha256'] and p.sha(export_path) == child['export_sha256']
        assert route['accepted'] is True and export['export_accepted'] is True
        assert child['checked_export']['current'] is True and child['route_and_export_have_own_native_proof'] is True
        assert child['default_refusals'].keys() == {'route', 'review', 'choice', 'export'}
        protected = p.protected_for_record(route, original)
        assert len(protected) == child['protected_routes'] == len(route['protected_route_import']['matches']) == 1
        assert len(p.routes(original)) == 1 and len(plan['fixture_sha256']) == 4
        finals = []
        for label, folder, data in (('route', out / 'route', route), ('export', out / 'export/validation', export)):
            board = Path(data['candidate'])
            tree = sx.read(board)
            assert p.sha(board) == data['candidate_sha256'] == '1587bbb36142711b735b03292fc54e85ca169d8a58ca96431609d509594b5cb4'
            assert p.sha(folder / 'final-drc.json') == data['native_report_sha256']
            assert p.immutable(tree) == p.immutable(original)
            assert all(item in p.routes(tree) for item in protected)
            assert [data['native'][key] for key in ('opens', 'blocking', 'warnings', 'exclusions')] == [0, 0, 6, 0]
            assert data['schematic_parity'] == 'checked by final native DRC'
            finals.append(dict(stage=label, candidate_sha256=data['candidate_sha256'], native_report_sha256=data['native_report_sha256'],
                native=data['native'], metrics=data['metrics'], schematic_parity=data['schematic_parity'],
                protected_route_items=1, original_nonrouting_design_preserved=True))
        assert route['budget_seconds'] == 120 and 30 <= export['budget_seconds'] <= 60
        record.update(delivery_control_observed=True, own_final_proofs=finals,
            source_route_items=1, source_project_files=4, protected_route_items=1,
            protection_scope='Whole-board unlocked routing protects the fixture\'s one locked route record. The four project files are not four route records or four protected items.',
            actual_routing_allocation_seconds=route['budget_seconds'], actual_export_allocation_seconds=export['budget_seconds'],
            default_consumer_refusals=child['default_refusals'], checked_export=child['checked_export'],
            whole_project_drc_clean=export['whole_project_drc_clean'])
    else:
        request_path = BASE / (stem + '-request.json')
        request = load(request_path)
        process_path = out / 'route/source-drc-process.json'
        process = load(process_path)
        assert request['requested'] is True and request['signal'] == 'SIGINT'
        assert outer['passed'] is False and child['passed'] is False
        assert outer['status'] == child['status'] == process['status'] == 'cancelled'
        assert outer['cancellation_request_observed'] is True
        assert process['exit_code'] == -15 and process['cleanup_complete'] is True
        assert not (out / 'route/result.json').exists() and not (out / 'export').exists()
        copy(request_path, Path('cancel/request.json'))
        record.update(cancellation_control_observed=True, raw_cancellation_qualified=outer['cancellation_qualified'],
            observed_request=request, source_DRC_process={key:process[key] for key in ('status', 'exit_code', 'cleanup_complete', 'wall_seconds', 'cpu_seconds')},
            route_receipt_exists=False, export_directory_exists=False,
            staged_route_candidate_exists=(out / 'route/candidate' / plan['board_name']).is_file(),
            claim_scope='Observed SIGINT request to the owned parent during an owned1007 source-DRC worker; worker records cancelled/exit-15/cleanup complete, no accepted route/export. Raw passed=false/cancelled flags are intentionally retained. No SIGINT-only, permanent-descendant-absence, all-phase, GUI or Windows guarantee.')
    cases.append(record)

scope = '''# Runtime023 explicit KiCad10.0.7 delivery and cancellation controls

These are actual isolated, caller-pinned Native API controls using immutable runtime023 source8c0c8468823751d9b5dc4c9a9c51b1d622269a27 and manifest3df808e340dbe8c01ddebafe5c5c12583dc8d4d0cfea407c9252b0a89c41de81. The existing signed/notarized bundle prerequisite is unchanged. No installed production application, global configuration, security control or production pin was changed. This is not default production, GUI, Windows, broad current-stable support or routing-quality promotion. Runtime015's older API slice remains historical evidence.

The fresh positive records completed explicit-context Route, rendered review, software accept intent, fresh Native export, current readback and four default-consumer refusals. Both own finals have0 opens/0 blocking/6 warnings/0 exclusions and full schematic/original-rule proof. The fixture has four project files and one source route record, which is locked/protected. This is not the separate four-route partial-completion fixture. The actual allocations are120 seconds for routing and60 seconds for export, within the declared remaining30–60 export range and180-second whole bound.

Complete execution measures144.04 seconds wall and133.56 CPU; separate preparation measures0.51/.45. Earlier stored parent totals148.299479/137.780529 include preparation plus a conservative4-second publication budget charge. That charge is not measured consumption. Each measurement and the raw samples remain separate; do not add nested CPU or mistake charged totals for complete external time. Runtime preparation, authoring, AI review and this curation are additional costs, not zero.

The cancellation control records an actual SIGINT request to the owned parent while its owned1007 source-DRC worker was observed. Parent and child remain cancelled/accepted=false/passed=false; the worker reports cancelled/exit-15/cleanup complete. No route/result.json or export directory exists; an unaccepted staged candidate does exist. Complete cancellation execution measures2.29 wall/2.03 CPU, preparation0.57/.47. Raw cancellation_qualified=false is preserved. The curator labels only the observed control, not SIGINT-only termination, permanent descendant absence, all routing phases, GUI or Windows cancellation.

All new files are project-owned bounded text. Exact existing CAD/notice bytes are referenced by hashes rather than duplicated; application/engine/interpreter binaries and captured runtime source trees are not copied. Complete new process, Native, schematic, source/candidate, review/choice and request evidence is retained subject to explicit code/config/cache omissions. Raw originals remain on this Mac. This is evidence curation, not another verifier, relocated executable proof, new restoration test or claim that older backups cover newer raw work. Independent human review, cleanup timing and physical/electrical validation remain unperformed; formal release/contact/spending need separate approval.
'''
publish(NOTES / 'SCOPE.md', scope.encode())
copy(NOTES / 'SCOPE.md', Path('SCOPE.md'))
index = dict(schema=1, files=files, material=material, omitted=omitted,
             runtime_source_head=SOURCE_HEAD, runtime_manifest_sha256=MANIFEST,
             scope='Exact essential text curation and hash references only; no new admission/verifier.')
publish(NOTES / 'files.json', (json.dumps(index, indent=2) + '\n').encode())
record = dict(schema=1, kind='runtime023-explicit1007-delivery-and-observed-cancellation-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), accepted=False, project_complete=False,
    production_admitted=False, actual_GUI=False, human_review=False, broad_platform_support=False,
    source_head=SOURCE_HEAD, runtime_manifest_sha256=MANIFEST,
    full163=dict(path='evidence/export-budget-split-001.json', sha256=p.sha(ROOT / 'evidence/export-budget-split-001.json')),
    native_toolchain=signature['experimental_native_toolchain'], signed_bundle_prerequisite_sha256=p.sha(prerequisite),
    signed_bundle_prerequisite_reused=True, global_application_or_security_changes=False,
    cases=cases, reference_records=reference_records,
    limits=['Explicit isolated10.0.7 caller context only; default consumers refuse and production admission stays false.',
        'Whole-board control protects the one source route record; the four project files do not imply four-route partial preservation.',
        'Actual cancellation observation is restricted to source DRC; raw false/cancelled flags remain unchanged.',
        'No GUI, Windows, all-phase/permanent-descendant/SIGINT-only, independent-family or routing-superiority claim.',
        'No human engineer review, cleanup timing or physical/electrical qualification. Older raw backups do not cover new artifacts retroactively.'],
    accounting='Complete execution and preparation external wall/user/system measurements, raw samples and conservative4-second publication charge remain distinct. No nested CPU addition; authoring/review/curation and earlier runtime/bundle preparation are additional nonzero costs.',
    files=files, files_index=dict(path=str((NOTES / 'files.json').relative_to(ROOT)), sha256=p.sha(NOTES / 'files.json')),
    new_material_bytes=new_bytes)
publish(SUMMARY, (json.dumps(record, indent=2) + '\n').encode())
print(json.dumps(dict(summary=str(SUMMARY.relative_to(ROOT)), sha256=p.sha(SUMMARY),
                     files_index_sha256=record['files_index']['sha256'], files=len(files), bytes=new_bytes)))
