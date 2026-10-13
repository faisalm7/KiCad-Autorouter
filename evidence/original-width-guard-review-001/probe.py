"""Minimum-width policy/binding controls only; no native routing/tool execution."""
from pathlib import Path
import copy,hashlib,json,math,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,preferences as pref
OWN=Path(__file__).resolve().parent;source=OWN/'source';source.mkdir();board=source/'board.kicad_pcb';board.write_text('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)))\n');project=board.with_suffix('.kicad_pro');run=OWN/'run';run.mkdir();initial=p.sha(ROOT/'autorouter/pipeline.py');rows=[]
def write(value='missing'):
 obj={} if value=='missing' else {'board':{'design_settings':{'rules':{'min_track_width':value}}}};project.write_text(json.dumps(obj));return project.read_bytes()
for label,value in [('missing','missing'),('zero-int',0),('zero-float',0.0),('negative',-0.65),('boolean-true',True),('boolean-false',False),('string','0.65'),('NaN',float('nan')),('positive-infinity',float('inf')),('negative-infinity',float('-inf')),('positive',.65)]:
 raw=write(value)
 try:guard=p.minimum_width_guard(board,'both');outcome='none' if guard is None else 'guard';detail=guard
 except Exception as ex:outcome='reject';detail={'type':type(ex).__name__,'reason':str(ex)}
 expected='none' if label in {'missing','zero-int','zero-float'} else 'guard' if label=='positive' else 'reject';rows.append({'case':'original value '+label,'expected':expected,'outcome':outcome,'matched':outcome==expected,'project_unchanged':project.read_bytes()==raw,'detail':detail})
write(.65);guard=p.minimum_width_guard(board,'both');choices={'adapter':'both','profile':'standard'};request={'captured':None,'effective':pref.resolve(overrides=choices),'snapshot':pref.snapshot(overrides=choices)};data={'scope':'whole_board_unlocked_routing','source':str(board),'candidate':str(board),'adapter':'both','engine_profile':'standard','scoring_variant':None,'budget_seconds':120,'cpu_budget_seconds':120,'minimum_width_guard':guard}
p.capture_preferences(data,run,request)
def settings(d,strict=True):
 budget=p.engine_profile_settings('standard',100,strict_class_targets=strict);budget.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120);process={'name':'engine','argv':p.engine_argv(run,budget['argv']),'cwd':str(run),'status':'success','exit_code':0,'cleanup_complete':True};d['engine_budget']=budget;d['steps']=[process];p.save_json(run/'engine-process.json',process)
settings(data);baseline=copy.deepcopy(data)
def check(label,change=None,expected='reject'):
 d=copy.deepcopy(baseline);settings(d)
 if change:change(d)
 try:
  with patch('subprocess.run',side_effect=AssertionError('forbidden subprocess')),patch('subprocess.Popen',side_effect=AssertionError('forbidden subprocess')):p.check_preferences_record(run,d)
  outcome='passed';detail={}
 except Exception as ex:outcome='reject';detail={'type':type(ex).__name__,'reason':str(ex)}
 rows.append({'case':label,'expected':expected,'outcome':outcome,'matched':outcome==expected,'detail':detail});print(json.dumps(rows[-1],sort_keys=True))
check('captured corrected preferences with positive original minimum',expected='passed')
check('guard negative receipt value',lambda d:d['minimum_width_guard'].update(min_track_width_mm=-.65))
check('guard boolean receipt value with original.65',lambda d:d['minimum_width_guard'].update(min_track_width_mm=True))
check('guard NaN receipt value',lambda d:d['minimum_width_guard'].update(min_track_width_mm=float('nan')))
check('guard original project hash changed',lambda d:d['minimum_width_guard'].update(original_project_sha256='0'*64))
check('guard strict-class boolean false',lambda d:d['engine_budget'].update(strict_class_targets=False))
def no_flag(d):
 d['engine_budget']['argv'].remove('--router.fanout.enabled=false');d['steps'][0]['argv']=p.engine_argv(run,d['engine_budget']['argv']);p.save_json(run/'engine-process.json',d['steps'][0])
check('fanout flag stripped and process rebound',no_flag)
check('guard missing without budget rebase',lambda d:d.pop('minimum_width_guard'))
def missing_and_rebased(d):d.pop('minimum_width_guard');settings(d,False)
check('guard missing with all engine settings/process rebased to historical profile',missing_and_rebased)
# Independently expose Python bool/int dict equality in the typed receipt record.
write(1);good=p.minimum_width_guard(board,'both');bad=copy.deepcopy(good);bad['min_track_width_mm']=True
try:value=p.check_minimum_width_record({'source':str(board),'adapter':'both','minimum_width_guard':bad,'engine_budget':{'strict_class_targets':True}});outcome='passed';detail=value
except Exception as ex:outcome='reject';detail={'type':type(ex).__name__,'reason':str(ex)}
rows.append({'case':'receipt booleanTrue equals original numeric1 via dict equality','expected':'reject','outcome':outcome,'matched':outcome=='reject','detail':detail})
write(.65);stock=p.minimum_width_guard(board,'none');p.save_json(OWN/'results.json',{'native_validation_performed':False,'subprocesses_executed':0,'source_sha256_before':initial,'source_sha256_after':p.sha(ROOT/'autorouter/pipeline.py'),'stock_guard':stock,'results':rows});print(json.dumps(rows[-1],sort_keys=True))
