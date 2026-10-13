"""Same exact pure width guard counterexamples after caller-directory fix."""
from pathlib import Path
import ast,copy,json,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,preferences as pref
OWN=Path(__file__).resolve().parent;source=OWN/'source';board=source/'board.kicad_pcb';project=board.with_suffix('.kicad_pro');run=OWN/'postfix-run';run.mkdir();raw=(OWN/'run/routing-preferences.json').read_bytes();(run/'routing-preferences.json').write_bytes(raw);effective=pref.readback(raw);before=p.sha(ROOT/'autorouter/pipeline.py');lines=(ROOT/'autorouter/pipeline.py').read_text().splitlines(keepends=True);node=next(x for x in ast.parse(''.join(lines)).body if isinstance(x,ast.FunctionDef) and x.name=='minimum_width_guard');fragment='\n'+''.join(lines[node.lineno-1:node.end_lineno]);(run/'code').mkdir();(run/'code/pipeline.py').write_text(fragment);rows=[]
# This is an explicit retained-policy fragment seam, never actual code provenance.
def data(strict=True,include=True):
 d={'scope':'whole_board_unlocked_routing','source':str(board),'candidate':str(board),'adapter':'both','engine_profile':'standard','scoring_variant':None,'budget_seconds':120,'cpu_budget_seconds':120,'routing_preferences':{'file':'routing-preferences.json','sha256':p.sha(run/'routing-preferences.json'),'effective':effective}};settings=p.engine_profile_settings('standard',100,strict_class_targets=strict);settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120);process={'name':'engine','argv':p.engine_argv(run,settings['argv']),'cwd':str(run),'status':'success','exit_code':0,'cleanup_complete':True};d['engine_budget']=settings;d['steps']=[process];p.save_json(run/'engine-process.json',process)
 if include:d['minimum_width_guard']=p.minimum_width_guard(board,'both')
 return d
for label,record,expect in [('same controlling positive',data(), 'passed'),('same missing guard/rebased profile',data(False,False),'reject')]:
 try:p.check_preferences_record(run,record);outcome='passed';detail={}
 except p.Rejected as ex:outcome='reject';detail={'reason':str(ex)}
 rows.append({'case':label,'expected':expect,'outcome':outcome,'matched':outcome==expect,'detail':detail})
# Actual pre-policy implementation remains readable; do not synthesize history.
historical=ROOT/'.runs/ardujoy-original-native-001/code/autorouter/pipeline.py';(run/'code/pipeline.py').rename(run/'code/current-width-policy-fragment.py.txt');(run/'code/pipeline.py').write_bytes(historical.read_bytes());record=data(False,False);p.check_preferences_record(run,record);rows.append({'case':'actual archived pre-width-policy source fragment compatibility','outcome':'passed','expected':'passed','matched':True,'archived_source_sha256':p.sha(historical)})
project.write_text(json.dumps({'board':{'design_settings':{'rules':{'min_track_width':1}}}}));record=data();record['minimum_width_guard']['min_track_width_mm']=True
try:p.check_minimum_width_record(record,run);outcome='passed';detail={}
except p.Rejected as ex:outcome='reject';detail={'reason':str(ex)}
rows.append({'case':'same boolTrue/original1 record alias','outcome':outcome,'expected':'reject','matched':outcome=='reject','detail':detail})
project.write_text(json.dumps({'board':{'design_settings':{'rules':{'min_track_width':.65}}}}));p.save_json(OWN/'postfix-results.json',{'native_validation_performed':False,'subprocesses_executed':0,'source_sha256_before':before,'source_sha256_after':p.sha(ROOT/'autorouter/pipeline.py'),'results':rows});assert all(x['matched'] for x in rows);assert before==p.sha(ROOT/'autorouter/pipeline.py');print(json.dumps(rows,sort_keys=True))
