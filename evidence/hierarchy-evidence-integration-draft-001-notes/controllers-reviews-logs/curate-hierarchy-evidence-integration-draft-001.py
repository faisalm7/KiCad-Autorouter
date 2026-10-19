"""Checkpoint integrated source/plumbing before heavy native qualification."""
import ast,datetime,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/hierarchy-evidence-integration-draft-001-notes';packet=ROOT/'evidence/hierarchy-evidence-integration-draft-001.json';assert not notes.exists() and not packet.exists()
review=ROOT/'.runs/hierarchy-binder-evidence-integration-review-001.json';assert p.sha(review)=='a0b5a527c9bb5b7515409df878d97304c3411e91270422bbe4d2595f781632e6'
v=f.read_json(review)
for row in v['source_files']:assert p.sha(ROOT/row['path'])==row['sha256']
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')];exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
names=['hierarchy-binder-evidence-integration-review-001.json','hierarchy-integration-core-targeted-001.log','hierarchy-integration-core-targeted-001-time.log','hierarchy-evidence-targeted-001.log','hierarchy-evidence-targeted-001-time.log','hierarchy-evidence-targeted-002.log','hierarchy-evidence-targeted-002-time.log','hierarchy-native-controls-001-preparation.log','hierarchy-native-controls-001-preparation-time.log','run-full-integration-179.py']
for name in names:retain(ROOT/'.runs'/name,Path('controllers-reviews-logs')/name)
retain(Path(__file__),Path('controllers-reviews-logs')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
source_names=[row['path'] for row in v['source_files']]+['tests/test_schematic_hierarchy_evidence.py','experiments/schematic_hierarchy_native_v1/fixture.py']
source=ROOT/'.runs/hierarchy-native-controls-001/source'
prepared={str(path.relative_to(source)):p.sha(path) for path in sorted(source.iterdir())};assert len(prepared)==5
record=dict(schema=1,kind='hierarchy-evidence-integration-source-draft-before-native',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_base_head='42afb56e81b5453fd4bd82188ff569b4e64b0156',source_files_sha256={name:p.sha(ROOT/name) for name in source_names},
 project_complete=False,Native_executed=False,hierarchy_support_qualified=False,routing_accepted=False,
 implementation='Source-derived versioned shared task/final/export class evidence. All closure bytes, Native maps/workerargv/logs, copied projects and exactafter/PRLguard are mandatory. Original flatproof branch preserved. Only ordinaryselected7 whole/partial/source_all can request hierarchyproof; advanced/comparison staysclosed. Defaultidentity is independent of unchanged globalfloor/finalDRC enforcement.',
 review=dict(path=str(review.relative_to(ROOT)),sha256=p.sha(review),scope='Separate bounded AI integrationdelta source review; no concrete blocker, not actualNative/human proof.'),
 targeted_controls=dict(core_tests=54,core_cost=cost(ROOT/'.runs/hierarchy-integration-core-targeted-001-time.log'),first_plumbing_tests=59,first_plumbing_cost=cost(ROOT/'.runs/hierarchy-evidence-targeted-001-time.log'),final_plumbing_tests=60,final_plumbing_cost=cost(ROOT/'.runs/hierarchy-evidence-targeted-002-time.log'),scope='Constructed worker/netlist/map journals and real ownedMacPRLflags. Final adds forged-path-before-read regression; no Native tool selection/execution is inferred.'),
 owned_native_fixture=dict(generator='experiments/schematic_hierarchy_native_v1/fixture.py',generator_sha256=p.sha(ROOT/'experiments/schematic_hierarchy_native_v1/fixture.py'),path=str(source.relative_to(ROOT)),files_sha256=prepared,preparation_cost=cost(ROOT/'.runs/hierarchy-native-controls-001-preparation-time.log'),intended_counts=dict(components=5,terminals=11,nets=5,instances=3,extra_no_net_pads=4),qualified=False,scope='Owned generated root/repeated child/two-unit/commonpin/libalias control. Sourcegeneration+staticprerequisiteonly, no actualKiCad netlist/Native/candidate. No zone/protectedcopper or independentbenchmarkfamily claim.'),
 next='After auditedpush/readback, run fresh full179 sequentially, then freshdistribution009/selected7 and actualowned Native hierarchy positive/invalid+sixstage delivery. Preserve any failure and fix only demonstrated cause. Then onebounded existingmixer wholeRoute/freshexport unchangedconstraints. No repeatcompleted observation orWindows011loop.',
 costs_note='All targeted/preparation costs retained separately; sourceauthoring/research/AI review and futureNative costs additional/unknownnotzero. No routingquality/completion/gain claim.',
 backup_scope='Essential source/tests/generator/proof intended for auditedGit; raw preparedNative source and035GUI remainMac-only outside008/010. Freeheadroom below18.64GBrestorelowerbound; no restoration/delete/capraise.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(packet,record)
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
print(json.dumps(dict(files=len(files),bytes=total,Native_executed=False)))
