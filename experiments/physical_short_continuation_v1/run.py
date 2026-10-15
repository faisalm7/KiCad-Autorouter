"""UNEXECUTED physical-short-only005; all failed001002003004/readers charged."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import argparse,json,signal,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.physical_short_continuation_v1.actor import check_outer_witness
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
if not a.run_native:ap.error('explicit Native opt-in required')
spec=f.read_json(a.protocol);prior=spec['prior_costs'];here=Path(__file__).resolve().parent
if spec['status']!='prospectively_frozen' or p.sha(a.protocol)!=a.protocol_sha256 or p.sha(__file__)!=spec['wrapper_sha256'] or p.sha(here/'actor.py')!=spec['actor_sha256']:raise p.Rejected('unfrozen outer')
for name,pin in spec['code_sha256'].items():
    if p.sha(ROOT/name)!=pin:raise p.Rejected('frozen current code differs: '+name)
PUBLICATION_ALLOWANCE=1
out=a.output;execution=out.parent/(out.name+'-execution')
if out.parent!=ROOT/'.runs' or any(path.exists() or path.is_symlink() for path in (out,execution)):raise p.Rejected('fresh direct actor/outer outputs required')
execution.mkdir();owner={};h.capture_destination(owner,execution)
def remaining():return min(120-prior['wall_seconds']-PUBLICATION_ALLOWANCE-(time.monotonic()-START),120-prior['full_cpu_seconds']-PUBLICATION_ALLOWANCE-(cpu()-CPU0))
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(here/'actor.py'),'--run-native','--output',str(out),'--protocol',str(a.protocol),'--protocol-sha256',a.protocol_sha256],cwd=execution,log=execution/'command.log',timeout=max(.001,remaining()),max_log_bytes=2_000_000,max_workdir_bytes=16*1024**2,max_group_rss_bytes=4*1024**3)
inner=f.read_json(out/'result.json') if (out/'result.json').is_file() else None
record=dict(schema=1,kind='selected-proposal-physical-short-only-outer',status='cancelled' if process['status']=='cancelled' else 'completed',accepted=False,production_admitted=False,method_qualified=bool(inner and inner.get('method_qualified') and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']),process=process,protocol_sha256=a.protocol_sha256,prior_costs=prior,publication_allowance_seconds=PUBLICATION_ALLOWANCE,inner_receipt_sha256=p.sha(out/'result.json') if inner else None,driver_sha256=p.sha(here/'actor.py'),wrapper_sha256=p.sha(__file__),log_sha256=p.sha(execution/'command.log'))
def account():
    wall,full=time.monotonic()-START,cpu()-CPU0
    record.update(new_wall_seconds=wall,new_full_cpu_seconds=full,charged_wall_seconds=prior['wall_seconds']+PUBLICATION_ALLOWANCE+wall,charged_full_cpu_seconds=prior['full_cpu_seconds']+PUBLICATION_ALLOWANCE+full,within_cumulative120_caps=remaining()>0,cumulative_active002_reader_and_short_wall_seconds=27.294584+prior['wall_seconds']+PUBLICATION_ALLOWANCE+wall,cumulative_active002_reader_and_short_full_cpu_seconds=22.430367+prior['full_cpu_seconds']+PUBLICATION_ALLOWANCE+full)
    if record['status']!='completed' or not record['within_cumulative120_caps']:record['method_qualified']=False

def stable():
    h.owned_destination(owner)
    if remaining()<=0 or p.sha(a.protocol)!=a.protocol_sha256 or p.sha(here/'actor.py')!=spec['actor_sha256'] or p.sha(__file__)!=spec['wrapper_sha256']:raise p.Rejected('outer cumulative cap/frozen sources changed')
    if inner and p.sha(out/'result.json')!=record['inner_receipt_sha256']:raise p.Rejected('continuation receipt changed')
    if record['method_qualified']:check_outer_witness(out,inner,spec,a.protocol_sha256)
f.publish(execution,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
print(json.dumps({k:record[k] for k in ('status','method_qualified','charged_wall_seconds','charged_full_cpu_seconds','within_cumulative120_caps')}));raise SystemExit(0 if record['method_qualified'] else 2)
