"""Lead readback using shared validators; never reruns native or routing work."""
import time, resource
START=time.monotonic(); U=resource.getrusage(resource.RUSAGE_SELF); CPU0=U.ru_utime+U.ru_stime
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def forbidden(*args,**kwargs):raise AssertionError('readback cannot launch processes')
subprocess.run=forbidden;subprocess.Popen=forbidden
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,handoff as h
from scripts import experiment_portfolio as portfolio
from experiments.native_paired_v1.readback import final_candidate_readback,pruning_incumbent_readback,inherited_trial_accounting
parser=argparse.ArgumentParser();parser.add_argument('--method',required=True,choices=('B2','C'));parser.add_argument('--attempt',type=int,default=1);parser.add_argument('--prior-readback',type=Path);args=parser.parse_args()
draft=Path(__file__).parent;specpath=draft/(args.method+'-protocol.json');spec=f.read_json(specpath)
base=Path(spec['output']);folder=Path(spec['inner_output']);board=Path(spec['source'])
out=base.with_name(base.name+f'-readback-{args.attempt:03d}');out.mkdir(mode=0o700);owner={};h.capture_destination(owner,out)
index=folder/('portfolio-summary.json' if args.method=='B2' else 'result.json')
outer=f.read_json(base/'execution.json');data=f.read_json(index)
pins={**spec['artifacts'],str(specpath):p.sha(specpath),str(base/'execution.json'):p.sha(base/'execution.json'),str(index):p.sha(index),str(Path(__file__)):p.sha(Path(__file__))}
witness=pc.inventory(base,max_bytes=256*1024**2,max_files=12000,max_entries=24000,with_directories=True)
original=p.preflight(board);hashes=spec['freeze']['source_hashes']
native0=f.read_json(Path(spec['original_source_receipt']))['parity_native']
prior_wall=prior_cpu=0
if args.prior_readback:
    old=f.read_json(args.prior_readback);pins[str(args.prior_readback)]=p.sha(args.prior_readback)
    assert old['method']==args.method and old['status']=='invalidated' and old['new_native_execution'] is False
    cost=old['audit_cost'];prior_wall=cost['active_wall_seconds']+2;prior_cpu=cost['active_full_cpu_seconds']+2
    # Prior JSON samples precede the final return; charge an extra .25s for its
    # observed <.13s final tail. Never reclassify the invalidated receipt.
    prior_wall+=.25;prior_cpu+=.25
warnings=lambda native:f.canonical([x for x in native['findings'] if x['severity']=='warning'])
report=dict(schema=1,method=args.method,status='incomplete',passed=False,accepted=False,comparison_eligible=False,
    new_native_execution=False,new_engine_execution=False,physical_electrical_validation=False,
    controller_sha256=p.sha(Path(__file__)),inputs_sha256=pins,observations=[],claims_limit=spec['claims_limit'])
def measured():
    u=resource.getrusage(resource.RUSAGE_SELF);return time.monotonic()-START,u.ru_utime+u.ru_stime-CPU0
def remaining():
    wall,cpu=measured();return min(15-3-2-prior_wall-wall,15-3-2-prior_cpu-cpu)
def stable():
    h.owned_destination(owner)
    for name,pin in pins.items():
        if p.sha(Path(name))!=pin:raise p.Rejected('frozen retained evidence changed')
    if p.tree_hash(board.parent)!=hashes:raise p.Rejected('original source changed')
    if pc.inventory(base,max_bytes=256*1024**2,max_files=12000,max_entries=24000,with_directories=True)!=witness:raise p.Rejected('completed native evidence changed')
    for name,pin in {**spec['freeze']['files_sha256'],**spec['freeze']['tools']['files']}.items():
        path=Path(name) if Path(name).is_absolute() else ROOT/name
        if p.sha(path)!=pin:raise p.Rejected('frozen implementation/tool bytes changed')
    if remaining()<=0:raise p.Rejected('charged15 audit reserve exhausted')
def account():
    wall,cpu=measured();report['audit_cost']=dict(active_wall_seconds=wall,active_full_cpu_seconds=cpu,
        bootstrap_emission_allowance_seconds=2,separate_skeptical_review_allowance_seconds=3,
        prior_failed_readback_charged_wall_seconds=prior_wall,prior_failed_readback_charged_full_cpu_seconds=prior_cpu,
        charged_wall_seconds=wall+5+prior_wall,charged_full_cpu_seconds=cpu+5+prior_cpu,cap_seconds=15,within_caps=remaining()>0)
    if remaining()<=0:report.update(status='audit_budget_exceeded',passed=False,accepted=False,comparison_eligible=False)
def inspect(name,path,receipt,parent=None):
    if receipt.get('candidate_sha256') and receipt.get('native_report_sha256'):
        checked=final_candidate_readback(path,receipt,board,original,hashes,resource_parent=parent)
        checked.update(id=name,status=receipt['status'],accepted_in_receipt=receipt.get('accepted') is True,
            all209_original_warning_signatures_exact=warnings(receipt['native'])==warnings(native0),metrics=receipt.get('metrics'))
        report['observations'].append(checked);return checked
    report['observations'].append(dict(id=name,status=receipt.get('status'),final_native_available=False,accepted_in_receipt=False))
    return None
