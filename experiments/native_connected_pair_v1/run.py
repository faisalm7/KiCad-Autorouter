"""Unexecuted actual120s outer supervisor; launch arms sequentially only."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import argparse,json,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.native_connected_pair_v1.driver import check_outer_witness
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--method',choices=('all-active','native-connected'),required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True);a=parser.parse_args()
if not a.run_native:parser.error('explicit native execution required')
out=a.output;execution=out.parent/(out.name+'-execution');here=Path(__file__).resolve().parent
if out.parent!=ROOT/'.runs' or any(x.exists() or x.is_symlink() for x in (out,execution,out.parent/(out.name+'-classifier'))):raise p.Rejected('three fresh direct sibling outputs required')
if p.sha(a.protocol)!=a.protocol_sha256:raise p.Rejected('prospective protocol SHA differs')
spec=f.read_json(a.protocol)
if p.sha(Path(__file__))!=spec['wrapper_sha256']:raise p.Rejected('frozen supervisor differs')
execution.mkdir();owner={};h.capture_destination(owner,execution)
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(here/'driver.py'),'--run-native','--method',a.method,'--output',str(out),'--protocol',str(a.protocol),'--protocol-sha256',a.protocol_sha256],cwd=execution,log=execution/'command.log',timeout=max(.001,120-(time.monotonic()-START)),max_log_bytes=2_000_000,max_workdir_bytes=16*1024**2,max_group_rss_bytes=4*1024**3)
inner=f.read_json(out/'result.json') if (out/'result.json').is_file() else None
record=dict(schema=1,kind='NUS120 connected-activity outer actual-cost diagnostic',status='completed',accepted=False,method=a.method,method_qualified=bool(inner and inner.get('method_qualified') and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']),production_admitted=False,process=process,protocol_sha256=a.protocol_sha256,inner_receipt_sha256=p.sha(out/'result.json') if inner is not None else None,driver_sha256=p.sha(here/'driver.py'),wrapper_sha256=p.sha(Path(__file__)),log_sha256=p.sha(execution/'command.log'))
def remaining():return min(120-(time.monotonic()-START),120-(cpu()-CPU0))
def account():
    record.update(wall_seconds=time.monotonic()-START,total_cpu_seconds=cpu()-CPU0,within_parent120_caps=remaining()>0)
    if record['status']!='completed' or not record['within_parent120_caps']:record['method_qualified']=False
def stable():
    h.owned_destination(owner)
    if remaining()<=0:raise p.Rejected('outer full120 wall/CPU exceeded')
    if p.sha(a.protocol)!=a.protocol_sha256 or p.sha(here/'driver.py')!=spec['driver_sha256'] or p.sha(Path(__file__))!=spec['wrapper_sha256']:raise p.Rejected('frozen outer inputs changed')
    if inner is not None and p.sha(out/'result.json')!=record['inner_receipt_sha256']:raise p.Rejected('inner receipt changed')
    if record['method_qualified']:check_outer_witness(out,inner,a.method,a.protocol_sha256,spec)
f.publish(execution,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
print(json.dumps({k:record[k] for k in ('status','method_qualified','wall_seconds','total_cpu_seconds','within_parent120_caps')}));raise SystemExit(0 if record['method_qualified'] else 2)
