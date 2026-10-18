"""Retain this completed milestone with the existing bounded evidence helpers."""
from pathlib import Path
import ast, datetime, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
notes=ROOT/'evidence/runtime032-native-controls-001-notes'
assert not notes.exists()
refs={};files=[];material=[];total=0
for name in ('runtime030-native-workflow-qualification-001','runtime030-negative-cancel-001','runtime031-install-cancel-001','runtime022-thermal-export-control-001','comparison-v2-group-development-001'):
 data=f.read_json(ROOT/('evidence/'+name+'.json'))
 rows=data.get('files',[])
 if data.get('files_index'):
  index=ROOT/data['files_index']['path'];assert p.sha(index)==data['files_index']['sha256'];idx=f.read_json(index);rows=rows+idx.get('files',[])+idx.get('material',[])
 for row in rows:refs.setdefault(row['sha256'],row.get('path',row.get('retained')))
source=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
functions=[node for node in ast.parse(source.read_text()).body if isinstance(node,ast.FunctionDef) and node.name in ('retain','tree','cost')]
assert len(functions)==3
# This fixed population includes five distinct2.2MB native alias observations.
# Preserve them unchanged: measured17MB partial stopped at inherited16MB; fixed32MB text bound.
for node in ast.walk(functions[0]):
 if isinstance(node,ast.Constant) and type(node.value) is int and node.value==16:node.value=32
exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'))
runtime=ROOT/'.runs/runtime-directory-032/runtime'
manifest=runtime/'runtime-distribution.json'
assert p.sha(manifest)=='391c8ff33badbd762d3ae4af9757eaa9075ef42ce3b53865dfa0a193647ef2a0'
rows=[]
cases=[('stock_functional','runtime032-v2-b0_positive-002'),('scored_functional','runtime032-v2-via_low_positive-001'),('engine_cancel','runtime032-v2-engine-cancel-001'),('native_invalid','runtime032-v2-invalid-001'),('positive_portfolio','runtime032-v2-portfolio-positive-002'),('negative_portfolio_budget_failure','runtime032-v2-portfolio-negative-001'),('ordinary_whole','runtime032-ordinary-whole4Cu-001'),('ordinary_partial','runtime032-ordinary-partial2Cu-001')]
for label,name in cases:
 base=ROOT/'.runs'/name;plan=f.read_json(base/'protocol.json');out=Path(plan['output'])
 tree(base,Path('enclosures')/label);tree(out,Path('cases')/label)
 for n,root in enumerate(plan.get('material_roots',[])):tree(Path(root),Path('portfolio-material')/label/str(n))
 if label=='engine_cancel':tree(runtime/'.runs/native7-comparison-v2-cancel-attempt-001',Path('cases/engine_cancel/attempt'))
 timefile=ROOT/'.runs'/(name+'-time.log')
 # Failed command001 and successful retry002 used one frozen Native output.
 if label=='stock_functional':timefile=ROOT/'.runs/runtime032-v2-b0_positive-002-time.log'
 row=dict(case=label,protocol_sha256=p.sha(base/'protocol.json'),output_receipt_sha256=p.sha(out/'result.json'),complete_cost=cost(timefile),scope=plan['scope'])
 result=f.read_json(out/'result.json');row.update(status=result.get('status'),control_passed=result.get('controls_passed',result.get('control_passed',result.get('passed',result.get('workflow_delivered')))),native=result.get('native',result.get('Native_counts')))
 rows.append(row)
 for suffix in ('-controller.log','-time.log'):
  q=ROOT/'.runs'/(name+suffix)
  if q.is_file():retain(q,Path('logs')/q.name)
for name in ('full-integration-175','install-distribution-native-005','runtime032-v2-controls-preparation-001'):
 tree(ROOT/'.runs'/name,Path('integration-install-preparation')/name)
retain(ROOT/'.runs/runtime-directory-032/result.json',Path('installation/result.json'))
retain(manifest,Path('runtime/runtime-distribution.json'))
retain(runtime/'RUNTIME_README.txt',Path('runtime/RUNTIME_README.txt'))
tree(runtime/'.runs/install-native-smoke',Path('installation/native-smoke'))
tree(ROOT/'.runs/runtime-directory-032/source-fixture',Path('installation/source-fixture'))
for command in f.read_json(ROOT/'.runs/runtime-directory-032/result.json')['commands']:
 retain(Path(command['log']),Path('installation/logs')/Path(command['log']).name)
names=['run-full-integration-175.py','run-install-distribution-native-005.py','freeze-install-distribution-native-005-authoring-original-001.py','freeze-install-distribution-native-005-failure-001.json','prepare-runtime032-v2-controls-001.py','freeze-runtime032-v2-controls-001.py','freeze-runtime032-v2-follow-on-001.py','enclose-comparison-v2-delivery-001.py','enclose-native7-independent-control-003.py','enclose-runtime030-ordinary-workflow-001.py','runtime032-v2-b0-command-correction-001.json','runtime032-v2-controller-preflight-review-001.json','portfolio-negative-budget-review-001.json','runtime032-gui-access-001.json','runtime029-gui073-toolbar-access-state-007.json']
for name in names:retain(ROOT/'.runs'/name,Path('controllers-reviews')/name)
for name in ('runtime032-gui-access-002.json','portfolio-api-replay-targeted-001.log','portfolio-api-replay-targeted-001-time.log','curation-runtime032-bound-failure-001.json','curate-runtime032-native-controls-001-authoring-original.py','curate-runtime032-native-controls-001-time.log'):
 retain(ROOT/'.runs'/name,Path('controllers-reviews')/name)
