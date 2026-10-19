"""Bounded, byte-preserving curation of one completed GUI037 positive.

No routing, Native, GUI, test, network, or archive inspection is performed.
The existing retain/tree/cost helpers are AST-extracted without running their
original controller. All selected payloads are preflighted before copying.
"""
from pathlib import Path
import ast, datetime, hashlib, json, re, sys

ROOT = Path(__file__).resolve().parents[2]
notes = Path(__file__).resolve().parent
summary_path = ROOT / 'evidence/gui-runtime037-077-positive-001.json'
assert not summary_path.exists()
assert sorted(q.name for q in notes.iterdir()) == ['curate.py']
runtime = ROOT / '.runs/runtime-directory-037/runtime'
sys.dont_write_bytecode = True
sys.path.insert(0, str(runtime))
from autorouter import pipeline as p, floor_route as f, placement_clearance as io

helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
module = ast.parse(helper.read_bytes())
definitions = [n for n in module.body if isinstance(n, ast.FunctionDef)
               and n.name in {'retain', 'tree', 'cost'}]
assert {n.name for n in definitions} == {'retain', 'tree', 'cost'}
refs = {}; files = []; material = []; total = 0
exec(compile(ast.Module(body=definitions, type_ignores=[]), str(helper), 'exec'))
real_retain = retain
selected = []
def retain(q, name):
    selected.append((Path(q), Path(name)))

prior = ROOT / 'evidence/runtime037-hierarchy-native-milestone-001.json'
assert p.sha(prior) == 'b5e53cad5e71e29b2dd80ab65eab34c699dd4dd39cad5d9c61f0c59dab3af868'
prior_record = f.read_json(prior)
index = ROOT / prior_record['files_index']['path']
assert p.sha(index) == prior_record['files_index']['sha256'] == 'c445d02ae6a9e8377df7c59c0fbc464b0d5143f4cb3b9127da6e5a2891fd0245'
prior_index = f.read_json(index)
for row in prior_index['files']:
    refs.setdefault(row['sha256'], row['path'])
for row in prior_index['material']:
    refs.setdefault(row['sha256'], row['retained'])

session = runtime / '.runs/gui-session077'
workspace = session / 'jobs/autorouter-gui-a97a659983354c8591534336b9784cd3'
copy = session / 'preopen-positive-export-001'
manifest = runtime / 'runtime-distribution.json'
assert p.sha(manifest) == 'c1ef6a1e1f47d03e39ca63c3114707889d86a3269fbccf5dcc9cec9ccfcba940'
manifest_record = f.read_json(manifest)
assert manifest_record['build_source']['git_head'] == 'c3e7e8ef4dadce1f83f838322fb5d685ce3714ac'
assert len(manifest_record['immutable_files_sha256']) == 52
for rel, digest in manifest_record['immutable_files_sha256'].items():
    assert p.sha(runtime / rel) == digest
    retain(runtime / rel, Path('runtime037/immutable') / rel)
retain(manifest, Path('runtime037/runtime-distribution.json'))

receipt_pins = {
    'preopen-positive-001.json': 'c1127133367ac861b4079f77a1bf6479b80169a025414fe7409ca236a2a2ee83',
    'postopen-positive-001.json': 'f9a41861418e75f42e092272458683e1a3c0e8ba582bf26cc973aa3f663d140d',
    'postclose-positive-001.json': 'ed2681fd2fe85746a9a31ba8a43d69af8bbb68e907c8360d763f13d070a8b170',
}
receipts = {}
for name, digest in receipt_pins.items():
    q = session / name
    assert p.sha(q) == digest
    receipts[name] = f.read_json(q)
    retain(q, Path('observations') / name)
before = receipts['preopen-positive-001.json']
after = receipts['postclose-positive-001.json']
access = ROOT / '.runs/gui-runtime037-077-access-002.json'
assert p.sha(access) == 'df6ea87d20793fa938d6e6642e4ff7463c27c6ec2f49f8eaf39f2a52b70898b5'
retain(access, Path('observations') / access.name)
for name in ['prepared-state.json', 'route-settings.json',
             'prepare-launcher-process.json', 'prepare-launcher.log']:
    retain(session / name, Path('preparation') / name)
