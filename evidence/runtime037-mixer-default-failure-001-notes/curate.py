"""Retain the completed first Mixer failure; no routing, tools or tests run."""
from pathlib import Path
import ast, collections, datetime, hashlib, json, re, sys

ROOT = Path(__file__).resolve().parents[2]
runtime = ROOT/'.runs/runtime-directory-037/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
notes = Path(__file__).parent; packet = ROOT/'evidence/runtime037-mixer-default-failure-001.json'
assert not packet.exists() and set(notes.iterdir()) == {Path(__file__)}
helper = ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions = [node for node in ast.parse(helper.read_text()).body
             if isinstance(node, ast.FunctionDef) and node.name in ('retain','tree','cost')]
assert len(functions) == 3
exec(compile(ast.Module(body=functions, type_ignores=[]), str(helper), 'exec'))
refs = {}; files = []; material = []; total = 0; queued = []; dependencies = []
for name in ('evidence/runtime035-hierarchy-observation-001.json',
             'evidence/runtime037-hierarchy-native-milestone-001.json'):
    source = ROOT/name; data = f.read_json(source); index = ROOT/data['files_index']['path']
    assert p.sha(index) == data['files_index']['sha256']
    idx = f.read_json(index)
    for row in idx.get('files', []): refs.setdefault(row['sha256'], row['path'])
    for row in idx.get('material', []): refs.setdefault(row['sha256'], row['retained'])
    dependencies.append(dict(path=name, sha256=p.sha(source), files_index=data['files_index']))
shared_retain = retain
def retain(source, name): queued.append((Path(source), Path(name)))

base = ROOT/'.runs/runtime037-mixer-whole-001'
plan = f.read_json(base/'protocol.json'); outer = f.read_json(base/'execution.json')
child = Path(plan['output']); result = f.read_json(child/'result.json'); workspace = Path(result['workspace'])
route = f.read_json(workspace/'route/result.json'); source = Path(plan['source'])
manifest = runtime/'runtime-distribution.json'; md = f.read_json(manifest)
assert p.sha(manifest) == plan['runtime_manifest_sha256'] == 'c1ef6a1e1f47d03e39ca63c3114707889d86a3269fbccf5dcc9cec9ccfcba940'
assert plan['source_head'] == md['build_source']['git_head'] == 'c3e7e8ef4dadce1f83f838322fb5d685ce3714ac'
assert md['native_version'] == '10.0.7' and len(md['immutable_files_sha256']) == 52
assert p.sha(base/'protocol.json') == outer['protocol_sha256']
assert p.sha(child/'result.json') == outer['child_sha256']
assert p.sha(workspace/'route/result.json') == result['route_receipt_sha256']
assert outer['workflow_delivered'] is False and outer['controls_passed'] is False
assert outer['process']['status'] == 'nonzero_exit' and outer['process']['exit_code'] == 2 and outer['process']['cleanup_complete']
assert result['workflow_delivered'] is False and result['status'] == 'failed'
assert route['accepted'] is False and route['status'] == 'drc_rejected'
assert route['candidate_sha256'] == p.sha(Path(route['candidate'])) == result['candidate_sha256']
assert p.tree_hash(source.parent) == plan['source_hashes'] == route['source_hashes'] == result['source_hashes']
assert [route['native'][k] for k in ('opens','blocking','warnings','exclusions')] == [161,63,235,0]
assert [route['source_drc'][k] for k in ('opens','blocking','warnings','exclusions')] == [0,24,91,0]
assert len(route['native']['ignored_checks']) == 7
assert [row['stage'] for row in result['processes']] == ['preview','route']
assert result['processes'][0]['process']['exit_code'] == 0 and result['processes'][1]['process']['exit_code'] == 2
assert not any((workspace/name).exists() for name in ('review','choice','export'))
assert plan['warning_policy'] == 'retain_all_native_findings' and plan['expected_counts'] is None
source_process = f.read_json(workspace/'route/source-drc-process.json')
final_process = f.read_json(workspace/'route/final-drc-process.json')
assert '--schematic-parity' not in source_process['argv'] and '--schematic-parity' in final_process['argv']
assert source_process['cleanup_complete'] and final_process['cleanup_complete']
assert route['invariants_unchanged'] and route['whole_project_drc_clean'] is False
errors = collections.Counter(row['type'] for row in route['native']['findings'] if row['severity'] == 'error' and row['type'] != 'unconnected_items')
assert dict(errors) == {'track_width':57, 'clearance':5, 'starved_thermal':1}
assert plan['source_rights']['license'] == 'CC-BY-SA-4.0'

