"""Current exact finalization controls; mocked DRC readback is not native proof."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast,hashlib,json,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.original_project_native_v1 import driver as d
source=Path(d.__file__).read_text();(HERE/'driver-final-control-source.py').write_text(source)
function=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='experiment');tail=next(n.finalbody for n in function.body if isinstance(n,ast.Try) and n.finalbody);code=compile(ast.Module(body=tail,type_ignores=[]),str(d.__file__),'exec')
results={}
for mode in ['normal','pre-witness-class','post-canonical-class','pre-witness-report','post-canonical-candidate']:
 out=HERE/('final-publication-'+mode);out.mkdir();original=out/'original';(original/'hardware').mkdir(parents=True)
 pcb=b'(kicad_pcb (version 20260206) (segment (start 0 0) (end 1 0) (width 0.6) (layer "F.Cu") (net "/P") (uuid "authored-route")))\n'
 files={'LICENSE':b'authored notice','hardware/ArcDice.kicad_pcb':pcb,'hardware/ArcDice.kicad_pro':b'{}','hardware/ArcDice.kicad_sch':b'authored schematic'}
 for name,raw in files.items():(original/name).write_bytes(raw)
 before=d.p.tree_hash(original);board=original/'hardware/ArcDice.kicad_pcb'
 saved=out/'saved';saved.mkdir();candidate=out/'candidate';candidate.mkdir()
 for folder in [saved,candidate]:
  for name in ['ArcDice.kicad_pcb','ArcDice.kicad_pro','ArcDice.kicad_sch']:(folder/name).write_bytes((board.parent/name).read_bytes())
 savedboard=saved/board.name;candidate=candidate/board.name;saved_before=d.p.tree_hash(saved);candidate_before=d.p.tree_hash(candidate.parent)
 jobdir=out/'job';jobdir.mkdir();context=jobdir/'class-context.json';observation=jobdir/'class-observation.json';dsn=jobdir/'original.dsn';finalreport=jobdir/'original-final.json'
 for path in [context,observation,finalreport]:path.write_text('{"authored":true}\n')
 dsn.write_text('authored DSN placeholder\n');fake_native={'fixture':'mocked readback only'}
 record={'schema':1,'status':'observed','accepted':False,'native_routing_scope_accepted':True,'helper_sha256':d.p.sha(Path(d.__file__)),'class_context_sha256':d.p.sha(context),'class_observation_sha256':d.p.sha(observation),'original_dsn_sha256':d.p.sha(dsn),'final_candidate_sha256':d.p.sha(candidate),'final_native_report_sha256':d.p.sha(finalreport),'original_native':fake_native,'parity_native':fake_native,'budget_seconds':90.,'cpu_budget_seconds':90.,'production_support_qualified':False}
 owner={};d.h.capture_destination(owner,out);start=time.monotonic();cpu0=time.process_time()+d.f.child_cpu();calls=[];witness_calls=[];real_witness=d.completed_evidence;real_save=d.p.save_json
 def mutate():
  if mode.endswith('candidate'):candidate.write_bytes(pcb.replace(b'(width 0.6)',b'(width 0.7)'))
  elif mode.endswith('report'):finalreport.write_text('{"changed_report":true}\n')
  else:observation.write_text('{"changed_observation":true}\n')
 def witness(path):
  witness_calls.append(path)
  if mode.startswith('pre-witness') and len(witness_calls)==1:mutate()
  return real_witness(path)
 def publish(path,value):
  real_save(path,value);calls.append(path)
  if mode.startswith('post-canonical') and len(calls)==1:mutate()
 env={'Path':Path,'__file__':d.__file__,'project':'arcdice','candidate':candidate,'board':board,'savedboard':savedboard,'saved_before':saved_before,'candidate_before':candidate_before,'context':context,'observation':observation,'dsn':dsn,'route_records':d.route_records,'sx':d.sx,'record':record,'job':SimpleNamespace(out=jobdir,steps=[]),'owner':owner,'out':out,'before':before,'files':files,'snapshot':SimpleNamespace(capture=lambda:dict(files)),'started':start,'cpu0':cpu0,'SECONDS':90.,'LIMIT':d.LIMIT,'h':d.h,'p':d.p,'f':d.f,'time':time,'remaining':lambda:90.-(time.monotonic()-start),'size':lambda:sum(len(v) for v in d.io.inventory(out,contents=True,max_bytes=d.LIMIT,max_files=2048,max_entries=4096).values()),'completed':None,'bound_native':None,'completed_evidence':witness,'hashlib':hashlib}
 with patch.object(d.f,'check_drc_stage',return_value=fake_native),patch.object(d.p,'save_json',side_effect=publish):exec(code,env)
 canonical=d.f.read_json(out/'result.json')
 if mode=='normal':assert canonical['status']=='observed' and canonical['native_routing_scope_accepted'] is True
 else:assert canonical['status']!='observed' and canonical['native_routing_scope_accepted'] is False
 results[mode]={'status':canonical['status'],'native_scope_flag':canonical['native_routing_scope_accepted'],'reason':canonical.get('reason'),'error':canonical.get('error'),'witness_calls':len(witness_calls),'archives':len(list(out.glob('invalidated-result-*')))}
print(json.dumps({'schema':1,'scope':'Exact current controller suffix, authored source/evidence, mocked DRC readback; NO native qualification','driver_sha256':hashlib.sha256(source.encode()).hexdigest(),'results':results},indent=2))