for name in ['gui037-positive-preopen-001.log', 'gui037-positive-preopen-001-time.log',
             'gui037-positive-postclose-001.log', 'gui037-positive-postclose-001-time.log']:
    retain(ROOT / '.runs' / name, Path('readback-costs') / name)

route = f.read_json(workspace / 'route/result.json')
export = f.read_json(copy / 'export.json')
candidate_sha = '2281e2d9baec054e149199805b2e691c12baf77105a3dda6e4afc9c6a457b823'
assert route['accepted'] and export['export_accepted']
assert route['candidate_sha256'] == export['candidate_sha256'] == candidate_sha
assert route['source_hashes'] == export['source_hashes']
source_inventory = io.inventory(session / 'project')
assert source_inventory == route['source_hashes']
tree(session / 'project', Path('original-source'))
for q in sorted(workspace.iterdir()):
    if q.is_file():
        retain(q, Path('workspace-commands') / q.name)
excluded = []
skip = {'kicad-cache', 'kicad-config', 'kicad-documents', 'engine-config', 'tmp', '__pycache__'}
for stage in ['route', 'review', 'choice']:
    folder = workspace / stage
    inv = io.inventory(folder, max_bytes=64 * 1024**2)
    for rel, digest in inv.items():
        q = folder / rel
        if set(Path(rel).parts) & skip:
            excluded.append(dict(path=str(q.relative_to(ROOT)), bytes=q.stat().st_size,
                                 sha256=digest, reason='Isolated intermediate configuration/cache/documents; not required copied proof.'))
        else:
            retain(q, Path('workspace') / stage / rel)

# Preserve every byte of the BEFORE-OPEN export, including its eight isolated
# job-created configuration JSONs. The copy itself is not a relocated pass.
copy_inventory = io.inventory(copy, max_bytes=4 * 1024**2)
assert copy_inventory == before['export_preopen_hashes']
assert len(copy_inventory) == 84
copy_bytes = sum((copy / rel).stat().st_size for rel in copy_inventory)
assert copy_bytes == 1393260
for rel in copy_inventory:
    retain(copy / rel, Path('before-open-export') / rel)
current_inventory = io.inventory(workspace / 'export', max_bytes=4 * 1024**2)
assert current_inventory == after['export_after']
assert p.sha(workspace / 'export/validation/candidate/owned1007-transport.kicad_pcb') == candidate_sha
assert before['route_readback']['current'] and before['export_readback']['current']
assert after['postclose_export_readback']['current'] is False
assert after['postclose_export_readback']['error'] == 'Rejected: export inputs/runtime/evidence changed'
assert before['source_unchanged'] and after['source_project_unchanged'] and after['PCB_unchanged']
for rel in after['changed']:
    q = workspace / 'export' / rel
    if q.suffix == '.zip':
        excluded.append(dict(path=str(q.relative_to(ROOT)), bytes=q.stat().st_size,
                             sha256=current_inventory[rel], reason='KiCad-created post-open backup ZIP; hash/size only, archive not opened or published.'))
    else:
        assert q.suffix in {'.kicad_pro', '.kicad_prl'}
        retain(q, Path('after-close-changes') / rel)

# Preflight only this finite source/positive workspace. No historical/archive
# enumeration, secret-bearing browser context, or screenshot payload is read.
secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16})')
new_unique = {}; seen_original = set()
for q, name in selected:
    assert q.is_file() and not q.is_symlink()
    raw = io.read_bytes(q, 4 * 1024**2)
    assert b'\0' not in raw
    raw.decode('utf-8')
    assert not secret.search(raw), str(q)
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in refs:
        new_unique.setdefault(digest, len(raw))
    seen_original.add(str(q.relative_to(ROOT)))
assert sum(new_unique.values()) + 1024**2 < 16 * 1024**2
assert len(selected) < 2000
for q, name in selected:
    real_retain(q, name)