tree(base, Path('actual001/enclosure-and-protocol'))
tree(child, Path('actual001/workflow'))
tree(source.parent, Path('source/original-project'))
retain(manifest, Path('runtime/runtime-distribution.json'))
for name, digest in md['immutable_files_sha256'].items():
    assert p.sha(runtime/name) == digest
    retain(runtime/name, Path('runtime/immutable')/name)

# Notices are also physically present beside this packet's derived board bytes.
for name in ('LICENSE.README','LICENSE.CC-BY-SA-4.0'):
    q = source.parent/'_licenses'/name; refs.pop(p.sha(q), None)
    queued.insert(0, (q, Path('source-license')/name))
retain(ROOT/'data/sources.json', Path('source-license/data-sources.json'))
controllers = [
    (ROOT/'.runs/enclose-runtime030-ordinary-workflow-002.py', plan['enclosure_sha256']),
    (ROOT/'scripts/qualify_runtime_workflow.py', plan['driver_sha256']),
]
for q, digest in controllers:
    assert p.sha(q) == digest
    retain(q, Path('controllers')/q.name)
for name in ('.runs/freeze-runtime037-mixer-workflow-001.py',
             '.runs/ordinary-workflow-warning-policy-review-001.json',
             '.runs/mixer-default-floor-causal-review-001.json',
             '.runs/runtime037-mixer-freeze-001.log', '.runs/runtime037-mixer-freeze-001-time.log',
             '.runs/runtime037-mixer-whole-001-controller.log', '.runs/runtime037-mixer-whole-001-time.log'):
    retain(ROOT/name, Path('controllers-reviews-costs')/Path(name).name)
retain(helper, Path('controllers')/helper.name)

proofs = []
for stage in ('task','final'):
    path = workspace/'route'/(stage+'-classes-proof.json'); proof = f.read_json(path); q = proof['qualification']
    assert proof['context'] == 'native-route-hierarchy-default-v2' and q['policy'] == 'hierarchy-default-instance-unit-v2'
    census = [q[k] if k != 'unconnected_pads' else len(q[k]) for k in ('components','terminals','nets','instances','unconnected_pads')]
    assert census == [114,280,80,5,47]
    assert q['board_floors_waived'] is False and not any(q[k] for k in ('accepted','routing_accepted','production_qualified'))
    proofs.append(dict(stage=stage, original_path=str(path.relative_to(ROOT)), sha256=p.sha(path),
        context=proof['context'], policy=q['policy'], census=census, source_class_policy=q['source_class_policy'],
        board_floors_waived=False, sha256_bindings=q['sha256']))

# Preflight all selected bytes before creating additional payload files.
new = {}; names = {}; findings = []
secret = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|github_pat_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|(?i:Authorization:\s*Bearer\s+[A-Za-z0-9_.-]{20,})')
for q, name in queued:
    raw = io.read_bytes(q, 4*1024**2); assert b'\0' not in raw; raw.decode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()
    assert name not in names or names[name] == digest; names[name] = digest
    if secret.search(raw): findings.append(str(q.relative_to(ROOT)))
    if digest in refs: assert p.sha(ROOT/refs[digest]) == digest
    else: new.setdefault(digest, len(raw))
