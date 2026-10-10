"""Small independent semantic falsifiers on copied source; no Java/native execution."""
from pathlib import Path
import copy, hashlib, json, sys
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE/'source-001'))
import test_driver as t
import checks
rows=[]
def run(name,mutate,expected):
 value=t.observed(True); mutate(value)
 try:
  result=checks.validate(value,t.EXPECTED)
  outcome=all(x['expected_observation_matches'] for x in result)
  error=None
 except (ValueError,KeyError,TypeError) as exc:outcome=False;error=str(exc)
 rows.append({'case':name,'expected_match':expected,'observed_match':outcome,'error':error})
 assert outcome is expected,(name,outcome)

def state(value):return value['cases'][2]['states'][-1]
def area(value):return next(a for a in state(value)['areas'] if a['reference']=='CONCAVE')
def trace(value):return next(a for a in state(value)['traces'] if a['net']=='CONTACT')
run('unchanged_split_positive',lambda v:None,True)
run('fill_concave_notch',lambda v:area(v)['ring_um'].__setitem__(2,[19350,-15000]),False)
run('move_integer_witness_only',lambda v:area(v)['ring_board_integer'][0].__setitem__(0,1+area(v)['ring_board_integer'][0][0]),False)
run('coordinate_scale_mismatch',lambda v:state(v).__setitem__('board_units_per_um',2),False)
run('unexpected_area_hole',lambda v:area(v).__setitem__('holes',1),False)
run('wrong_area_layer',lambda v:area(v).__setitem__('layer','bottom_layer'),False)
run('wrong_area_net',lambda v:area(v).__setitem__('net','FOREIGN'),False)
run('wrong_fixed_state',lambda v:area(v).__setitem__('fixed','UNFIXED'),False)
run('unwitnessed_contact',lambda v:area(v)['contacts'].append(999),False)
run('rational_board_point',lambda v:trace(v)['corner_classes'].__setitem__(0,'app.freerouting.geometry.planar.RationalPoint'),False)
run('wrong_foreign_terminal_net',lambda v:next(p for p in state(v)['pins'] if p['reference']=='FOREIGN_A').__setitem__('net','CONTACT'),False)
run('parser_warning',lambda v:v['cases'][2]['parser_warnings'].append('unknown source item omitted'),False)
run('unqualified_native_claim',lambda v:v.__setitem__('native_executed',True),False)
raw={'scope':'pure copied checker with synthetic importer observations; no Java/native evidence','cases':rows,'passed':True,
'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'source-001').iterdir() if p.is_file()}}
(HERE/'independent-controls-001.json').write_text(json.dumps(raw,indent=2)+'\n')
print(json.dumps({'cases':len(rows),'passed':True}))