scope = '''# GUI runtime037 / session077: one ordinary positive

This packet retains one observed owner-assisted toolbar/ordinary Route/review/
explicit acceptance-intent/fresh Native export/open path. Runtime037 is the
immutable c3e7e8ef build; source and all four protected routes remain unchanged.
The preopen receipt observed current Route/export before KiCad opened the result.
All 84 preopen export files (1,393,260 bytes) are retained or hash-linked, including
the isolated job configuration. Their copied location is preservation, not a new
relocation qualification. The source is a project-owned generated GPL fixture;
the exact runtime LICENSE is retained by a verified prior public payload link.

Opening and closing the exported project changed its PRO/PRL and created a ZIP.
The exported PCB stayed byte-identical. The after-close readback correctly refuses
the current export as stale. The changed text is separate; the unopened ZIP has
only a hash/size entry. No post-open Native run is claimed.

Rendered Chrome front/back and KiCad editor views were observed in the CUA
transcript. No screenshot files exist here and none are fabricated. Browser AX,
bookmarks, private browser data and screenshots are not published. Access002 is
an earlier unsuccessful automated toolbar attempt; later owner assistance enabled
the positive path. This is AI curation of actual observations, not human PCB review.

This is not full GUI qualification. Rejection, cancellation, stale source/settings/
export, recovery, high-budget and hierarchy GUI controls remain pending for this
record. A changed build needs fresh GUI evidence. No family gain, broad quality,
electrical, physical, Windows or full product admission follows from this fixture.

The completed Route/review/choice/export costs are nested process observations,
not a measured total interactive session. Whole interactive wall/CPU is unknown,
not zero. Before-open preservation and after-close readback costs are separate.
Only this finite workspace and explicit runtime filenames were inspected. Shared
retention helpers are reused unchanged. No Native, GUI, route, test, build or CI
execution occurred during curation. Raw originals are unmodified and remain on Mac;
this essential text packet is not a full raw backup/restoration or formal release.
'''
with (notes / 'SCOPE.md').open('x') as stream:
    stream.write(scope)