assert not findings and sum(new.values()) + Path(__file__).stat().st_size < 16*1024**2 and len(new) < 1900
for q, name in queued: shared_retain(q, name)
assert total == sum(new.values()) and len(files) == len(new)
curator_raw = Path(__file__).read_bytes()
files.append(dict(path=str(Path(__file__).relative_to(ROOT)), bytes=len(curator_raw), sha256=hashlib.sha256(curator_raw).hexdigest(), authored=True)); total += len(curator_raw)

def author(name, text):
    global total
    raw = text.encode(); q = notes/name; q.open('xb').write(raw)
    files.append(dict(path=str(q.relative_to(ROOT)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), authored=True)); total += len(raw)
author('ATTRIBUTION.md', '''# Multichannel Mixer source and derived routing

The original Multichannel Mixer demo comes from the KiCad project,
`demos/multichannel`, official tag10.0.7, commit
69cafb907ebc09e7722a2a464b1d466fc2e3608d:
https://gitlab.com/kicad/code/kicad/-/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/multichannel
Mirror: https://github.com/KiCad/kicad-source-mirror/tree/69cafb907ebc09e7722a2a464b1d466fc2e3608d/demos/multichannel

KiCad's retained source LICENSE.README explicitly assigns all demos/* files to
Creative Commons Attribution-ShareAlike4.0 International. The exact license
and notice are physically retained under source-license/. The original source
and library credits, including embedded CERN Author/License properties, remain
unchanged. No new authorship of the original demo is claimed. The source
schematic explicitly warns that this is a demo, not a working audio mixer.

Generated candidate PCB/DSN/SES and copied/refilled design files in this packet
derive from that source and remain CC-BY-SA-4.0. Changes comprise the declared
whole-board unlocked-routing task, engine-generated routing and Native refill;
the unchanged original and exact source hashes are linked in files.json. The
candidate failed actual Native checks and is not an approved design. No KiCad,
CERN or original-contributor endorsement is implied.

Authored router/controller code remains governed by its repository GPL notice;
that license is not substituted for the demo and derived design license.
''')
author('SCOPE.md', '''# Completed first Mixer attempt only

This packet preserves the completed runtime037 first Mixer workflow001 at
source c3e7e8ef4dadce1f83f838322fb5d685ce3714ac and exact c1ef6a1e...manifest.
It links prior licensed source and immutable runtime payloads by SHA, and copies
new candidate/proof/process/DSN/SES/report/log bytes without alteration. Prior
packets and the original source are not rewritten. ATTRIBUTION.md and the
CC-BY-SA4.0 notice/license apply to all demo-derived design payloads.

Preview completed; Route emitted a DRC-rejected candidate. Review, accept-intent,
export and export verification did not run. No Route was accepted and no GUI
action, Native rerun, test, CI or router execution occurred during curation.
The raw generic child scope's "owned complete schematic" text does not make
the third-party KiCad demo project-owned; its actual CC-BY-SA4.0 rights govern.

Final full-SCH Native is161opens/63blocking/235warnings/0exclusions. Blocking
findings include57width(.2mm vs original.3mm),5clearance and1starvedthermal.
Seven original ignored checks and every warning/finding remain retained. This
Route's non-full-SCH source stage is0/24/91/0; historical exact-source full-SCH
0/24/206/0 is linked separately, not relabelled as a new current full-SCH run.
Source opens are not an invalidity diagnosis; this original source has0opens.

Task/final v2 class proofs bind114components/280terminals/80nets/5instances/
47extra nonnetted pads. Exact class identity did not enforce global hard floors:
actual input targets were.2mm width/clearance versus.3mm board minima, with a
latent.6mm via target below1.5mm minimum. No generated via appears here. A
prospective pure Default fix is not included or qualified by this failed run;
161opens and thermal starvation remain separate problems.

Engine-reported43.20s internalTIMED_OUT/0violations/181unrouted is not Native
validity or enclosure timeout. Actual engine worker45.760606s/55.879376CPU
emitted SES/exit0. Reported816MB peak heap,96.88GB cumulative allocations and
runner RSS observations are distinct; cumulative allocations are not RSS.

Complete external exit62.82wall/72.24CPU is authoritative within240s wall/fullCPU;
pre-publication controller/Route/engine samples are nested, not added again.
Freeze1.24wall/1.16CPU is separate. Authoring/review/curation whole cost is
additional and unknown, not zero. No broad family/quality/comparison gain,
automatic support coverage, human/electrical/physical/GUI/Windows approval.

Excluded: job-owned kicad-config/cache/documents, engine-config, tmp, __pycache__,
downloaded tools/venv/apps/JRE/JAR and unrelated runs/history/unfinished fix code.
Only bounded requested roots were considered. Full newer raw remains Mac-only
outside008/010; this is essential public evidence, not a full backup/restore.
''')
assert total < 16*1024**2
index = notes/'files.json'
p.save_json(index, dict(schema=1, files=files, material=material, dependencies=dependencies,
    preflight=dict(text_only=True, max_file_bytes=4*1024**2, max_new_bytes=16*1024**2, new_unique_payload_bytes=sum(new.values()), secret_pattern_findings=findings),
    excluded_patterns=['kicad-cache/**','kicad-config/**','kicad-documents/**','engine-config/**','tmp/**','__pycache__/**','runtime/.venv/**','runtime/.tools/**'],
    design_rights='KiCad Multichannel Mixer and all derived design payload CC-BY-SA-4.0; physical source license/notice and ATTRIBUTION.md retained. Authored controller code has separate repository GPL license.'))
