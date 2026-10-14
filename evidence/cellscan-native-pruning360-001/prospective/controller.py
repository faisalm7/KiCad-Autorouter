"""Frozen sequential larger-board probes using existing routing/process helpers.

Preparation is inert. The lead launches one explicit method at a time; shared
final/native readback, exact original warnings and full costs remain mandatory.
"""
import time,resource
START=time.monotonic()
usage=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
CPU0=usage.ru_utime+usage.ru_stime+child.ru_utime+child.ru_stime
from pathlib import Path
import argparse,datetime,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,strategy as strategy
from autorouter.runner import run
from scripts import experiment_quality as q,experiment_portfolio as portfolio

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--method',required=True,choices=('B2','C'))
parser.add_argument('--inner',action='store_true')
args=parser.parse_args();specpath=Path(__file__).with_name(args.method+'-protocol.json');spec=f.read_json(specpath)
SPEC_PIN=p.sha(specpath)
board=Path(spec['source']);out=Path(spec['output']);inner=Path(spec['inner_output'])
def elapsed_cpu():
    usage=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime+usage.ru_stime+child.ru_utime+child.ru_stime-CPU0
def stable():
    if p.sha(specpath)!=SPEC_PIN or f.read_json(specpath)!=spec:raise p.Rejected('prospective protocol changed')
    q.verify_freeze(spec['freeze'],board)
    for name,pin in spec['artifacts'].items():
        if p.sha(Path(name))!=pin:raise p.Rejected('frozen comparison prefix/controller changed')
    original=Path(spec['original_source_receipt']).parent/'original'
    if p.tree_hash(original)!=spec['original_notice_source_sha256']:
        raise p.Rejected('original notice-bearing eight-file source changed')
    if (spec['method']!=args.method or spec['outer_wall_full_cpu_cap_seconds']!=360
            or out.parent!=ROOT/'.runs' or inner.parent!=out
            or spec['freeze']['tools']['git_head']!='965796670d2835e185938d52ef694333e5752356'):
        raise p.Rejected('prospective scope or currency differs')
    committed=spec['already_committed_charge']
    if (spec['remaining_wall_seconds']!=360-committed['wall_seconds']
            or spec['remaining_full_cpu_seconds']!=360-committed['full_cpu_seconds']
            or spec['assigned_inner_seconds']!=min(spec['remaining_wall_seconds'],spec['remaining_full_cpu_seconds'])-2):
        raise p.Rejected('cumulative allocation differs')
if args.inner:
    stable()
    if args.method=='B2':
        result=portfolio.experiment(inner,'cellscan',budget=spec['assigned_inner_seconds'],
            allocation='balanced',outer_ceiling=360)
        index=inner/'portfolio-summary.json'
        terminal_ready=result.get('comparison_eligible') is True and result.get('all_variants_attempted') is True
    else:
        if q.freeze(board)!=spec['freeze']:raise p.Rejected('current committed C source differs from prospective freeze')
        result=strategy.prune(board,inner,spec['assigned_inner_seconds'],proposal_policy='feedback',incumbent_scoring='via_default')
        index=inner/'result.json';terminal_ready=result.get('accepted') is True
    stable()
    print(json.dumps(dict(method=args.method,status=result.get('status'),terminal_ready=terminal_ready,
        result=str(index),result_sha256=p.sha(index),accepted_in_method=result.get('accepted'),
        all_variants_attempted=result.get('all_variants_attempted'),improvements=result.get('improvements'))))
    raise SystemExit(0 if terminal_ready else 2)

stable();out.mkdir(exist_ok=False)
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--method',args.method,'--inner'],
    cwd=out,log=out/'command.log',timeout=spec['remaining_wall_seconds']-(time.monotonic()-START),
    max_log_bytes=256*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=2*1024**3)
stable()
index=inner/('portfolio-summary.json' if args.method=='B2' else 'result.json')
data=f.read_json(index) if index.is_file() and not index.is_symlink() else None
wall=time.monotonic()-START;cpu=elapsed_cpu();committed=spec['already_committed_charge']
record=dict(schema=1,method=args.method,accepted=False,comparison_eligible=False,
    process=process,prospective_protocol_sha256=p.sha(specpath),wrapper_sha256=p.sha(Path(__file__)),
    whole_new_wall_seconds=wall,whole_new_full_cpu_seconds=cpu,already_committed_charge=committed,
    combined_charged_wall_seconds=committed['wall_seconds']+wall,
    combined_charged_full_cpu_seconds=committed['full_cpu_seconds']+cpu,
    result=str(index),result_sha256=p.sha(index) if data is not None else None,
    inner_terminal_status=data.get('status') if data is not None else None,
    all_B2_variants_attempted=data.get('all_variants_attempted') if args.method=='B2' and data else None,
    prior_outcomes_unchanged=True,physical_electrical_validation=False,
    new_native_readback_required=True,claims_limit=spec['claims_limit'],finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    timing_scope='First controller line before project imports through retained result read; prior/new audit and bootstrap allowances are separately committed. Polling guards are not OS quotas; final small emission is covered by the charged1second bootstrap/emission allowance.')
record['within_cumulative360_caps']=max(record['combined_charged_wall_seconds'],record['combined_charged_full_cpu_seconds'])<=360
record['execution_closed']=(process['status'],process['exit_code']) in (('success',0),('nonzero_exit',2)) and process['cleanup_complete'] is True and data is not None and record['within_cumulative360_caps']
stable();p.save_json(out/'execution.json',record)
print(json.dumps({key:record[key]for key in ('method','inner_terminal_status','execution_closed','combined_charged_wall_seconds','combined_charged_full_cpu_seconds','within_cumulative360_caps','all_B2_variants_attempted')}))
raise SystemExit(0 if record['execution_closed'] else 2)
