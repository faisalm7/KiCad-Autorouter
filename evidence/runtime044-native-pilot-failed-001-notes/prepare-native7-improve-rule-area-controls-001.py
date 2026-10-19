"""Bounded owned supported-pour combination and unsupported-track source controls.

No Native execution. Preserve the pinned complete fractional source unchanged.
Decision: qualify actual faithful interchange or retain a concrete unsupported
combination. No attempt to weaken original keepouts or electrical requirements.
"""
from pathlib import Path
import sys,shutil,json,uuid
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,pour_rule_area as pour
from tests.test_pour_rule_area import zone
plan=json.loads((R/'.runs/runtime043-native-regression-source-plan-001.json').read_bytes())
base=next(row for row in plan['cases'] if row['case']=='fractional-owned');source=Path(base['source'])
assert p.tree_hash(source.parent)==base['source_hashes']
out=R/'.runs/native7-improve-rule-area-controls-001';out.mkdir(mode=0o700)
rows=[]
for name in ('pour-only','track-prohibited'):
 folder=out/name;shutil.copytree(source.parent,folder);candidate=folder/source.name;tree=sx.read(candidate)
 area=zone(number=901,x=20,layers=('B.Cu',));sx.one(sx.one(area,'polygon'),'pts')[1:]=[['xy','20','23'],['xy','25','23'],['xy','25','25'],['xy','20','25']]
 if name=='track-prohibited':sx.one(sx.one(area,'keepout'),'tracks')[1]='not_allowed'
 tree.append(area);sx.write(candidate,tree)
 if name=='pour-only':assert len(pour.qualify(tree))==1
 else:
  try:p.check_rule_area_support(tree)
  except p.Rejected:pass
  else:raise AssertionError('unsupported track prohibition was admitted')
 rows.append(dict(case=name,source=str(candidate),source_hashes=p.tree_hash(folder),expected='actual own Native/export validation required' if name=='pour-only' else 'static refusal before output or worker'))
assert p.tree_hash(source.parent)==base['source_hashes']
p.save_json(out/'prepared.json',dict(schema=1,Native_executed=False,actual_GUI=False,source_basis=base,controller_sha256=p.sha(Path(__file__)),fixture_grammar='tests/test_pour_rule_area.py:zone; literal only vertices/layer/unique UUID/prohibition changed on a fresh complete source copy',fixture_grammar_sha256=p.sha(R/'tests/test_pour_rule_area.py'),cases=rows,scope='Product combination qualification; not unrelated development data, routing improvement or electric suitability. All source originals retained.'))
print(json.dumps({'prepared':len(rows),'Native_executed':False}))
