"""Synthetic complete receipt controls only; no native/process/solver execution."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,preferences as pref,routing_scope as rs,sexpr as sx,adapter as a
OWN=Path(__file__).resolve().parent;old=ROOT/'.runs/selected-net-implementation-review-001/synthetic';base=OWN/'receipt-seam';run=base/'run';receipt=run/'result.json'
def rebase(value):
 if type(value)is str:return value.replace(str(old),str(base))
 if type(value)is list:return [rebase(x) for x in value]
 if type(value)is dict:return {k:rebase(v) for k,v in value.items()}
 return value
for file in run.glob('*.json'):
 if file.name=='routing-preferences.json':continue
 p.save_json(file,rebase(json.loads(file.read_text())))
data=json.loads(receipt.read_text());names=['SEL'];choices={'scope':'selected_nets','nets':names,'profile':'completion-only','adapter':'both'};request={'captured':None,'effective':pref.resolve(overrides=choices),'snapshot':pref.snapshot(overrides=choices)};(run/'routing-preferences.json').rename(run/'initial-routing-preferences.json');p.capture_preferences(data,run,request);data['adapter']='both'
raw=b'(pcb fixture (parser (string_quote ")) (unit um) (resolution um 10) (structure (layer F.Cu (type signal)) (layer B.Cu (type signal)) (rule (width 200) (clearance 150))) (placement) (library) (network (net SEL (pins J1-1)) (net OTHER (pins J2-1)) (class kicad_default SEL OTHER (circuit (use_via V)) (rule (width 200) (clearance 150)))) (wiring))\n'
(run/'native.dsn').write_bytes(raw);scoped=run/'routing-scope-input.dsn';scoped.write_bytes(raw);data['adapter_transformations']=a.adapt_dsn(scoped,'both',[]);emitted,binding=rs.partition_dsn(scoped.read_bytes(),names);(run/'task.dsn').write_bytes(emitted);data['selected_dsn_binding']=binding;data['native_dsn_sha256']=p.sha(run/'native.dsn');data['task_dsn_sha256']=p.sha(run/'task.dsn');settings=p.engine_profile_settings('completion-only',100,strict_class_targets=True);settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120);settings['argv'].append(binding['engine_argument']);data['engine_budget']=settings;data['steps'][0]['argv']=p.engine_argv(run,settings['argv']);p.save_json(run/'engine-process.json',data['steps'][0]);p.save_json(receipt,data)
initial={str(x):p.sha(ROOT/x) for x in ['autorouter/pipeline.py','autorouter/routing_scope.py']};good={file:file.read_bytes() for file in [scoped,run/'task.dsn',run/'routing-preferences.json',run/'engine-process.json']};results=[]
def check(label,mutate=None,expected='reject'):
 for file,raw in good.items():file.write_bytes(raw)
 d=copy.deepcopy(data)
 if mutate:mutate(d)
 p.save_json(receipt,d)
 try:
  with patch('subprocess.run',side_effect=AssertionError('forbidden subprocess')),patch('subprocess.Popen',side_effect=AssertionError('forbidden subprocess')):v=p.check_result(receipt)
  outcome='current'
 except (p.Rejected,ValueError,KeyError,FileNotFoundError) as ex:outcome='reject';v={'type':type(ex).__name__,'reason':str(ex)}
 entry={'case':label,'outcome':outcome,'expected':expected,'matched':outcome==expected,'detail':v};results.append(entry);print(json.dumps(entry,sort_keys=True))
check('complete selected Default/both-adapter partition positive',expected='current')
def wrong_rule(d):
 tree=a._parse_dsn(scoped.read_text());row=sx.one(sx.one(tree,'network'),'class');sx.one(sx.one(row,'rule'),'width')[1]='100';scoped.write_bytes(a._dump_dsn(tree).encode());emitted,binding=rs.partition_dsn(scoped.read_bytes(),names);(run/'task.dsn').write_bytes(emitted);d['selected_dsn_binding']=binding;d['task_dsn_sha256']=p.sha(run/'task.dsn');d['adapter_transformations']['output_sha256']=binding['input_sha256']
check('rehashed scope input weakens original Native DSN class width via adapter lineage',wrong_rule)
def remove_flag(d,flag):
 d['engine_budget']['argv']=[x for x in d['engine_budget']['argv'] if not x.startswith(flag)];d['steps'][0]['argv']=p.engine_argv(run,d['engine_budget']['argv']);p.save_json(run/'engine-process.json',d['steps'][0])
check('ignore flag removed with process and engine-budget rebound',lambda d:remove_flag(d,'--router.autorouter.ignore_net_classes'))
check('fanout safety flag removed with process and engine-budget rebound',lambda d:remove_flag(d,'--router.fanout.enabled'))
check('optimizer safety flag removed with process and engine-budget rebound',lambda d:remove_flag(d,'--router.optimizer.enabled'))
check('missing partition binding',lambda d:d.pop('selected_dsn_binding'))
check('scope downgrade retaining actual scoped-input marker',lambda d:d.update(scope='whole_board_unlocked_routing'))
for file,raw in good.items():file.write_bytes(raw)
p.save_json(receipt,data)
p.save_json(OWN/'receipt-scope-results.json',{'native_validation_performed':False,'subprocesses_executed':0,'source_sha256_before':initial,'source_sha256_after':{x:p.sha(ROOT/x) for x in initial},'results':results})
