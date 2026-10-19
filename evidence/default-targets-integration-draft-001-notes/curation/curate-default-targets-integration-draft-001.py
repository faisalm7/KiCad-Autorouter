"""Retain only the explicitly enumerated first Default-target source draft."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io

notes = ROOT / 'evidence/default-targets-integration-draft-001-notes'
summary_path = ROOT / 'evidence/default-targets-integration-draft-001.json'
assert not notes.exists() and not summary_path.exists()
refs = {}; files = []; material = []; total = 0
prior = []
for name in ('evidence/runtime037-hierarchy-native-milestone-001.json',
             'evidence/runtime037-mixer-default-failure-001.json'):
    packet = f.read_json(ROOT / name); index = packet['files_index']
    assert p.sha(ROOT / index['path']) == index['sha256']
    table = f.read_json(ROOT / index['path'])
    for row in table.get('files', []): refs.setdefault(row['sha256'], row['path'])
    for row in table.get('material', []): refs.setdefault(row['sha256'], row['retained'])
    prior.append({'path': name, 'sha256': p.sha(ROOT / name), 'files_index': index,
                  'source_head': packet['source_head'], 'runtime_manifest_sha256': packet['runtime_manifest_sha256']})

helper = ROOT / '.runs/curate-runtime030-native-workflow-qualification-001.py'
syntax = ast.parse(helper.read_text())
functions = [node for node in syntax.body if isinstance(node, ast.FunctionDef) and node.name in {'retain', 'tree', 'cost'}]
assert {node.name for node in functions} == {'retain', 'tree', 'cost'}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'), globals())

expected = {
    'autorouter/default_targets.py': '245de5fc970a1a492485421a27ab5f4896ab4c1a900bca2309f25ef15d5e7660',
    'autorouter/netclass.py': '60eb4f314177b94a4a97916a8c29643b245d0f26c34b63b81e5c5e69b705c5f0',
    'autorouter/pipeline.py': 'aa1ec94ac6662e13ed22640dd6e0b434720c516bb66f8eb6d9b51f5869bbda6c',
    'autorouter/review_export.py': 'a5f566a46ae7ccb1551031e1eb4cc83e2b13aed07b7f4cf41ace541458d52795',
    'tests/test_default_targets.py': '465ea44fb5abcbf2604d50d34a056e086306f4407f71215646a5ea036e8320e5',
    'tests/test_default_target_integration.py': '83336a0efe53844f1339229fe6dc6901f84c5abdf5ec0b5457e6f345769e3cd0',
}
for name, digest in expected.items():
    assert p.sha(ROOT / name) == digest, name
    retain(ROOT / name, Path('source') / name)
for name in ('LICENSE',): retain(ROOT / name, Path('rights') / name)
retain(helper, Path('curation') / helper.name)
retain(Path(__file__), Path('curation') / Path(__file__).name)

runs = [
    'default-targets-implementation-handoff-001.json', 'default-targets-implementation-delta-002.json',
    'default-targets-skeptical-review-001.json', 'default-targets-skeptical-delta-002.json',
    'default-targets-mixer-retained-replay-001.json', 'default-targets-mixer-retained-replay-001.log',
    'default-targets-mixer-retained-replay-001-time.log',
    'default-targets-integration-targeted-001.log', 'default-targets-integration-targeted-001-time.log',
]
for number in range(1, 6):
    for suffix in ('.log', '-time.log'): runs.append(f'default-targets-targeted-{number:03d}' + suffix)
for number in (1, 2):
    for suffix in ('.log', '-time.log'): runs.append(f'default-targets-via-pin-regression-{number:03d}' + suffix)
if (ROOT / '.runs/integrate-default-targets-001.py').is_file(): runs.append('integrate-default-targets-001.py')
for name in runs: retain(ROOT / '.runs' / name, Path('proof') / name)

# The replay contains licensed net-name membership but no new CAD. Link exact
# already retained license/attribution bytes rather than copying source boards.
rights = []
mix_index = f.read_json(ROOT / prior[1]['files_index']['path'])
for row in mix_index['material']:
    if row['original'].endswith(('/_licenses/LICENSE.README', '/_licenses/LICENSE.CC-BY-SA-4.0')):
        target = ROOT / row['retained']; assert p.sha(target) == row['sha256']
        rights.append({key: row[key] for key in ('retained', 'sha256', 'bytes')})
assert {Path(row['retained']).name for row in rights} >= {'LICENSE.README', 'LICENSE.CC-BY-SA-4.0'}

scope = '''# First reviewed-source Default-target integration draft

This packet preserves source, constructed tests, failures, AI review and a pure
replay of one previously retained real Native export. It is not a built runtime,
new Native run, routing result, completion improvement, electrical finding or
production qualification. Runtime037 and its failed Mixer trial remain unchanged.

The sole-Default raw class still equals the original source. The new planning
stage derives width/clearance/via/drill targets from the unchanged global floors;
its output must survive all ordinary source, tool, original-design, protected
copper, full-schematic, cancellation, Native and final metadata checks. Current
pipeline/export integration is a source draft awaiting independent final review
and full/install/native/cancel/GUI qualification.

The original helper had a constructed dangling image-pin reference when a via
stack was renamed. Both failed author regressions and the independent embedded
reproducer remain visible. The corrected helper retains every original stack
and appends the new routing choice. The initial exact helper/test source bytes
are pinned in earlier receipts but not separately archived here: do not claim
their old bytes are retained. The available old reproducer is embedded verbatim
in the original AI review; current final helper/test source is retained.

Project code/generated test data is covered by repository LICENSE. Mixer net
membership and the pure replay derive from the KiCad multichannel demo under
CC-BY-SA-4.0; exact retained attribution/license and the complete unchanged CAD,
Native reports and source provenance are linked through the prior Mixer packet.
No private input, engine, application, venv, cache, pixel or browser material is
included. AI review is not human PCB review. All author/research costs that were
not metered remain unknown, not zero. Raw artifacts remain on this Mac outside
older backup snapshots unless separately recorded.
'''
notes.mkdir(parents=True, exist_ok=True)
scope_file = notes / 'SCOPE.md'
with scope_file.open('x') as stream: stream.write(scope)
scope_raw = scope_file.read_bytes(); scope_sha = hashlib.sha256(scope_raw).hexdigest()
files.append({'path': str(scope_file.relative_to(ROOT)), 'bytes': len(scope_raw), 'sha256': scope_sha})
total += len(scope_raw)
assert total < 16 * 1024**2 and len(files) < 2000

costs = []
for number in range(1, 6):
    name = f'default-targets-targeted-{number:03d}'
    costs.append({'case': name, 'outcome': 'failed:53pass plus1 loader error' if number == 1 else 'passed',
                  **cost(ROOT / '.runs' / (name + '-time.log'))})
for number in (1, 2):
    name = f'default-targets-via-pin-regression-{number:03d}'
    costs.append({'case': name, 'outcome': 'failed before fix:1 constructed regression',
                  **cost(ROOT / '.runs' / (name + '-time.log'))})
costs += [{'case': 'retained-Mixer-pure-replay', 'outcome': 'pure replay passed; no Native',
           **cost(ROOT / '.runs/default-targets-mixer-retained-replay-001-time.log')},
          {'case': 'integration-targeted-001', 'outcome': '141passed; no new Native qualification',
           **cost(ROOT / '.runs/default-targets-integration-targeted-001-time.log')}]
for name, digest in expected.items(): assert p.sha(ROOT / name) == digest, name
index = notes / 'files.json'
p.save_json(index, {'schema': 1, 'files': files, 'material': material})
summary = {
    'schema': 1, 'kind': 'first-reviewed-source-Default-floor-integration-draft',
    'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'accepted': False, 'routing_accepted': False, 'production_qualified': False,
    'project_complete': False, 'Native_execution': False, 'actual_GUI': False, 'human_review': False,
    'source_files_sha256': expected, 'source_scope': 'Unbuilt ROOT development draft; no runtime037 module or proof changed.',
    'prior_immutable_evidence': prior, 'source_rights': {'code': 'Repository LICENSE',
        'Mixer_replay_and_net_membership': 'CC-BY-SA-4.0; exact existing notices below', 'retained_notices': rights},
    'finding': 'Actual runtime037 input underrepresented original width/clearance/via floors; final Native correctly rejected161opens/63blocking/235warnings. The correction is faithful planning transport, not a demonstrated routing gain.',
    'policy': 'single-default-global-floor-targets-v1',
    'effective_Mixer_targets_nm': {'width_nm': 300000, 'clearance_nm': 300000, 'via_diameter_nm': 1500000, 'via_drill_nm': 300000},
    'pure_replay': {'passed': True, 'new_Native': False, 'guided_bytes': 42007,
        'raw_dsn_sha256': 'd1f7dadffbdef49bbca66217e887804aa4e050350f867cc23bc9f2856465a6d0',
        'guided_sha256': '3eeda734a2d0a26a4eec17ebc44c5039be407b589a98f2d49105bf8699583655',
        'interpretation': 'Existing real raw export/map/task only; transform/replay, no new routing or validation.'},
    'tests_and_complete_external_costs': costs,
    'failed_evidence': ['targeted001 loader-path error after53passes; corrected invocation retained',
        'Independent DT-001: initial helper transform/check could leave an image pin referencing a removed old via stack; both failed author regression logs retained, corrected source and delta review retained'],
    'review_scope': 'Original independent pure-helper review001 and closure delta002 only. Current pipeline/export integration review still underway; no claim it passed.',
    'old_source_retention_limit': 'Pre-fix helper/test hashes are retained, but separate pre-fix source copies are not available in this finite selection. Exact independent recipe is embedded in skeptical-review001; corrected source is copied. Never imply source pins alone are archived bytes.',
    'remaining_gates': ['Independent current integration review', 'Fresh full suite and isolated install',
        'Actual selected7 two/fourCu whole/partial positive and invalid/protected Native controls',
        'Current cancellation/freshness/source/PRL readback controls and actual GUI',
        'Fresh bounded equal-budget Mixer observation after source freeze; no predicted completion',
        'Broader licensed development/untouched confirmation, Windows safeguards/native, restoration capacity, human/physical and separate formal-publication approval'],
    'accounting': 'Complete measured test/replay exits above; no hidden reroute. Independent reviews retain in-process-only timers explicitly excluding imports/startup; authoring/research/whole-review CPU unmetered, notzero. Curation exit costs are recorded separately in its external log and not asserted before exit.',
    'files_index': {'path': str(index.relative_to(ROOT)), 'sha256': p.sha(index)},
    'new_files': len(files), 'new_bytes': total, 'material_rows': len(material),
    'retention_bounds': {'single_file_bytes': 4 * 1024**2, 'new_bytes': 16 * 1024**2, 'new_files': 2000},
}
p.save_json(summary_path, summary)
print(json.dumps({'files': len(files), 'bytes': total, 'material': len(material),
                  'summary_sha256': p.sha(summary_path), 'files_index_sha256': p.sha(index)}))
