"""Copy completed bounded text evidence; never execute Native or acceptance readers."""
from pathlib import Path
import hashlib
import json
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import placement_clearance as pc

STARTED = time.monotonic()
CPU_STARTED = time.process_time()
NOTES = ROOT / 'evidence/task-copper-fixed-native-001-notes'
OWNED_ROOTS = (
    'task-copper-fixed-probe-001', 'task-copper-fixed-native-001',
    'task-copper-fixed-alias-native-001', 'task-copper-fixed-alias-native-002',
    'task-copper-fixed-alias-native-003', 'task-copper-fixed-alias-native-004',
    'task-copper-fixed-invalid-001',
)
NUS_ROOTS = ('task-copper-fixed-nus-probe-001', 'task-copper-fixed-nus-native-001')
GENERATED = {'kicad-config', 'kicad-cache', 'kicad-documents', '__pycache__'}
LIMIT = 32 * 1024 * 1024
MAX_FILES = 3000
COPIES = {}
EXCLUDED = []
SOURCE_INVENTORIES = {}
SOURCE_PROJECTS = {}
EXPECTED = {
    'task-copper-fixed-probe-001': ('invalidated', False),
    'task-copper-fixed-native-001': ('routing_accepted', True),
    'task-copper-fixed-alias-native-001': ('rejected', False),
    'task-copper-fixed-alias-native-002': ('drc_rejected', False),
    'task-copper-fixed-alias-native-003': ('drc_rejected', False),
    'task-copper-fixed-alias-native-004': ('routing_accepted', True),
    'task-copper-fixed-nus-probe-001': ('invalidated', False),
    'task-copper-fixed-nus-native-001': ('routing_accepted', True),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def inventory(folder):
    return pc.inventory(folder, max_bytes=LIMIT, max_files=MAX_FILES,
                        max_entries=MAX_FILES * 2)


def local_pin(path):
    raw = pc.read_bytes(path, 4 * 1024 * 1024)
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': digest(raw)}


def text_file(source, relative):
    relative = Path(*('owned-run-evidence' if part == '.runs' else part
                      for part in Path(relative).parts))
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('curation target must be a relative owned path')
    raw = pc.read_bytes(source, 4 * 1024 * 1024)
    raw.decode('utf-8')
    if b'\0' in raw:
        raise ValueError('unexpected binary in selected text evidence')
    if re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)', raw):
        raise ValueError('possible credential in selected text: ' + str(source.relative_to(ROOT)))
    if sum(row['bytes'] for row in COPIES.values()) + len(raw) > LIMIT:
        raise ValueError('selected evidence exceeds32MiB')
    target = NOTES / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    if pc.read_bytes(target, 4 * 1024 * 1024) != raw:
        raise ValueError('curated copy differs')
    COPIES[str(relative)] = {
        'source': str(source.relative_to(ROOT)), 'bytes': len(raw),
        'sha256': digest(raw), 'byte_identical': True,
    }
    return str(relative)


def generated_json(relative, value):
    target = NOTES / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def counts(value):
    return {key: value.get(key) for key in ('opens', 'blocking', 'warnings', 'exclusions')}


def timing(value):
    return {key: value.get(key) for key in (
        'wall_seconds', 'parent_cpu_seconds', 'child_cpu_seconds',
        'monitor_cpu_seconds', 'total_cpu_seconds', 'control_child_cpu_seconds',
        'resource_accounting_point', 'resource_limitations') if key in value}


