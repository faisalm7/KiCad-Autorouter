"""Copy bounded completed owned evidence; never run Native or acceptance readers."""
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import placement_clearance as pc

STARTED = time.monotonic()
CPU_STARTED = time.process_time()
NOTES = ROOT / 'evidence/legacy-via-import-native-001-notes'
ROOTS = (
    'legacy-via-native-001', 'legacy-via-native-002',
    'legacy-via-native-004', 'legacy-via-native-005',
    'legacy-via-observation-003', 'legacy-via-strict-red-001',
    'legacy-via-strict-red-002', 'legacy-via-green-001',
    'legacy-via-green-002', 'legacy-via-modern-positive-001',
    'legacy-via-explicit-positive-001', 'legacy-via-native-invalid-001',
    'legacy-via-delivery-001', 'default-map-prerequisite-001',
    'default-format-prerequisite-002', 'default-meta-prerequisite-003',
)
GENERATED_KICAD_DIRECTORIES = {'kicad-config', 'kicad-cache', 'kicad-documents'}
OPAQUE = '.runs/legacy-via-native-002/observation.json'
LIMIT = 15 * 1024 * 1024
MAX_FILES = 2000
COPIES = {}
EXCLUDED = []
SOURCE_INVENTORIES = {}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def text_file(source, relative):
    relative = Path(*('owned-run-evidence' if part == '.runs' else part
                      for part in Path(relative).parts))
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('curation target must be a relative owned path')
    raw = pc.read_bytes(source, 4 * 1024 * 1024)
    raw.decode('utf-8')
    if b'\0' in raw:
        raise ValueError('unexpected binary in selected text evidence')
    if sum(row['bytes'] for row in COPIES.values()) + len(raw) > LIMIT:
        raise ValueError('selected evidence exceeds15MiB')
    target = NOTES / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    if pc.read_bytes(target, 4 * 1024 * 1024) != raw:
        raise ValueError('curated copy differs')
    COPIES[str(relative)] = {
        'source': str(Path(source).relative_to(ROOT)),
        'bytes': len(raw), 'sha256': digest(raw), 'byte_identical': True,
    }


def generated_json(relative, value):
    target = NOTES / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def local_pin(path):
    raw = pc.read_bytes(path, LIMIT)
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': digest(raw)}


NOTES.mkdir(exist_ok=False)
for label in ROOTS:
    folder = ROOT / '.runs' / label
    inventory = pc.inventory(folder, max_bytes=LIMIT, max_files=MAX_FILES,
                             max_entries=MAX_FILES * 2)
    SOURCE_INVENTORIES[label] = inventory
    for name, pin in inventory.items():
        source = folder / name
        source_relative = str(source.relative_to(ROOT))
        reason = ('generated KiCad configuration/cache/documents, retained locally'
                  if set(Path(name).parts[:-1]) & GENERATED_KICAD_DIRECTORIES else
                  'invalid opaque-pointer interpretation; raw observation retained locally'
                  if source_relative == OPAQUE else None)
        if reason:
            EXCLUDED.append({**local_pin(source), 'reason': reason})
            continue
        text_file(source, Path(label) / name)
        if COPIES[str(Path(label) / name)]['sha256'] != pin:
            raise ValueError('source inventory/copy differs')
    if pc.inventory(folder, max_bytes=LIMIT, max_files=MAX_FILES,
                    max_entries=MAX_FILES * 2) != inventory:
        raise ValueError('completed source evidence changed during curation')

nus = ROOT / '.runs/legacy-via-nus-partial-001'
nus_inventory = pc.inventory(nus, max_bytes=LIMIT, max_files=MAX_FILES,
                             max_entries=MAX_FILES * 2)
for name in ('protocol.json', 'process.json', 'command.log'):
    text_file(nus / name, Path('nus-partial-metadata') / name)
nus_result_path = nus / 'route/result.json'
nus_result = json.loads(pc.read_bytes(nus_result_path))
difference_path = nus / 'import-difference.json'
difference = json.loads(pc.read_bytes(difference_path))
if nus_result.get('accepted') is not False or nus_result.get('status') != 'rejected':
    raise ValueError('NUS failure status changed; do not curate as a positive')
if tuple(difference.get(key) for key in ('original_routes', 'imported_routes',
        'missing_non_uuid_records', 'added_non_uuid_records')) != (47, 59, 21, 33):
    raise ValueError('NUS aggregate counterexample differs')
