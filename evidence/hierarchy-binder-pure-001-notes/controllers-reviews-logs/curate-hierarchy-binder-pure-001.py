"""Retain the bounded first binder slice without promoting routing support."""
import ast,datetime,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/hierarchy-binder-pure-001-notes';packet=ROOT/'evidence/hierarchy-binder-pure-001.json';assert not notes.exists() and not packet.exists()
review=ROOT/'.runs/hierarchy-binder-pure-source-review-001.json';assert p.sha(review)=='72e1dbf9806e635aeacc17b3011fb4873ef61bde14d2f2b58b5a7aa4bbd1cea1'
replay=ROOT/'.runs/hierarchy-binder-retained003-006.json';data=f.read_json(replay);proof=data['proof']
assert data['passed'] and data['comparator_sha256']==p.sha(ROOT/'autorouter/schematic_hierarchy.py')=='61cfd80a0e466e28ee286eb742a888ccf95ddf52f5458deec7daca57274a5347'
assert (proof['components'],proof['terminals'],proof['nets'],proof['instances'],len(proof['unconnected_pads']))==(114,280,80,5,47)
assert all(proof[k] is False for k in ('accepted','routing_accepted','production_qualified','native_execution_performed_by_comparator','board_floors_waived'))
assert p.sha(ROOT/'tests/test_schematic_hierarchy.py')=='aa32926f3e204b313fc31a57a223da5023cbf57793eef98a86c5c181df2c78fe'
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')];exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
names=['runtime035-hierarchy-binder-contract-assessment-001.json','hierarchy-binder-pure-source-review-001.json','hierarchy-binder-retained003-006.json']
for i in range(1,7):
 names += [f'hierarchy-binder-targeted-{i:03d}.log',f'hierarchy-binder-targeted-{i:03d}-time.log',f'replay-hierarchy-retained003-binder-{i:03d}.py',f'replay-hierarchy-retained003-binder-{i:03d}-command.log',f'replay-hierarchy-retained003-binder-{i:03d}-time.log']
for i in range(1,5):names += [f'hierarchy-binder-retained003-{i:03d}.json']
sources=[ROOT/'.runs'/name for name in names]+[Path(__file__)]
raws=[io.read_bytes(q,4*1024**2) for q in sources];assert sum(map(len,raws))<16*1024**2
for raw in raws:assert b'\0' not in raw;raw.decode('utf8')
for q in sources:retain(q,Path('controllers-reviews-logs')/q.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
source_names=['autorouter/schematic_hierarchy.py','autorouter/layer_policy.py','tests/test_schematic_hierarchy.py','experiments/schematic_hierarchy_fixture.py']
p.save_json(packet,dict(schema=1,kind='hierarchy-default-instance-unit-first-pure-slice',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_base_head='72db8d41c8d389f8c3b6f80fb22535bd9962c93c',source_files_sha256={name:p.sha(ROOT/name) for name in source_names},
 project_complete=False,Native_executed=False,hierarchy_support_admitted=False,routing_accepted=False,coverage_unchanged=dict(total=25,static_eligible=7,unsupported=18),
 implementation='New pure exactbyte Default-only repeated-sheet/unit/terminal/class comparator. Existing flat policy and production hierarchy refusal remain; source-all User5-9 identity uses shared literal table helper without broadening explicit layer restrictions.',
 review=dict(path=str(review.relative_to(ROOT)),sha256=p.sha(review),scope='One separate skeptical AI source review. Expanded census and mutable-dict parse/hash issues fixed and targeted regression tested; not human or Native review.'),
 controls=dict(final_targeted_tests=54,final_complete_cost=cost(ROOT/'.runs/hierarchy-binder-targeted-006-time.log'),scope='28hierarchy controls plus existing flatparity/layer compatibility. Owned synthetic Native-shaped data only, not routing-quality or Native qualification.'),
 retained_data_replay=dict(passed=True,components=114,connected_terminals=280,nets=80,instances=5,original_unconnected_pad_UUIDs=47,complete_cost=cost(ROOT/'.runs/replay-hierarchy-retained003-binder-006-time.log'),source='evidence/runtime035-hierarchy-observation-001.json',report_sha256=p.sha(replay),source_findings='Original24clearanceerrors/206warnings/7ignoredchecks remain unchanged; not a source-invalid or routing-loss verdict.'),
 development_failures='Targeted001-003 positive initially refused direct-library drawing prefixes, pin-number presentation and one fixture alias Footprint mismatch. All earlier raw outputs remain. Replays001-004 refused crossdocument pinUUIDs, common0-only definitions, numeric20241229 nets and User5-9 table;005passed older source and006passed final reviewed bytes. These are finite pureauthoring corrections to the same retainedsource, not Native experiment reruns or stitched routing wins. Draftsourcehashes are retained, but exact superseded uncommitted draft source bytes were not archived; do not claim those drafts fully reproducible.',
 costs=dict(targeted=[dict(attempt=i,**cost(ROOT/'.runs'/f'hierarchy-binder-targeted-{i:03d}-time.log')) for i in range(1,7)],replay=[dict(attempt=i,**cost(ROOT/'.runs'/f'replay-hierarchy-retained003-binder-{i:03d}-time.log')) for i in range(1,7)],authoring_research_AI_review_seconds=None),
 decision='Integrate the versioned source-derived task/final/export proof using existing process/snapshot/PRL helpers next. Keep admission closed until fresh owned Native positive and invalid controls, ordinary compatibility and a bounded existing mixer Route/export qualify. No new board intake or Windowspolicyresearch.',
 rights='New comparator/tests/generated owned fixture are GPL-3.0-or-later. Reused mixer observation is existing public CC-BY-SA4.0 with source/license retained in prior packet and data/sources.json; no private material, downloadedtools or bulkboards added.',
 backup_scope='Essential source/receipt/index for audited Git. Existing raw source/tools/venv/preparedGUI stay onMac outside008/010; no new restoration attempted below capacity requirement.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
print(json.dumps(dict(files=len(files),bytes=total,hierarchy_support_admitted=False)))