def result_summary(label):
    folder = ROOT / '.runs' / label
    result_path = folder / 'route/result.json'
    result = json.loads(pc.read_bytes(result_path))
    if (result['status'], result['accepted']) != EXPECTED[label]:
        raise ValueError('retained terminal status differs: ' + label)
    process = json.loads(pc.read_bytes(folder / 'process.json'))
    if process.get('cleanup_complete') is not True:
        raise ValueError('completed process cleanup receipt required')
    protection = result.get('protected_route_import', {})
    hashes = sorted(row['non_uuid_sha256'] for row in protection.get('matches', []))
    candidate = Path(result['candidate']) if result.get('candidate') else None
    candidate_pin = local_pin(candidate) if candidate else None
    if candidate_pin and candidate_pin['sha256'] != result['candidate_sha256']:
        raise ValueError('retained candidate differs')
    summary = {
        'local_run': str(folder.relative_to(ROOT)),
        'recorded_status': result['status'], 'recorded_accepted': result['accepted'],
        'recorded_reason': result.get('reason'),
        'recorded_native_rejection_reasons': result.get('native_rejection_reasons'),
        'native_counts': counts(result.get('native', {})),
        'source_native_counts': counts(result.get('source_drc', {})),
        'whole_project_drc_clean': result.get('whole_project_drc_clean'),
        'candidate': candidate_pin, 'result': local_pin(result_path),
        'source_file': local_pin(Path(result['source'])),
        'source_files_sha256': result['source_hashes'],
        'protected_route_match_count': len(hashes),
        'protected_route_unique_hash_count': len(set(hashes)),
        'protected_non_uuid_record_sha256': hashes,
        'protected_hash_list_sha256': digest(canonical_json(hashes)),
        'protected_imported_file_sha256': protection.get('imported_sha256'),
        'transplanted_routes_sha256': protection.get('transplanted_routes_sha256'),
        'recorded_route_timing': timing(result),
        'recorded_outer_process': {key: process.get(key) for key in (
            'status', 'exit_code', 'wall_seconds', 'cpu_seconds',
            'supervisor_cpu_seconds', 'monitor_cpu_seconds', 'cleanup_complete',
            'resource_accounting', 'log_bytes', 'log_truncated')},
        'runtime_implementation_sha256': result['tools']['implementation_sha256'],
        'tool_file_sha256': result['tools']['files'],
        'kicad': result['tools']['kicad'], 'freerouting': result['tools']['freerouting'],
        'receipt_scope': 'Retained recorded outcomes and file hash readback only; no new acceptance reader, Native or engine execution.',
    }
    return result, summary


# Exclusive output: a failed or repeated curation never replaces an earlier packet.
NOTES.mkdir(exist_ok=False)
owned_summaries = {}
for label in OWNED_ROOTS:
    folder = ROOT / '.runs' / label
    before = inventory(folder)
    SOURCE_INVENTORIES[label] = before
    for name, pin in before.items():
        source = folder / name
        generated = (set(Path(name).parts) & GENERATED or
                     Path(name).suffix in {'.pyc', '.pyo'} or Path(name).name == '.DS_Store')
        if generated:
            EXCLUDED.append({**local_pin(source),
                             'reason': 'generated KiCad configuration/cache/documents or Python/OS cache; retained locally'})
            continue
        copied = text_file(source, Path(label) / name)
        if COPIES[copied]['sha256'] != pin:
            raise ValueError('source inventory/copy differs')
    if label.endswith('invalid-001'):
        record = json.loads(pc.read_bytes(folder / 'record.json'))
        if not (record['passed'] is True and record['accepted'] is False and
                record['routing_accepted'] is False and record['changed_import_rejected'] is True and
                record['source_unchanged'] is True):
            raise ValueError('retained deliberately invalid control changed')
        owned_summaries[label] = {
            'record': local_pin(folder / 'record.json'),
            'passed_negative_control': True, 'accepted': False,
            'changed_import_rejected': True, 'reason': record['reason'],
            'native_counts': counts(record['native']),
            'measured_postsetup_timing': timing(record),
            'cost_scope': 'Postsetup measurement only; source authoring/setup and whole-job cost are outside this record, not zero.',
            'scope': 'In-format v3 capping no-to-yes control: geometric Native DRC does not establish original manufacturing intent; strict original guard refused.',
            'runtime_implementation_sha256': record['tools']['implementation_sha256'],
        }
    else:
        _, owned_summaries[label] = result_summary(label)
    if inventory(folder) != before:
        raise ValueError('completed owned evidence changed during curation')

