"""Whole-process cap and retained final readback for the single fused006 trial."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import sys,json,argparse
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from experiments.thermal_group_pruning_v1 import actor as d
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');args=parser.parse_args()
if not args.run_native:parser.error('explicit Native opt-in required')
out=ROOT/'.runs/nus-thermal-group-pruning120-006';outer=out.with_name(out.name+'-execution')
if out.exists() or outer.exists():raise p.Rejected('fresh006 prefixes required; no repeated experiment')
spec=f.read_json(d.PROTOCOL);pin=p.sha(d.PROTOCOL);prior=d.prior_charge();tools=p.tool_manifest()
assert spec['prior_costs']==prior and spec['wrapper_sha256']==p.sha(Path(__file__))
outer.mkdir();allowance=1;reader_reserve=3
left=min(120-prior['wall_seconds'],120-prior['full_cpu_seconds'])-allowance-reader_reserve
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(d.__file__)),'--run-native','--output',str(out)],cwd=outer,log=outer/'command.log',timeout=max(.001,left-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=4*1024**3)
qualified=False;error=None;receipt=out/'result.json'
try:
    child=f.read_json(receipt);receipt_pin=p.sha(receipt)
    assert child['method_qualified'] is True and child['accepted'] is False and child['production_admitted'] is False
    assert child['tools']==tools and child['protocol_sha256']==pin and child['prior_costs']==prior
    d.check(out,child,spec,final=True)
    d.final_material(out,child,spec,tools,receipt_pin,pin)
    assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
    qualified=True
except Exception as exc:error=type(exc).__name__+': '+str(exc)
wall=time.monotonic()-START;full=cpu()-CPU0
record=dict(schema=1,accepted=False,production_admitted=False,method_qualified=qualified,error=error,process=process,
    source_tools=tools,protocol_sha256=pin,wrapper_sha256=p.sha(Path(__file__)),actor_sha256=p.sha(Path(d.__file__)),
    child_receipt_sha256=p.sha(receipt) if receipt.is_file() else None,log_sha256=p.sha(outer/'command.log'),
    prior_costs=prior,new_wall_seconds=wall,new_full_cpu_seconds=full,publication_allowance_seconds=allowance,
    independent_readback_reserve_seconds=reader_reserve,charged_wall_seconds=prior['wall_seconds']+wall+allowance,
    charged_full_cpu_seconds=prior['full_cpu_seconds']+full+allowance,
    within_cumulative120_with_reader_reserve=max(prior['wall_seconds']+wall,prior['full_cpu_seconds']+full)+allowance+reader_reserve<120,
    scope='ONE fused new candidate/final Native validation only. All old001..005 costs/proofs immutable; final outer readbacks and publication charged, three seconds reserved for independent readback. SingleexposedNUS diagnostic, no normal-C/general/comparative claim.')
if not record['within_cumulative120_with_reader_reserve']:
    record.update(method_qualified=False,error=record['error'] or 'cumulative120 publication/readback reserve exhausted')
p.save_json(outer/'execution.json',record);print(json.dumps({k:record[k] for k in ('method_qualified','error','charged_wall_seconds','charged_full_cpu_seconds','within_cumulative120_with_reader_reserve')}));raise SystemExit(0 if qualified and record['within_cumulative120_with_reader_reserve'] else 2)