source = Path(nus_result['source'])
source_inventory = pc.inventory(source.parent, max_bytes=LIMIT, max_files=MAX_FILES,
                                max_entries=MAX_FILES * 2)
if source_inventory != nus_result['source_hashes']:
    raise ValueError('NUS original source differs from retained source hashes')
generated_json('nus-partial-metadata/summary.json', {
    'kind': 'retained-NUS-partial-refusal-metadata-only',
    'accepted': False, 'status': nus_result['status'], 'reason': nus_result.get('reason'),
    'original_routes': 47, 'imported_routes': 59,
    'missing_non_uuid_records': 21, 'added_non_uuid_records': 33,
    'diagnostic_only': True,
    'comparison_scope': 'Retained non-UUID diagnostic counts only; no geometric equivalence waiver.',
    'scope': 'Three selected metadata/log files only. No NUS source, candidate, DSN/SES or Native report geometry copied.',
    'actual_local_files': [local_pin(nus_result_path), local_pin(difference_path),
                           local_pin(nus / 'route/imported.kicad_pcb'),
                           local_pin(source)],
    'original_source_files_sha256': source_inventory,
    'original_source_unchanged': True,
    'complete_local_run_inventory_sha256': digest(canonical_json(nus_inventory)),
    'complete_local_run_files': len(nus_inventory),
    'local_run': str(nus.relative_to(ROOT)),
    'new_native_or_engine_execution': False,
    'limitations': 'NUS remains refused. Precision and free-via changes are not corrected by the legacy OFF-field policy. Raw unique evidence remains on this Mac, outside this selected public packet.',
})
if pc.inventory(nus, max_bytes=LIMIT, max_files=MAX_FILES,
                max_entries=MAX_FILES * 2) != nus_inventory:
    raise ValueError('NUS retained evidence changed during curation')

opaque = ROOT / OPAQUE
generated_json('exclusions.json', {
    'schema': 1, 'excluded_files': EXCLUDED,
    'opaque_observation': {
        **local_pin(opaque), 'interpretation_valid': False,
        'reason': 'The six mode getters returned SwigPyObject pointers. int() recorded pointer addresses, not enum values. These integers cannot establish manufacture modes or equality.',
        'replacement_evidence': ['legacy-via-observation-003/observation.json',
                                 'legacy-via-observation-003/serialized-vias.json',
                                 'legacy-via-native-004/observation.json'],
        'qualification': 'Later observations retain return types and actual separately saved Native boards. Getter enum-value access remains unqualified.',
    },
    'remaining_raw_evidence': 'All source directories and excluded files remain unchanged on this Mac. This selected packet is not an independent disk-failure backup.',
})
text_file(Path(__file__), Path('controllers/curate-legacy-via-native-001.py'))
scope = """# Protected legacy-via native evidence packet

This is a byte-preserving selection of completed local evidence, not a new Native run, a new acceptance reader, or a release qualification. `files.json` inventories every selected file except itself; the original source paths and copied byte hashes are retained. Copied `.runs` path components are named `owned-run-evidence` only in destination filenames; file contents remain unchanged.

The generated designs come from the project-owned complete-schematic transport factory and the GPL-3.0-or-later legacy-via fixture factory (`experiments/legacy_via_import_v1/fixture.py`); the grant explicitly covers generated designs. See the repository `LICENSE`, `experiments/legacy_via_import_v1/COPYING` and the factory notices. Captured runtime source retains its original notices. No third-party board/model/library payload is included in the owned control cases.

The sixteen case directories retain source projects, separately saved boards, exact candidate projects, captured runtime code, Native reports and input bindings, journals, command logs and protocols. Early setup failures, the strict importer failures, the first v3 DRC rejection and subsequent positive controls remain separate. The initial fixture's missing net-settings schema metadata caused the Native Default width to resolve to0.2mm; the first green case therefore remained rejected against its0.25mm minimum. Later newly authored controls declare the schema and resolve0.3mm. No retained source or failed result was repaired in place. The Default prerequisite records remain evidence of that distinction, not a general Default-class implementation change.

The legacy positive, modern-inherited positive and explicit-manufacture positive each retain their own actual pinned KiCad10.0.0 import/refill/full-schematic Native evidence. The legacy v3 case restores all three original protected records, including its exact literal via. Modern inheritance and explicit source values keep strictv2 handling. The invalid manufacture candidate has zero Native opens/blocking findings with six retained warnings, but preservation rejects it: DRC is not proof of manufacture intent. Its v3 refusal is the source-format boundary, not a claimed in-format changed-value Native control. Software matcher controls separately cover all six changed values and malformed/ambiguous imports.

`legacy-via-delivery-001` retains rendered review, software accept intent, fresh Native export and checked-export evidence for the legacy positive. This does not establish graphical interaction, live application/undo, human PCB approval or electrical/manufacturing suitability. All Native warnings, ignored checks and failures remain visible; zero opens/blocking findings is not whole-project cleanliness.

The original mode-getter observation in `legacy-via-native-002/observation.json` is excluded from the public packet, with its exact digest and invalid interpretation in `exclusions.json`. Its integer values were opaque pointer addresses, not enum values. The original file remains local. Later003/004 records preserve the `SwigPyObject` return types and actual saved serialization; they do not claim usable enum-value getters. Generated `kicad-config`, `kicad-cache` and `kicad-documents` directories are also excluded with individual hashes; these retained local generated preferences are not required source/Native proof.

`nus-partial-metadata` contains only the requested protocol, outer process journal, command log and a geometry-free aggregate summary. The actual real-board attempt remains rejected:47 source routes became59 imported routes, with21 missing and33 added non-UUID records in its retained diagnostic. No geometric equivalence or generic protected-copper support is inferred. Raw NUS source/candidates/DSN/SES and Native-report geometry remain local; original source hashes and exact local result/import/difference hashes bind the visible failure.

No new board family, comparison completion gain, cleanup-time improvement, routing-quality superiority, Windows support, human review or physical validation is claimed. This curation executes no Native/JVM/engine/test/CI/network job. Preparation, authoring, review and curation costs are separate from actual routing/runtime receipts. All originals and excluded evidence remain preserved; later raw artifacts are Mac-only unless a later backup receipt explicitly captures them.
"""
with (NOTES / 'SCOPE.md').open('x') as stream:
    stream.write(scope)