for label in NUS_ROOTS:
    folder = ROOT / '.runs' / label
    before = inventory(folder)
    SOURCE_INVENTORIES[label] = before
    allowed = {'protocol.json', 'process.json'}
    if label == 'task-copper-fixed-nus-native-001':
        allowed.add('command.log')
    for name in allowed:
        raw = pc.read_bytes(folder / name)
        if any(token in raw for token in (b'"pos":', b'"comparison_map":', b'(kicad_pcb', b'(kicad_sch')):
            raise ValueError('unexpected NUS geometry in selected metadata')
        text_file(folder / name, Path('nus-metadata') / label / name)
    for name in before:
        if name in allowed:
            continue
        reason = ('raw probe command.log contains Native findings with positions and field comparison payload; hash only, original retained locally'
                  if name == 'command.log' else
                  'NUS metadata-only scope: no CAD, DSN/SES, Native report geometry, captured runtime payload or other raw run files copied; original retained locally')
        EXCLUDED.append({**local_pin(folder / name), 'reason': reason})
    result, summary = result_summary(label)
    source = Path(result['source'])
    original = inventory(source.parent)
    if original != result['source_hashes']:
        raise ValueError('NUS original source differs from retained source hashes')
    SOURCE_PROJECTS[str(source.parent.relative_to(ROOT))] = original
    summary.update({
        'kind': 'NUS-geometry-free-retained-outcome-metadata',
        'original_source_unchanged': True,
        'complete_local_run_files': len(before),
        'complete_local_run_inventory_sha256': digest(canonical_json(before)),
        'copied_raw_files': sorted(allowed),
        'scope': 'Protocol/process and geometry-free normal command.log only, plus this authored summary. The raw probe command.log is excluded; this summary is not its byte-identical replacement.',
        'comparison_scope': 'Exposed original already had zero Native opens; support/preservation control only, not added routing completion or B2 superiority.',
        'prototype_scope': 'The experimental probe is production-invalidated despite geometric Native zero opens/blocking. Only the separate normal producer records acceptance.',
    })
    generated_json(Path('nus-metadata') / label / 'summary.json', summary)
    if inventory(folder) != before or inventory(source.parent) != original:
        raise ValueError('NUS retained evidence/source changed during curation')

generated_json('case-summary.json', {
    'schema': 1, 'kind': 'authored-summary-of-retained-owned-control-records',
    'cases': owned_summaries,
    'qualification': 'Both probe outcomes remain production-invalidated. Three alias prerequisite failures remain failures. Alias004 is a newly authored literal-field-parity control with its own runtime pins. No new Native or acceptance execution.',
})
generated_json('exclusions.json', {
    'schema': 1, 'excluded_files': EXCLUDED,
    'remaining_raw_evidence': 'All source directories and excluded files remain unchanged on this Mac. This selected packet is not an independent disk-failure backup.',
})
for name in (
    'LICENSE', 'experiments/task_copper_fixed_v1/COPYING',
    'experiments/task_copper_fixed_v1/README.md',
    'experiments/task_copper_fixed_v1/fixture.py',
    'experiments/task_copper_fixed_v1/driver.py',
    'experiments/task_copper_fixed_v1/native_probe.py',
    'experiments/legacy_via_import_v1/COPYING',
    'experiments/legacy_via_import_v1/fixture.py',
):
    text_file(ROOT / name, Path('source-notices') / name)
text_file(Path(__file__), Path('controllers/curate-task-copper-fixed-native-001.py'))
scope = """# Task-copper fidelity evidence packet

This is a byte-preserving selection of completed local evidence, not a new Native run or acceptance reader. `files.json` inventories every selected file except itself. Copy provenance includes the original path and exact byte hash. Destination filenames map any `.runs` component to `owned-run-evidence`; copied contents remain unchanged.

The seven owned control roots contain project-owned GPL-3.0-or-later generated designs. The grant in `experiments/task_copper_fixed_v1/fixture.py` explicitly covers its factory and generated design; it derives from the owned legacy-via/complete-schematic transport factory. The repository `LICENSE`, both experiment `COPYING` files, current fixture/controller source and their notices are copied under `source-notices`. Captured runtime source retains its own notices. These owned cases contain no third-party board payload. NUS CAD and library payload are not included.

The owned roots preserve source/snapshot/candidate projects, DSN/SES, exact Native reports and input bindings, captured runtime code, protocols and logs. Both experimental probes reached zero Native opens/blocking findings but are deliberately production-invalidated for their unadmitted worker/alias artifact contract. Their results are not product passes. The separate normal owned and NUS records retain production acceptance with warnings visible. This curation does not revalidate those records.

All three alias prerequisites remain separate failures:001 failed strict protected-route reconstruction after noncanonical free-field ordering;002 retained ten warnings and DRC refusal including field mismatch after the library prerequisite;003 retained six Datasheet warnings and DRC refusal because the narrow existing field qualifier did not cover the added board-only footprints.004 is a newly authored source with literal field parity, then zero Native opens/blocking/warnings and recorded acceptance. No earlier source, warning or result was repaired in place. Every record keeps its own producer hashes; later helper-decoder pins differ from the first owned/NUS proofs.

The deliberately invalid owned control changes an imported protected via's capping from no to yes in the qualified v3 format. Actual full-schematic Native evidence has zero opens/blocking with six warnings, while the strict original-route guard rejects the changed manufacture intent. `passed` means the negative control behaved as required, never routing acceptance or Native approval of manufacturing intent. Its recorded timing measures postsetup work only; source authoring/setup is outside that cost, not zero and not whole-job cost.

`nus-metadata` contains only the selected protocols/process journals, the geometry-free normal command.log and authored geometry-free summaries with counts, hashes and timings. The probe command.log contains Native positions/field comparison payload, so it is excluded with its exact hash and reason. No NUS source/candidate/DSN/SES, Native report geometry or runtime payload is copied. The summaries contain recorded Native counts, source/candidate hashes, protected-record hash counts/lists and runtime pins only. The unchanged exposed NUS source already had zero Native opens: this is a preservation/support gain, not gained routing completion. All omitted NUS files have individual hashes and reasons in `exclusions.json`.

Generated KiCad configuration/cache/documents and Python/OS cache files are excluded with individual hashes. Every source root is inventoried before and after curation; NUS original-source hashes are checked against its recorded inventory. Original roots and all excluded files remain on this Mac. This selected public packet is not an independent disk-failure backup.

No new Native/JVM/engine/test/CI/network execution occurs. Recorded route/outer-process timings are distinct; curation costs cover only this script and exclude read preparation/authoring/review. No broad B2 superiority, new independent board family, human PCB review, GUI interaction, Windows qualification, electrical or physical validation is claimed.
"""
with (NOTES / 'SCOPE.md').open('x') as stream:
    stream.write(scope)

