"""Retain the demonstrated presentation defect and focused correction."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/gui-thermal-budget-display-001-notes'
packet=ROOT/'evidence/gui-thermal-budget-display-001.json'
assert not notes.exists() and not packet.exists()
refs,files,material,total={},[],[],0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')]
assert len(nodes)==3;exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper),'exec'))
review=ROOT/'.runs/gui-thermal-budget-display-review-001.json';r=f.read_json(review)
assert r['blocking_findings']==[]
assert p.sha(ROOT/'autorouter/gui.py')=='93963f6a68d3269042298b6a2d374ffbfa18a86315c2ee30cb9cf02d7caf709e'
assert p.sha(ROOT/'tests/test_gui_thermal_budget_display.py')=='b2dff93829b7e3f8dc45e03c717e4449bd194ca73ba6e878fbc3f34daef8ae7a'
for row in r['pins']:assert p.sha(ROOT/row['path'])==row['sha256']
for name in ['gui-thermal-budget-display-targeted-001.log','gui-thermal-budget-display-targeted-001-time.log',
    'gui-thermal-budget-display-targeted-002.log','gui-thermal-budget-display-targeted-002-time.log',review.name]:
    retain(ROOT/'.runs'/name,Path('controls-review')/name)
retain(Path(__file__),Path('controllers')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='demonstrated-recovery-budget-summary-display-fix',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,
    defect='034 GUI review/choice generic operation30 budget overwrote method420; export120 overwrote method420. Actual commands and receipts preserved420/120.',
    change='Only recovery presentation gets immutable captured effective preferences after stage-record merging. Commands, receipts, validation, admission and cancellation are unchanged.',
    controls=dict(before=dict(failing_subtests=['review','choice','export'],complete_cost=cost(ROOT/'.runs/gui-thermal-budget-display-targeted-001-time.log')),
        after=dict(passed=38,complete_cost=cost(ROOT/'.runs/gui-thermal-budget-display-targeted-002-time.log'))),
    source_sha256=p.sha(ROOT/'autorouter/gui.py'),regression_sha256=p.sha(ROOT/'tests/test_gui_thermal_budget_display.py'),
    independent_AI_source_review=dict(path=str((notes/'controls-review'/review.name).relative_to(ROOT)),sha256=p.sha(review),human=False),
    limits='Focused extracted callback/software controls and source/log review only. Immutable034 retains defect; new installed/full-suite/Native/GUI qualification required. No routing quality, speed, Windows or release claim.',
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
for item in material:assert p.sha(ROOT/item['original'])==item['sha256']
p.save_json(packet,record);print(json.dumps(dict(files=len(files),bytes=total,Native=False,actual_GUI=False)))