for name in ('full-integration-175-time-001.log','full-integration-175-controller-001.log','install-distribution-native-005-time-001.log','install-distribution-native-005-controller-001.log','runtime032-v2-controls-preparation-001-time.log','runtime032-v2-controls-preparation-001-controller.log','freeze-runtime032-v2-controls-001-log','freeze-runtime032-v2-controls-001-time.log'):
 q=ROOT/'.runs'/name
 if q.is_file():retain(q,Path('logs')/name)
for name in ('qualify-comparison-v2-delivery-001.py','qualify-comparison-v2-route-child-001.py','cancel-comparison-v2-engine-001.py','qualify-comparison-v2-native-invalid-001.py'):
 retain(runtime/'.runs'/name,Path('controllers-reviews')/name)
# Preserve the unexecuted internal-source positive plan and pre-Native shell failure.
for name in ('runtime032-v2-portfolio-positive-001','runtime032-v2-b0_positive-001'):tree(ROOT/'.runs'/name,Path('retained-failures-unexecuted')/name)
retain(Path(__file__),Path('controllers-reviews')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
summary=dict(schema=1,kind='runtime032-installed-native-controls-with-negative-budget-failure',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,accepted=False,actual_GUI=False,human_review=False,source_head='b0d2e6f737a72ebc127f02f3861d191f01f8a2d9',runtime_manifest_sha256=p.sha(manifest),runtime_modules=46,runtime_immutable_files=51,
 full175=dict(passed=True,tests=2151,skips=1,scope='Frozen b0 product and then-current external administration; later API-only helper fix needs its own targeted controls and regression, not a product rebuild.'),
 controls=rows,
 negative_failure=dict(qualified=False,status='budget_exceeded',wall_seconds=358.1369217,CPU_seconds=420.936517,inner_wall_CPU_cap=420,complete_wall_seconds=371.91,complete_CPU_seconds=435.31,Native_counts=[[0,1,22,0],[1,2,22,0],[1,4,22,0]],selected=None,delivery=False,diagnostic='Old controller mislabeled the budget failure as negative acceptance trouble. No candidate was accepted. Bounded external-helper duplicate-check removal and truthful diagnostic are separately reviewed; no budget increase or product-core change.'),
 scope='Actual current Mac selected10.0.7/Java25/Freerouting2.5 installed ordinary CLI and non-admitting comparison functional controls. Each delivered Route/export retains own Native/fullSCH/original/protected proof. Positive portfolio tries all three fixed scores, chooses via_default by fixed valid rank. B0 is stock engine/native DSN within shared fidelity/validation safeguards, not an untouched official plugin. No fair B0/B1/B2/C matrix, general routing gain, GUI, Windows, cleanOS, relocation or physical qualification.',
 warnings='Whole ordinary keeps6warnings/protected10; partial0warnings/protected4; comparison owned2Cu protected1. Two original ignored checks remain visible. Interf source has expected opens and repairable thermal findings, not hard net/pad conflicts. No hidden warning/exclusion changes.',
 source_rights='Generated board/schematic geometry project-owned GPL. Unchanged copied official KiCad project settings and Interf source retain CC-BY-SA-4.0 and original source/license notices. Reused Tux bitmap retains Larry Ewing/The GIMP attribution in existing packet. Public licensed/owned fixtures only; no private boards, downloaded apps/engines or local-reference.',
 accounting='Complete external exit times are retained per control; stored child/portfolio samples omit their later tails and cannot replace whole costs. Preparation/freezing, full suites, installation, failed commands, authoring/research/AI review/curation are additional. Four-second planning charge is not measured consumption; unknown interactive CPU is not zero.',
 GUI='026/GUI072 remains last actual GUI-qualified build; immutable029/GUI073 preserved.032 lacks actual GUI evidence. Latest bounded tool attempts gave cgWindowNotFound then no native apps and Mac-locked report; actual desktop lock cannot be distinguished from stale tool detection. No unlock loop or security change.',
 backup_scope='Essential source/proof for audited Git checkpoint only. Full raw remains on this Mac outside completed008/010 inventories. No new-target restoration; current disk insufficient for previously measured18.64GB lower bound plus newer work. Owner chose on-Mac storage.',
 remaining=['Fresh bounded unchanged-budget Interf regression of external helper fix','Fair current installed default and optimizer vs stock/corrected/competent tuned-restart, unrelated licensed families and untouched frozen-policy confirmation','Current GUI; Windows explicit isolation prerequisite and actual Native slice; cleanOS/relocation/standalone','Space for required new-target restoration; authorized independent engineer/cleanup/physical validation; separate formal publication approval'],
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(ROOT/'evidence/runtime032-native-controls-001.json',summary)
print(json.dumps(dict(files=len(files),bytes=total,material=len(material),project_complete=False)))