before_manifest = inventory(NOTES)
rows = []
for name, pin in before_manifest.items():
    row = {'path': name, 'bytes': (NOTES / name).stat().st_size, 'sha256': pin}
    row.update(COPIES.get(name, {'source': 'authored curation metadata; not an executed Native receipt'}))
    rows.append(row)
generated_json('files.json', {
    'schema': 1, 'kind': 'bounded-owned-text-and-NUS-metadata-evidence-curation',
    'inventory_scope': 'Every selected file except this files.json; no self-hash claim.',
    'files': rows, 'files_count': len(rows), 'bytes': sum(row['bytes'] for row in rows),
    'owned_source_roots': list(OWNED_ROOTS), 'NUS_metadata_roots': list(NUS_ROOTS),
    'source_inventories_sha256': {name: digest(canonical_json(value))
                                for name, value in SOURCE_INVENTORIES.items()},
    'source_inventory_file_counts': {name: len(value) for name, value in SOURCE_INVENTORIES.items()},
    'NUS_original_source_inventories_sha256': {name: digest(canonical_json(value))
                                            for name, value in SOURCE_PROJECTS.items()},
    'excluded_files_count': len(EXCLUDED),
    'excluded_bytes': sum(row['bytes'] for row in EXCLUDED),
    'byte_identical_copies': len(COPIES),
    'new_native_execution': False, 'new_engine_execution': False,
    'new_test_execution': False, 'new_network_execution': False,
    'curation_wall_seconds_before_manifest_publication': time.monotonic() - STARTED,
    'curation_self_CPU_seconds_before_manifest_publication': time.process_time() - CPU_STARTED,
    'cost_scope': 'Curation script only, sampled before final manifest write. Read preparation, authoring and review are outside this cost; no routing-speed claim.',
})
final = inventory(NOTES)
if {name: pin for name, pin in final.items() if name != 'files.json'} != before_manifest:
    raise ValueError('selected material changed before final inventory')
for label, expected in SOURCE_INVENTORIES.items():
    if inventory(ROOT / '.runs' / label) != expected:
        raise ValueError('original run changed before final seal')
for name, expected in SOURCE_PROJECTS.items():
    if inventory(ROOT / name) != expected:
        raise ValueError('NUS original source changed before final seal')
print(json.dumps({
    'files_with_manifest': len(final),
    'bytes_with_manifest': sum((NOTES / name).stat().st_size for name in final),
    'files_json_sha256': final['files.json'], 'byte_identical_copies': len(COPIES),
    'excluded_files': len(EXCLUDED), 'excluded_bytes': sum(row['bytes'] for row in EXCLUDED),
    'curator_sha256': local_pin(Path(__file__))['sha256'],
    'Native_reexecuted': False, 'engine_reexecuted': False,
    'curation_complete_wall_seconds': time.monotonic() - STARTED,
    'curation_complete_self_CPU_seconds': time.process_time() - CPU_STARTED,
}))