for q in [Path(__file__), notes / 'SCOPE.md']:
    raw = q.read_bytes()
    files.append(dict(path=str(q.relative_to(ROOT)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    total += len(raw)
for row in material:
    assert p.sha(ROOT / row['original']) == row['sha256'] == p.sha(ROOT / row['retained'])
for row in files:
    assert p.sha(ROOT / row['path']) == row['sha256']
p.save_json(notes / 'files.json', dict(schema=1, files=files, material=material,
    exclusions=excluded, preflight=dict(selected_file_occurrences=len(selected),
    distinct_original_files=len(seen_original), new_payload_unique_bytes=sum(new_unique.values()),
    maximum_file_bytes=4 * 1024**2, packet_ceiling_bytes=16 * 1024**2,
    UTF8_no_NUL=True, selected_material_secret_pattern_check=True,
    browser_private_context_read=False, screenshots_copied=False)))

def stage_cost(j):
    return dict(wall_seconds=j['wall_seconds'], CPU_seconds=j['total_cpu_seconds'],
                scope='Recorded completed operation; nested subprocess costs not added again.')
summary = dict(schema=1, kind='actual-GUI-runtime037-session077-one-ordinary-positive',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_head=manifest_record['build_source']['git_head'],
    runtime_manifest_sha256=p.sha(manifest), native_version='10.0.7',
    runtime_modules=47, runtime_immutable_files=52,
    observed_positive=True, actual_GUI_fully_qualified=False, project_complete=False,
    human_PCB_review=False, physical_electrical_validation=False,
    workspace=str(workspace.relative_to(ROOT)), candidate_sha256=candidate_sha,
    source_hashes=route['source_hashes'], source_unchanged=True,
    observations=before['actual_GUI_observations'] + [
        'GUI checked Open launched the exact exported project in KiCad manager; Tools > PCB Editor rendered the candidate with 6 pads, 1 via, 6 track segments, 3 nets and 0 unrouted.',
        'Cmd-W then Close Project left manager with no project loaded; no board edit/save was requested.'],
    earlier_access=dict(path=str(access.relative_to(ROOT)), sha256=p.sha(access),
        scope='Earlier automatic toolbar attempts failed; later owner assistance enabled the positive. Not a current no-window gate.'),
    Route=dict(accepted=True, native=route['native'], protected_records=4,
        schematic_parity=route['schematic_parity'], candidate_sha256=candidate_sha,
        complete_operation_cost=stage_cost(route)),
    review=dict(status=f.read_json(workspace / 'review/review.json')['status'],
        complete_operation_cost=stage_cost(f.read_json(workspace / 'review/review.json')),
        human_review=False),
    choice=dict(choice='accept', applied=False, human_pcb_approval_observed=False,
        complete_operation_cost=stage_cost(f.read_json(workspace / 'choice/choice.json')),
        meaning='Explicit acknowledgement and acceptance intent; not a human PCB approval or source application.'),
    before_open_export=dict(observed_current=True, export_accepted=True,
        native_validation_performed=True, schematic_parity=export['schematic_parity'],
        native=export['native'], applied=False, candidate_sha256=candidate_sha,
        full_copy_files=84, full_copy_bytes=copy_bytes,
        complete_operation_cost=stage_cost(export),
        copied_location_is_not_a_relocation_qualification=True),
    after_open_and_close=dict(PCB_unchanged=True, source_unchanged=True,
        changed=after['changed'], current_export_readback=after['postclose_export_readback'],
        fresh_Native_after_open=False,
        meaning='Current export is stale after KiCad project-file changes; earlier preopen proof remains separately preserved.'),
    screenshots=dict(files=[], observed_only_in_CUA_transcript=True,
        public_browser_AX_or_bookmarks=False, fabricated=False),
    accounting=dict(interactive_whole_wall_seconds=None, interactive_whole_CPU_seconds=None,
        unknown_is_not_zero=True, nested_costs_not_summed=True,
        preopen_readback_and_copy=cost(ROOT / '.runs/gui037-positive-preopen-001-time.log'),
        postclose_readback=cost(ROOT / '.runs/gui037-positive-postclose-001-time.log'),
        curation_and_authoring_additional_unmeasured=True),
    pending=['GUI reject and active cancellation', 'Current source/settings/export freshness controls',
        'Recovery and high-budget GUI controls', 'Hierarchy GUI path',
        'Fresh GUI evidence after product source changes'],
    prior_native_packet=dict(path=str(prior.relative_to(ROOT)), sha256=p.sha(prior),
        files_index_sha256=p.sha(index)),
    rights='Project-owned GPL generated fixture and project code only; exact LICENSE preserved through verified payload link. No private CAD/browser inputs or downloaded tools.',
    limits='One observed ordinary GUI positive; no full qualification, independent family/comparison/quality gain, human/electrical/physical/Windows admission or new-build promotion. Postclose current export refuses. Essential text retention only; full raw Mac-only, no new restoration claim.',
    curation_scope=dict(no_Native_GUI_route_tests_build_CI_network_execution=True,
        no_original_edits=True, bounded_selected_workspace_only=True,
        helper=dict(path=str(helper.relative_to(ROOT)), sha256=p.sha(helper)),
        excluded_files=len(excluded)),
    retention=dict(new_payload_files=len(files), new_payload_bytes=total,
        material_occurrences=len(material), distinct_original_files=len(seen_original),
        before_open_copy_complete=True, maximum_file_bytes=4 * 1024**2,
        packet_ceiling_bytes=16 * 1024**2),
    files_index=dict(path=str((notes / 'files.json').relative_to(ROOT)), sha256=p.sha(notes / 'files.json')))
p.save_json(summary_path, summary)
physical_files = [q for q in notes.rglob('*') if q.is_file()] + [summary_path]
physical_bytes = sum(q.stat().st_size for q in physical_files)
assert physical_bytes < 16 * 1024**2
assert max(q.stat().st_size for q in physical_files) <= 4 * 1024**2
print(json.dumps(dict(summary=str(summary_path.relative_to(ROOT)), sha256=p.sha(summary_path),
    files_index_sha256=p.sha(notes / 'files.json'), physical_files=len(physical_files),
    physical_bytes=physical_bytes, new_payload_files=len(files), new_payload_bytes=total,
    material_occurrences=len(material), exclusions=len(excluded),
    actual_GUI_fully_qualified=False, current_export_fresh=False), sort_keys=True))
