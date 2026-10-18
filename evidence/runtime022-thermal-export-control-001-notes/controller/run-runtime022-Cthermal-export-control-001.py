"""Correct explicit CLI budget in a NEW export control; v3 remains failed."""
from pathlib import Path
import sys,json,os,resource,time
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-022/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,review_export as ex,placement_clearance as pc,floor_route as f
from autorouter.runner import run
case=ROOT/'.runs/runtime-directory-022/Cthermal-export-control-001-run';case.mkdir();out=runtime/'.runs/Cthermal-export-control-001';prior=runtime/'.runs/interf-installed022-comparison-001/C_thermal';choice=prior/'choice/choice.json';receipt=prior/'thermal-route/result.json';data=f.read_json(receipt);tools=p.tool_manifest();assert data['accepted'] and p.check_result(receipt)['current']
source=Path(data['source']);pins=data['source_hashes'];assert pc.inventory(source.parent)==pins;bound={str(q):p.sha(q)for q in(receipt,choice)};commands=[];processes=[]
python=[str(runtime/'.venv/bin/python'),'-B','-m','autorouter'];commands=[('export',python+['review-export',str(choice),'--seconds','120','--output',str(out)]),('check',python+['review-export-check',str(out/'export.json')])]
p.save_json(case/'protocol.json',dict(schema=1,kind='fresh-installed022-existing-thermal-receipt-export-control-v1',source=str(source),source_hashes=pins,prior_receipt_sha256=bound[str(receipt)],choice_sha256=bound[str(choice)],tools=tools,commands=commands,export_wall_fullCPU_seconds=120,whole_control_wall_fullCPU_seconds=180,new_routing=False,scope='New standalone export-only correctness control using valid explicit120s Native budget. v3Cthermal remains failed; do not stitch into comparative success. Each newfinal keeps own Native/fullSCH/original proof. Research qualificationcost separate from v3.'))
env={k:v for k,v in os.environ.items()if k not in{'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
passed=False;error=None;checked=None
try:
 for name,argv in commands:
  assert p.tool_manifest()==tools and pc.inventory(source.parent)==pins and all(p.sha(Path(q))==pin for q,pin in bound.items())
  left=min(175-(time.monotonic()-START),175-(cpu()-CPU0));assert left>1
  process=run([*f.SANDBOX,*argv],cwd=runtime,env=env,log=case/(name+'.log'),timeout=min(140,left),max_log_bytes=256*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=512*1024**2);processes.append(dict(stage=name,process=process));p.save_json(case/(name+'-process.json'),process)
  assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']
 checked=ex.check_export(out/'export.json');assert checked['current'] and p.tool_manifest()==tools and pc.inventory(source.parent)==pins and all(p.sha(Path(q))==pin for q,pin in bound.items());passed=True
except BaseException as exc:error=type(exc).__name__+': '+str(exc)
record=dict(schema=1,passed=passed,accepted=False,project_complete=False,new_routing=False,comparative_success=False,actual_GUI=False,processes=processes,checked=checked,error=error,sampled_wall_seconds=time.monotonic()-START,sampled_fullCPU_seconds=cpu()-CPU0,export_receipt=str(out/'export.json'),export_receipt_sha256=p.sha(out/'export.json')if(out/'export.json').exists()else None)
if max(record['sampled_wall_seconds'],record['sampled_fullCPU_seconds'])>180:record['passed']=False
p.save_json(case/'execution.json',record);print(json.dumps({k:v for k,v in record.items()if k!='processes'}));raise SystemExit(0 if record['passed']else 2)
