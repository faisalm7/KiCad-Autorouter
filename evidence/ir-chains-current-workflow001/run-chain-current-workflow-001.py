"""Use the existing real preview/intent/native-export qualifier on one retained chain candidate."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,argparse
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,review_export as e
from autorouter.runner import run
parser=argparse.ArgumentParser(description=__doc__)
for name in ('receipt','output','enclosure'):parser.add_argument('--'+name,type=Path,required=True)
a=parser.parse_args();O=a.enclosure.absolute();O.mkdir();receipt=a.receipt.resolve(strict=True);out=a.output.absolute();tools=p.tool_manifest();controller=R/'scripts/qualify_review_export.py';pin=p.sha(controller);sourcepin=p.sha(receipt);own=p.sha(Path(__file__))
argv=[*f.SANDBOX,str(R/'.venv/bin/python'),'-B',str(controller),'--receipt',str(receipt),'--render','--output',str(out),'--run-native']
p.save_json(O/'prospective.json',dict(schema=1,receipt=str(receipt),receipt_sha256=sourcepin,tools=tools,controller_sha256=pin,wrapper_sha256=own,outer_wall_full_cpu_cap_seconds=180,publication_allowance_seconds=2,argv=argv,claims='Preview/acceptreject testintents/freshNativeexport qualification only; no solver/newcomparison/GUI/human/liveapplication.'))
record=dict(schema=1,passed=False,tools=tools,controller_sha256=pin,wrapper_sha256=own,source_receipt_sha256=sourcepin,new_routing_executed=False,gui_qualified=False,human_pcb_approval_observed=False)
try:
 process=run(argv,cwd=O,log=O/'command.log',timeout=max(.001,178-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=4*1024**3);record['process']=process
 data=f.read_json(out/'result.json');current=p.tool_manifest()==tools and p.sha(controller)==pin and p.sha(receipt)==sourcepin
 record.update(source_current=current,result_sha256=p.sha(out/'result.json'),observed_status=data['status'],observed_controls_passed=data['controls_passed'],scope=data['scope'])
 record['passed']=current and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False and data['status']=='completed' and data['controls_passed'] is True
except (Exception,KeyboardInterrupt) as exc:record.update(passed=False,error=type(exc).__name__+': '+str(exc))
record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
if max(record['wall_seconds'],record['full_cpu_seconds'])+2>180:record.update(passed=False,error='Wholeworkflowdelivery exceeds180seconds')
p.save_json(O/'execution.json',record);print(json.dumps({k:record.get(k) for k in ('passed','observed_status','wall_seconds','full_cpu_seconds','error')}));raise SystemExit(0 if record['passed'] else 2)