engine = next(row for row in route['steps'] if row['name'] == 'engine')
record = dict(schema=1, kind='runtime037-first-mixer-default-floor-failure', recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_head=plan['source_head'], runtime_manifest_sha256=p.sha(manifest), native_version='10.0.7',
    accepted=False, routing_accepted=False, workflow_delivered=False, project_complete=False, actual_GUI=False, human_review=False, physical_electrical_validation=False,
    source=str(source.relative_to(ROOT)), source_hashes=plan['source_hashes'], source_rights=plan['source_rights'], source_upstream=dict(repository='KiCad/kicad-source-mirror', canonical_repository='https://gitlab.com/kicad/code/kicad', tag='10.0.7', commit='69cafb907ebc09e7722a2a464b1d466fc2e3608d', path='demos/multichannel', license='CC-BY-SA-4.0'),
    source_references=dependencies, source_history=plan['source_reference'],
    first_actual_attempt=dict(attempt='001', settings=plan['settings'], warning_policy=plan['warning_policy'],
        preview_exit0=True, route_exit2=True, route_status=route['status'], final_Native_counts=[161,63,235,0],
        final_blocking_by_type=dict(errors), ignored_checks=route['native']['ignored_checks'],
        candidate_sha256=route['candidate_sha256'], native_report_sha256=route['native_report_sha256'],
        route_receipt_sha256=p.sha(workspace/'route/result.json'), invariants_unchanged=route['invariants_unchanged'],
        noProtectionClaim=True, protected_count=0,
        postroute_stages_not_run=['review','accept-intent','export','verify_export'],
        outer_status=outer['process']['status'], outer_exit_code=outer['process']['exit_code'], cleanup_complete=outer['process']['cleanup_complete']),
    source_observations=dict(current_route_non_full_SCH_counts=[0,24,91,0], current_source_argv_includes_schematic_parity=False,
        historical_exact_source_full_SCH_counts=[0,24,206,0], historical_reused_not_rerun=True,
        final_candidate_argv_includes_schematic_parity=True, original_severities_exclusions_and_ignored_checks_preserved=True,
        distinction='Different check scope, not a relabelled warning reduction or invalid-source judgment. Raw original project/rules remain exact.'),
    class_proofs=proofs,
    causal_finding=dict(status='demonstrated input floor underrepresentation; acceptance correctly refused',
        actual_Default_targets_nm=dict(width=200000, clearance=200000, via_diameter=600000, via_drill=300000),
        original_board_floors_nm=dict(min_track_width=300000, min_clearance=300000, min_via_diameter=1500000, min_through_hole_diameter=300000, min_via_annular_width=300000),
        final_width_findings=57, final_clearance_findings=5, final_thermal_findings=1, final_opens=161,
        source_task_final_identity_proof_does_not_prove_floor_transport=True,
        prospective_fix='Not copied from unfinished working code, not Native-qualified here; input floor correction is not a demonstrated completion fix or automatic coverage gain.'),
    engine=dict(status=engine['status'], exit_code=engine['exit_code'], internal_state='TIMED_OUT', internal_reported_seconds=43.20,
        internal_violations=0, internal_unrouted=181, worker_wall_seconds=engine['wall_seconds'], worker_CPU_seconds=engine['cpu_seconds'],
        actual_SES_sha256=p.sha(workspace/'route/routes.ses'), reported_peak_heap_MB=816.0,
        reported_cumulative_allocation_GB=96.88, cumulative_allocation_is_RSS=False,
        runner_max_RSS_bytes=engine['max_rss_bytes'], runner_sampled_peak_group_RSS_bytes=engine['sampled_peak_group_rss_bytes'],
        meaning='Engine exit0/SES/self-reported0violations is output availability, never candidate admission; Native final findings control rejection.'),
    costs=dict(complete_external=cost(ROOT/'.runs/runtime037-mixer-whole-001-time.log'), freeze=cost(ROOT/'.runs/runtime037-mixer-freeze-001-time.log'),
        nested_prepublication_controller_wall_seconds=outer['complete_wall_seconds'], nested_prepublication_controller_full_CPU_seconds=outer['complete_full_CPU_seconds'],
        nested_driver_wall_seconds=result['sampled_wall_seconds'], nested_driver_full_CPU_seconds=result['sampled_full_cpu_seconds'],
        nested_route_wall_seconds=route['wall_seconds'], nested_route_full_CPU_seconds=route['total_cpu_seconds'],
        whole_wall_full_CPU_budget_seconds=240,
        accounting='External exit62.82/72.24 is authoritative; nested controller/driver/Route/engine observations are included, not added again. Freeze1.24/1.16 is separate; interactive authoring/review/curation additional, whole CPU unknown/notzero.'),
    reviews=['.runs/ordinary-workflow-warning-policy-review-001.json','.runs/mixer-default-floor-causal-review-001.json'],
    limits=['One exposed licensed development demo; family independence remains unverified.','No accepted Route/review/intent/export or GUI/human/electrical/physical/Windows approval. Source warns it is not a working audio mixer.','No quality/completion/comparative speed gain or automatic coverage improvement.','All final warnings, original severities,7ignored checks and actual failure retained; no source/rule relaxation.','No new Native/tests/GUI/CI/routing/install/network/delegation or unfinished code inspection by curation.','Full newer raw Mac-only outside008/010; no backup restoration performed.'],
    public_safety='All selected payload text preflighted UTF8/noNUL/4MiB each and known credential/private-key patterns; no findings. Bounded pattern check is not authentication/general secret guarantee. Every original/retained hash rechecked.',
    retention=dict(new_payload_files=len(files), new_payload_bytes=total, original_material_paths=len(material), max_new_bytes=16*1024**2, max_file_bytes=4*1024**2),
    files_index=dict(path=str(index.relative_to(ROOT)), sha256=p.sha(index)))
for row in material: assert p.sha(ROOT/row['original']) == p.sha(ROOT/row['retained']) == row['sha256']
p.save_json(packet, record)
print(json.dumps(dict(packet=str(packet.relative_to(ROOT)), packet_sha256=p.sha(packet), index_sha256=p.sha(index),
    new_payload_files=len(files), new_payload_bytes=total, original_material_paths=len(material), physical_files_including_summary_index=len(files)+2)))
