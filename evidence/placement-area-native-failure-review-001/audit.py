"""Read-only actual001 source/report geometry audit; no native subprocesses."""
from pathlib import Path
from decimal import Decimal
import json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx
run=ROOT/'.runs/placement-area-native-001';out=Path(__file__).parent;before=p.tree_hash(run)
summary=json.loads((run/'summary.json').read_text());assert summary['controls_passed'] is False
checks=[];cases=[]
for row in summary['cases']:
 case=row['case'];base=run/case;board=base/'diagnostic-drc-input/fixture.kicad_pcb';tree=sx.read(board)
 report=json.loads((base/'diagnostic-drc.json').read_text());project=json.loads(board.with_suffix('.kicad_pro').read_text())
 settings=project['board']['design_settings'];assert settings['rule_severities']['items_not_allowed']=='error';assert not settings['drc_exclusions'];checks.extend([case+':severity_error',case+':no_exclusions'])
 assert not report['violations'] and not report['unconnected_items'];assert not any(x['key']=='items_not_allowed' for x in report['ignored_checks']);checks.extend([case+':actual_zero_findings',case+':not_ignored'])
 assert p.sha(board)==row['board_sha256'];checks.append(case+':native_input_hash')
 zones=sx.children(tree,'zone');assert all(not sx.children(z,'filled_polygon') for z in zones);checks.append(case+':no_filled_ruleareas')
 for target in row['expected']['prohibited_target_uuids']:
  item=next(n for n in p.routes(tree) if sx.unquote(sx.one(n,'uuid')[1])==target)
  if item[0]=='segment':
   a,b=[tuple(Decimal(v) for v in sx.one(item,key)[1:]) for key in ('start','end')]
   assert a==(40,20) and b==(10,20);zone=next(z for z in zones if sx.one(sx.one(z,'keepout'),'tracks')[1]=='not_allowed')
   pts=[tuple(Decimal(v) for v in n[1:]) for n in sx.one(sx.one(zone,'polygon'),'pts')[1:]]
   assert min(v[0] for v in pts)==Decimal('24.5') and max(v[0] for v in pts)==Decimal('25.5') and min(v[1] for v in pts)<20<max(v[1] for v in pts)
  else:
   xy=tuple(Decimal(v) for v in sx.one(item,'at')[1:]);radius=Decimal(sx.one(item,'size')[1])/2;zone=next(z for z in zones if sx.one(sx.one(z,'keepout'),'vias')[1]=='not_allowed')
   pts=[tuple(Decimal(v) for v in n[1:]) for n in sx.one(sx.one(zone,'polygon'),'pts')[1:]]
   assert min(v[0] for v in pts)<xy[0]-radius<xy[0]+radius<max(v[0] for v in pts) and min(v[1] for v in pts)<xy[1]-radius<xy[1]+radius<max(v[1] for v in pts)
  checks.append(case+':actual_target_geometrically_violates_'+target)
 cases.append({'case':case,'native_findings':0,'negative_targets':row['expected']['prohibited_target_uuids'],'passed_original_control':row['passed'],'board_sha256':p.sha(board),'report_sha256':p.sha(base/'diagnostic-drc.json'),'process_sha256':p.sha(base/'diagnostic-drc-process.json')})
assert p.tree_hash(run)==before;checks.append('actual001_entire_tree_unchanged')
record={'scope':'read-only saved native evidence audit','native_executed':False,'constraint_qualification':False,'checks':checks,'check_count':len(checks),'cases':cases,'entire_actual001_tree':before,'script_sha256':p.sha(Path(__file__))}
with (out/'audit.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'actual001_unchanged':True,'native_executed':False}))
