"""Finite CLI integration only after guarded class policy is committed."""
from pathlib import Path
import sys,time,json,os
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io
from autorouter.runner import run
from experiments.licensed_acquisition_v1.fetch import cancellation
out=ROOT/'.runs/parent-class-production-native-001';out.mkdir();owner={};h.capture_destination(owner,out);tools=p.tool_manifest();sources={};commands=[]
env=os.environ.copy();env.update(PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1')
base=ROOT/'.runs/netclass-parent-transport-001/controls'
for case in ('whole_unprotected','partial_protected'):sources[case]=io.inventory(base/case/'original')
with cancellation():
 for case in ('whole_unprotected','partial_protected'):
  board=base/case/'original/fixture.kicad_pcb';result=out/case/'result.json'
  route=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B','-m','autorouter','route',str(board),'--output',str(result.parent),'--seconds','120','--adapter','both','--profile','completion-only']
  if case=='partial_protected':route.append('--keep-existing')
  for name,argv in [(case+'-route',route),(case+'-check',[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B','-m','autorouter','check-result',str(result)])]:
   step=run(argv,cwd=out,env=env,log=out/(name+'.log'),timeout=min(150,180-time.monotonic()+START),max_log_bytes=384*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=2*1024**3)
   commands.append({'name':name,**step});p.save_json(out/(name+'-process.json'),commands[-1])
   if step['status']!='success' or step['exit_code']!=0 or not step['cleanup_complete']:raise p.Rejected('actual production integration failed: '+name)
  data=f.read_json(result);verified=p.check_result(result)
  if data['netclass_policy']['mode']!='native-parent-dimensions-v1' or not data['accepted'] or not p.native_accepted(data['native']):raise p.Rejected('actual production class route not accepted')
  if data['native']['warnings']!=0 or io.inventory(board.parent)!=sources[case]:raise p.Rejected('production source/warning regression')
 h.owned_destination(owner)
 if p.tool_manifest()!=tools:raise p.Rejected('production integration Source/tool freeze changed')
 elapsed=time.monotonic()-START+1;cpu=h.cpu_seconds()
 if max(elapsed,cpu)>180:raise p.Rejected('whole production integration budget exceeded')
 record={'schema':1,'status':'qualified','accepted':False,'production_cli_qualified':True,'tools':tools,'commands':commands,'sources_before_after':sources,'charged_wall_seconds':elapsed,'lifetime_full_cpu_seconds':cpu,'results':{case:{'result_sha256':p.sha(out/case/'result.json'),'candidate_sha256':f.read_json(out/case/'result.json')['candidate_sha256'],'native':f.read_json(out/case/'result.json')['native'],'metrics':f.read_json(out/case/'result.json')['metrics']} for case in sources},'scope':'Actual new production route/check integration after code change: whole/unprotected and partial/exactprotected threeclass copies. Not repeated diagnostic experiment or ArcDice comparative run. Source/prior native records immutable; noSCHfixture/human/physical/broad gain. One lead, sequential2JAR, no network. Whole180wall/fullCPU+startup1 allowance; individual120caps. Inner sharedrunner4GiBgroup512MiB stage; enclosingmain2GiBgroup guard cannot sum separate childgroups. Workdir32MiB disposable integration subtree, source/root sideeffects and resource accounting checked by actual CLI validator.'}
 p.save_json(out/'execution.json',record);h.owned_destination(owner);assert f.read_json(out/'execution.json')==record
print(json.dumps({k:record[k] for k in ('status','charged_wall_seconds','lifetime_full_cpu_seconds')}))