try:
    stable();assert outer['execution_closed'] and outer['within_cumulative360_caps']
    assert outer['result_sha256']==p.sha(index) and outer['prospective_protocol_sha256']==p.sha(specpath)
    assert outer['wrapper_sha256']==p.sha(draft/'controller.py')
    assert spec['new_final_readback_charge_seconds']==15 and spec['new_bootstrap_emission_charge_seconds']==1
    prior=spec['prior_whole_qualified_charge'];committed={k:v+16 for k,v in prior.items()}
    assert committed==spec['already_committed_charge']==outer['already_committed_charge']
    combined=dict(wall_seconds=committed['wall_seconds']+outer['whole_new_wall_seconds'],full_cpu_seconds=committed['full_cpu_seconds']+outer['whole_new_full_cpu_seconds'])
    assert combined['wall_seconds']==outer['combined_charged_wall_seconds'] and combined['full_cpu_seconds']==outer['combined_charged_full_cpu_seconds']
    assert max(combined.values())<=360
    process=outer['process'];assert (process['status'],process['exit_code']) in (('success',0),('nonzero_exit',2)) and process['cleanup_complete']
    assert process['argv']==[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(draft/'controller.py'),'--method',args.method,'--inner']
    assert process['cwd']==str(base) and Path(process['log'])==base/'command.log' and not process['log_truncated']
    assert Path(process['log']).stat().st_size==process['log_bytes']
    assert data['wall_seconds']<=outer['whole_new_wall_seconds'] and data['total_cpu_seconds']<=outer['whole_new_full_cpu_seconds']
    with p.validation_readback_session():
        if args.method=='B2':
            protocol=f.read_json(folder/'protocol.json');assert p.sha(folder/'protocol.json')==data['protocol_sha256']
            assert protocol['allocation']=='balanced' and protocol['variants']==list(portfolio.VARIANTS)
            assert protocol['wall_budget_seconds']==protocol['cpu_budget_seconds']==spec['assigned_inner_seconds']
            for row in data['trials']:
                if row.get('result'):
                    path=Path(row['result']);receipt=f.read_json(path);assert p.sha(path)==row['result_sha256']
                    if receipt.get('engine_budget'):p.check_engine_profile_record(receipt,path.parent)
                    observed=inspect('B2/'+row['id'],path.parent,receipt)
                    if row['eligible']:
                        portfolio.verify_row(row,board,portfolio.trial_freeze(protocol,row))
                        assert observed and observed['all209_original_warning_signatures_exact']
            eligible=[r for r in data['trials'] if r.get('eligible')]
            assert data['pareto_frontier']==portfolio.frontier(data['trials'])
            if data.get('selected'):
                chosen=min(eligible,key=portfolio.rank)
                assert all(data['selected'][k]==chosen[k] for k in ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm'))
            all_native=len(report['observations'])==3 and all(x.get('native_report_sha256') for x in report['observations'])
            qualified=data.get('comparison_eligible') is True and data.get('all_variants_attempted') is True and all_native
            report.update(all_variants_attempted=data.get('all_variants_attempted'),skipped_variants=data.get('skipped_variants',[]),selected=data.get('selected'),all_three_final_native_proofs=all_native)
        else:
            assert data['budget_seconds']==data['cpu_budget_seconds']==spec['assigned_inner_seconds']
            assert data['tools']==spec['freeze']['tools'] and data['source_hashes']==hashes
            if data.get('incumbent'):
                incumbent,checked=pruning_incumbent_readback(folder,data,board,original,hashes)
                checked.update(id='C/incumbent',status=incumbent['status'],all209_original_warning_signatures_exact=warnings(incumbent['native'])==warnings(native0),metrics=incumbent.get('metrics'))
                report['observations'].append(checked)
            if data.get('accepted'):p.check_result(index)
            final=inspect('C/final',folder,data)
            for row in data.get('trials',[]):
                path=folder/'trials'/row['id'];receipt=f.read_json(path/'result.json');inherited_trial_accounting(path,receipt,data)
                inspect('C/'+row['id'],path,receipt,data)
            qualified=data.get('accepted') is True and final is not None and final['all209_original_warning_signatures_exact']
            report.update(improvements=data.get('improvements'),metrics=data.get('metrics'),trials=data.get('trials'))
    report.update(status='readback_closed',passed=True,accepted=False,method_qualified=qualified,
        combined_charged_wall_full_cpu_seconds=combined,within_cumulative360_caps=True,
        comparison_eligible=False,comparison_limit='Method readback only; cross-method comparison and separate skeptical review remain required.')
except BaseException as exc:report.update(status='readback_failed',passed=False,reason=type(exc).__name__+': '+str(exc))
f.publish(out,report,stable,account,remaining,owned=lambda:h.owned_destination(owner));stable();account()
if report['status']!='readback_closed':report['passed']=False
print(json.dumps({k:report.get(k) for k in ('method','status','passed','accepted','reason','audit_cost','metrics','improvements','all_three_final_native_proofs','combined_charged_wall_full_cpu_seconds')}))
raise SystemExit(0 if report['passed'] and report['status']=='readback_closed' else 2)
