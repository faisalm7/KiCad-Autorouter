"""Small additive DTI-001 correction packet; no Native or product execution."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io

notes = ROOT / 'evidence/default-targets-integration-correction-002-notes'
output = ROOT / 'evidence/default-targets-integration-correction-002.json'
assert not notes.exists() and not output.exists()
first = ROOT / 'evidence/default-targets-integration-draft-001.json'
assert p.sha(first) == 'd9b4298a71025f559d53902489f69cb627e84df0c33564cbbf3ccac55709e22d'
prior = f.read_json(first); prior_index = prior['files_index']
assert p.sha(ROOT / prior_index['path']) == prior_index['sha256']
table = f.read_json(ROOT / prior_index['path'])
refs = {row['sha256']: row['path'] for row in table['files']}
refs.update({row['sha256']: row['retained'] for row in table['material']})
files = []; material = []; total = 0
helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
functions = [node for node in ast.parse(helper.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in {'retain', 'tree', 'cost'}]
assert len(functions) == 3
exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'), globals())

expected = {
    'autorouter/pipeline.py': '276398a357b7c5ffc73aef481888174b5c902083df9ebc476a39239caf3b68bb',
    'autorouter/review_export.py': '5aca217c01deca20c333b5015af0cb3ebcc63c812a52441325765d00c51e15e8',
    'tests/test_default_target_integration.py': '5cc7b71fc052f36f445bf7cf095910464466b9a9787fbe4a7175b9ec58bfb7c2',
    '.runs/default-targets-parent-fence-fix-001.py': '6cb5caedce813692f2048e4a7d346d2dd8ab15fa6c855b4f9fe94082abba4404',
    '.runs/default-targets-integration-delta-review-002.json': '42cda932e4364065012db7fdec341ce70e931c23b71089d1775f8a032d9f17fa',
    '.runs/default-targets-integration-targeted-002.log': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    '.runs/default-targets-integration-targeted-002-time.log': 'fe68675012977d7e8f567ef091f04f96d71ce7492cfe72be950f40a8d6775b2d',
}
for name, digest in expected.items():
    assert p.sha(ROOT / name) == digest, name
    retain(ROOT / name, Path('source' if name.startswith(('autorouter/', 'tests/')) else 'proof') / name)
retain(Path(__file__), Path('curation') / Path(__file__).name)
unchanged = {name: prior['source_files_sha256'][name] for name in
             ('autorouter/default_targets.py', 'autorouter/netclass.py', 'tests/test_default_targets.py')}
for name, digest in unchanged.items(): assert p.sha(ROOT / name) == digest

scope = '''# Default-target integration correction002

This additive packet records only the DTI-001 correction after first draft001.
The captured pipeline/export source and constructed regression tests now replay
the mandatory Default transport and final class/dimension/process evidence for
a current rejected sole-thermal incumbent. Genuine historical/out-of-scope
producerNone behavior retains its previous contract. All unchanged helper,
netclass, prior tests, failed loader/image-pin reproductions, pure Mixer replay,
AI review and rights are linked through the immutable first draft and index.

DTI-001 is closed at source/constructed-control scope. This is not a built
runtime, actual Native run, routing/completion result, physical/electrical
validation or human PCB review. No runtime037 proof or first-draft byte changes.
Fresh full/install/native/cancel/freshness/GUI qualification remains necessary.
Code and owned test fixtures are covered by repository LICENSE retained in001;
no CAD, engine, venv, private input, screenshots or browser content is copied.
'''
notes.mkdir(parents=True, exist_ok=True)
doc = notes / 'SCOPE.md'
with doc.open('x') as stream: stream.write(scope)
raw = doc.read_bytes()
files.append({'path': str(doc.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
total += len(raw)
for name, digest in expected.items(): assert p.sha(ROOT / name) == digest, name
for name, digest in unchanged.items(): assert p.sha(ROOT / name) == digest, name
assert p.sha(first) == 'd9b4298a71025f559d53902489f69cb627e84df0c33564cbbf3ccac55709e22d'
index = notes / 'files.json'
p.save_json(index, {'schema': 1, 'files': files, 'material': material})
summary = {
    'schema': 1, 'kind': 'Default-targets-DTI001-source-and-constructed-control-correction',
    'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'accepted': False, 'routing_accepted': False, 'production_qualified': False,
    'project_complete': False, 'Native_execution': False, 'actual_GUI': False, 'human_review': False,
    'current_source_and_proof_sha256': expected, 'unchanged_source_sha256': unchanged,
    'prior_immutable_draft': {'path': str(first.relative_to(ROOT)), 'sha256': p.sha(first), 'files_index': prior_index},
    'DTI001': {'status': 'closed at source and constructed-control scope',
        'before': 'Rejected sole-thermal child omitted the mandatory new Default transport/final-class replay in first draft aa1ec94a.',
        'after': 'Rejected-child branch calls source-declared check_rejected_default_targets before existing Native/edge/pour/selection fences. A required contract uses shared final Native map/process/raw-class/derived-dimension audit; direct Route and export reuse it. Optional marker removal cannot select old compatibility for a current producer.',
        'review_limit': 'Independent AI source-delta review, not human review or demonstrated Native false-admission control.'},
    'targeted002': {'passed': True, 'tests': 109, 'unittest_seconds': 10.439,
        'complete_external_cost': cost(ROOT / '.runs/default-targets-integration-targeted-002-time.log'),
        'scope': 'Constructed targeted regressions; no new Native qualification.'},
    'retention': 'Only changed source/test, exact fix-authoring script, delta AI review and targeted002 outputs added. Helper/netclass/other tests/failed reproductions/pure replays/rights and previous evidence remain exact references through001. No old artifact overwritten.',
    'remaining_gates': ['Fresh full suite and isolated install', 'Actual selected7 owned2/4Cu whole/partial/invalid Native controls',
        'Current protected/cancel/freshness/last-PRL readback and actual GUI',
        'New frozen measured Mixer trial after source freeze; no predicted completion',
        'Broader independent evaluation, Windows safeguards/native, restoration capacity, human/physical and separate formal-publication approval'],
    'accounting': '109-test complete exit retained; prior costs remain in001. Authoring and whole-review CPU unmetered, notzero. Curation external exit cost is recorded separately after publication, not asserted here.',
    'files_index': {'path': str(index.relative_to(ROOT)), 'sha256': p.sha(index)},
    'new_files': len(files), 'new_bytes': total, 'material_rows': len(material),
}
p.save_json(output, summary)
for row in files:
    q = ROOT / row['path']; assert q.stat().st_size == row['bytes'] and p.sha(q) == row['sha256']
for row in material:
    q = ROOT / row['retained']; assert q.stat().st_size == row['bytes'] and p.sha(q) == row['sha256']
print(json.dumps({'files': len(files), 'bytes': total, 'material': len(material),
                  'summary_sha256': p.sha(output), 'files_index_sha256': p.sha(index)}))
