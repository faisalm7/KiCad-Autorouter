"""Copy the completed export-only control; no tools, rerouting or admission."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
NOTES = Path(__file__).resolve().parent
BASE = ROOT / '.runs/runtime-directory-022'
RUNTIME = BASE / 'runtime'
CONTROL = BASE / 'Cthermal-export-control-001-run'
EXPORT = RUNTIME / '.runs/Cthermal-export-control-001'
PRIOR = RUNTIME / '.runs/interf-installed022-comparison-001/C_thermal'
OLD_RECORD = ROOT / 'evidence/interf-installed022-comparison-001.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, 'Existing curated bytes differ: ' + str(path)
    else:
        with path.open('xb') as stream:
            stream.write(raw)


old = load(OLD_RECORD)
execution = load(CONTROL / 'execution.json')
export = load(EXPORT / 'export.json')
prior = load(PRIOR / 'thermal-route/result.json')
references = {}
for row in old['files']:
    references.setdefault(row['sha256'], row['path'])
files, material, excluded = [], [], []
new_bytes = 0


def retain(path, relative):
    global new_bytes
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    digest = sha(raw)
    public = references.get(digest)
    if public is None:
        target = NOTES / relative
        write(target, raw)
        public = str(target.relative_to(ROOT))
        references[digest] = public
        files.append(dict(path=public, bytes=len(raw), sha256=digest))
        new_bytes += len(raw)
        assert new_bytes < 12 * 1024 * 1024 and len(files) < 500
    else:
        assert sha((ROOT / public).read_bytes()) == digest
    material.append(dict(original=str(path.relative_to(ROOT)), retained=public,
                         bytes=len(raw), sha256=digest))
    return public


for path in sorted(CONTROL.iterdir()):
    retain(path, Path('controller') / path.name)
for name in ('run-runtime022-Cthermal-export-control-001.py',
             'runtime022-Cthermal-export-control-001.log',
             'runtime022-Cthermal-export-control-001-time.log'):
    retain(ROOT / '.runs' / name, Path('controller') / name)
for relative in ('thermal-route/result.json', 'choice/choice.json', 'review/review.json',
                 'result.json', 'export.log', 'export.process.json'):
    retain(PRIOR / relative, Path('prior-bindings') / relative)
for path in sorted(EXPORT.rglob('*')):
    if not path.is_file():
        continue
    relative = path.relative_to(EXPORT)
    if len(relative.parts) > 1 and relative.parts[:2] == ('validation', 'code'):
        excluded.append(dict(path=str(path.relative_to(ROOT)), reason='Captured runtime code already pinned by original immutable build and export receipt; not recopied.'))
    elif len(relative.parts) > 1 and relative.parts[1] in ('kicad-config', 'kicad-cache', 'kicad-documents'):
        excluded.append(dict(path=str(path.relative_to(ROOT)), reason='Generated job-owned preferences/cache/documents; raw files remain on this Mac.'))
    else:
        retain(path, Path('export') / relative)
for name in ('SCOPE.md', 'curate.py'):
    retain(NOTES / name, Path(name))

# This is a bounded public copy index, not a replacement Native/proof validator.
index = dict(schema=1, kind='runtime022-export-control-public-material-v1',
             files=files, material=material, excluded=excluded,
             immutable_source_head=export['tools']['git_head'],
             implementation_sha256=export['tools']['implementation_sha256'],
             archive_scope='Complete new export evidence except captured code and generated config/cache/documents; identical bytes map to one already retained public file. Absolute original paths remain in untouched receipts. This copy is not a relocated standalone executable proof or a backup of every referenced raw input.')
write(NOTES / 'files.json', (json.dumps(index, indent=2) + '\n').encode())

summary = dict(schema=1, kind='runtime022-thermal-corrective-export-only-control-v1',
    recorded_utc=datetime.now(timezone.utc).isoformat(), passed=execution['passed'],
    accepted=False, project_complete=False, actual_GUI=False, human_review=False,
    new_routing=False, comparative_success=False,
    purpose='Debugging export-only control from an existing accepted Cthermal candidate after the v3 delivery failed on explicit --seconds420 outside the unchanged30–120 export bound. A new --seconds120 export succeeds. No routing attempt was repeated and no v3 failure is replaced or stitched into a comparative first-attempt success.',
    retained_v3=dict(path=str(OLD_RECORD.relative_to(ROOT)), sha256=sha(OLD_RECORD.read_bytes()),
        status='All seven frozen v3 deliveries failed; Cthermal failed at export. That record and raw results remain unchanged.'),
    runtime=dict(source_head=export['tools']['git_head'],
        runtime_manifest_sha256=export['tools']['source_provenance']['manifest_sha256'],
        kicad=export['tools']['kicad'],
        qualification_limit='Uses immutable runtime022, before the later product GUI budget fix. Does not qualify any newer installed build or actual GUI.'),
    complete_control=dict(wall_seconds=29.43, full_cpu_seconds=29.36,
        user_seconds=24.68, system_seconds=4.68, resolution_seconds=0.01,
        measurement='Complete enclosing /usr/bin/time real/user/sys, including initial prior-route readback, source/tool/choice checks, fresh export, child readback, repeated in-controller readback, publication and exit. Do not add nested CPU.'),
    stored_controller_sample=dict(wall_seconds=execution['sampled_wall_seconds'],
        full_cpu_seconds=execution['sampled_fullCPU_seconds'],
        scope='Earlier prepublication sample, retained separately from complete exit measurement.'),
    cost_scope='Additional debugging/research qualification cost, separate from the original frozen v3 comparison. Authoring, AI review and this curation are additional, not measured as zero; not included in the29.43/29.36 control measurement.',
    own_final=dict(export_receipt_sha256=execution['export_receipt_sha256'],
        candidate_sha256=export['candidate_sha256'],
        native_report_sha256=export['native_report_sha256'],
        native={key:export['native'][key] for key in ('opens','blocking','warnings','exclusions')},
        ignored_checks=export['native']['ignored_checks'],
        schematic_parity=export['schematic_parity'],
        whole_project_drc_clean=export['whole_project_drc_clean'],
        original_geometry_and_routing_unchanged=export['original_geometry_and_routing_unchanged'],
        export_budget_seconds=export['budget_seconds'],
        sampled_export_wall_seconds=export['wall_seconds'],
        sampled_export_full_cpu_seconds=export['total_cpu_seconds'],
        metrics=export['metrics'],
        checked=execution['checked'],
        protection='Fresh export shared checker verifies original immutable geometry/rules and exact validated route copper, and requires original protected routes to remain. Full original source witnesses and fresh refill/final Native bindings are retained. This is not a separate nonempty protected-copper fixture or physical/electrical approval.'),
    bindings=dict(source_hashes=export['source_hashes'],
        prior_route_receipt_sha256=load(CONTROL / 'protocol.json')['prior_receipt_sha256'],
        choice_sha256=load(CONTROL / 'protocol.json')['choice_sha256'],
        source_unchanged_observed_by_control=execution['passed'],
        candidate_equals_bound_prior=export['candidate_sha256'] == prior['candidate_sha256']),
    rights=dict(source='KiCad demos/interf_u', revision='69cafb907ebc09e7722a2a464b1d466fc2e3608d',
        source_url='https://gitlab.com/kicad/code/kicad/-/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/interf_u',
        license='CC-BY-SA-4.0', attribution='KiCad contributors; Tux artwork by Larry Ewing and The GIMP',
        modifications='Candidate routing/Native serialization differ from the original demo; original source, original rules and complete schematic remain unchanged.',
        notices=[dict(path=row['path'], sha256=row['sha256']) for row in old['files'] if '/licenses/' in row['path']]),
    limits=['One exposed development family; not independent confirmation or generalized superiority.',
        'All22 Native warnings and original ignored-check configuration remain visible; no global waiver or whole-project cleanliness claim.',
        'No GUI action, human engineer review, physical testing, live application, formal release or new spending.',
        'Raw originals and outputs remain on this Mac. This curated packet is not a new full-restoration test and is not retroactively covered by older artifact backups.'],
    files_index=dict(path=str((NOTES / 'files.json').relative_to(ROOT)), sha256=sha((NOTES / 'files.json').read_bytes())),
    new_file_count=len(files), new_material_bytes=new_bytes)
write(ROOT / 'evidence/runtime022-thermal-export-control-001.json', (json.dumps(summary, indent=2) + '\n').encode())
print(json.dumps(dict(summary='evidence/runtime022-thermal-export-control-001.json',
    summary_sha256=sha((ROOT / 'evidence/runtime022-thermal-export-control-001.json').read_bytes()),
    files_index_sha256=summary['files_index']['sha256'], new_files=len(files), new_bytes=new_bytes)))