inventory = pc.inventory(NOTES, max_bytes=LIMIT, max_files=MAX_FILES,
                         max_entries=MAX_FILES * 2)
rows = []
for name, pin in inventory.items():
    path = NOTES / name
    row = {'path': name, 'bytes': path.stat().st_size, 'sha256': pin}
    if name in COPIES:
        row.update(COPIES[name])
    else:
        row['source'] = 'authored curation metadata; not an executed Native receipt'
    rows.append(row)
manifest = {
    'schema': 1, 'kind': 'bounded-owned-text-evidence-curation',
    'inventory_scope': 'All selected files except this files.json; no self-hash claim.',
    'files': rows, 'files_count': len(rows), 'bytes': sum(row['bytes'] for row in rows),
    'source_roots': list(ROOTS), 'source_inventories_sha256': {
        name: digest(canonical_json(value)) for name, value in SOURCE_INVENTORIES.items()},
    'new_native_execution': False, 'new_engine_execution': False, 'new_test_execution': False,
    'curation_wall_seconds_before_manifest_publication': time.monotonic() - STARTED,
    'curation_self_CPU_seconds_before_manifest_publication': time.process_time() - CPU_STARTED,
    'cost_scope': 'Curation script only, sampled before final manifest write. Research/read preparation and authoring are not included; no routing-speed claim.',
}
generated_json('files.json', manifest)
final = pc.inventory(NOTES, max_bytes=LIMIT, max_files=MAX_FILES,
                     max_entries=MAX_FILES * 2)
if {name: pin for name, pin in final.items() if name != 'files.json'} != inventory:
    raise ValueError('selected material changed before final inventory')
print(json.dumps({'files_with_manifest': len(final), 'bytes_with_manifest': sum(
    (NOTES / name).stat().st_size for name in final),
    'files_json_sha256': final['files.json'], 'excluded_files': len(EXCLUDED),
    'Native_reexecuted': False, 'engine_reexecuted': False,
    'curation_complete_wall_seconds': time.monotonic() - STARTED,
    'curation_complete_self_CPU_seconds': time.process_time() - CPU_STARTED}))
