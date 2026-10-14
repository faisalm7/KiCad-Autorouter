"""Shared final readback for frozen native-all development comparisons.

Uses the pipeline, native-stage, portfolio and publication validators. Runs no
native process. A failed or over-budget arm stays in the four-arm population.
The prospective protocol determines costs; this cannot repair an old receipt.
"""
from pathlib import Path
import time
START = time.monotonic()
CPU0 = time.process_time()
import argparse
import copy
import hashlib
import json
import signal
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as pc
from autorouter import handoff as h, sexpr as sx
from scripts import experiment_paired as paired, experiment_quality as q
CPU0 += f.child_cpu()


def qualify(base, prospective, output, source_receipt, source_readback):
    base, prospective, output = map(lambda x: Path(x).resolve(), (base, prospective, output))
    source_receipt, source_readback = map(lambda x: Path(x).resolve(), (source_receipt, source_readback))
    output.mkdir()
    owner = {}
    h.capture_destination(owner, output)
    spec = f.read_json(prospective)
    cap = spec['final_readback_allowance_wall_full_cpu_seconds']
    if not q.finite_nonnegative(cap) or not 1 <= cap <= 30:
        raise p.Rejected('invalid prospective audit allowance')
    protocol = f.read_json(base/'run/protocol.json')
    summary = f.read_json(base/'run/paired-summary.json')
    outer = f.read_json(base/'execution.json')
    witness = pc.inventory(base, max_bytes=96*1024**2, max_files=6000,
                           max_entries=12000, with_directories=True)
    board = Path(protocol['source'])
    original = p.preflight(board)
    original_record = f.read_json(source_receipt)
    original_readback = f.read_json(source_readback)
    original_native = original_readback['native']
    def signatures(native):
        return f.canonical([x for x in native['findings'] if x['severity']=='warning'])
    rows = []
    report = dict(schema=1, kind='native-all-complete-schematic-final-readback-v1',
                  status='incomplete', accepted=False, comparison_eligible=False,
                  new_native_execution=False, physical_electrical_validation=False,
                  controller_sha256=p.sha(Path(__file__)),
                  prospective_protocol_sha256=p.sha(prospective),
                  paired_summary_sha256=p.sha(base/'run/paired-summary.json'),
                  outer_execution_sha256=p.sha(base/'execution.json'),
                  original_receipt_sha256=p.sha(source_receipt),
                  original_readback_sha256=p.sha(source_readback),
                  audit_wall_and_full_cpu_charge_seconds=cap,
                  startup_allowance_wall_full_cpu_seconds=1,
                  shared_original_qualification_cost=spec['shared_original_qualification_cost'],
                  claims_limit=spec['limits'],
                  stock_scope='raw stock DSN with the same class-target safety settings; not untouched Freerouting defaults')

    def remaining():
        return min(cap-(time.monotonic()-START), cap-(time.process_time()+f.child_cpu()-CPU0))

    def stable():
        h.owned_destination(owner)
        q.verify_freeze(protocol['freeze'], board)
        if pc.inventory(base, max_bytes=96*1024**2, max_files=6000,
                        max_entries=12000, with_directories=True) != witness:
            raise p.Rejected('completed comparison changed during readback')
        for path, key in ((prospective,'prospective_protocol_sha256'),
                          (source_receipt,'original_receipt_sha256'),
                          (source_readback,'original_readback_sha256')):
            if p.sha(path) != report[key]:
                raise p.Rejected('prospective or original evidence changed')
        source = {name: meta['sha256'] for name, meta in spec['source_five_files'].items()}
        if p.tree_hash(source_receipt.parent/'original') != source:
            raise p.Rejected('original complete notice-bearing source changed')
        if report['comparison_eligible'] and remaining() <= 0:
            raise p.Rejected('complete readback exceeds its prospective allowance')

    def final_candidate(folder, data):
        candidate = folder/'candidate'/board.name
        p.verify_candidate_files(candidate, protocol['freeze']['source_hashes'], data['candidate_sha256'])
        tree = sx.read(candidate)
        if p.immutable(tree) != p.immutable(original):
            raise p.Rejected('final immutable design differs')
        protected = p.protected_for_record({'scope':'whole_board_unlocked_routing'}, original)
        if any(route not in p.routes(tree) for route in protected):
            raise p.Rejected('final protected copper differs')
        before = dict(protocol['freeze']['source_hashes'])
        before[board.name] = data['candidate_sha256']
        native = f.check_drc_stage(folder, data, 'final-drc', candidate,
            folder/'final-drc-input'/board.name, False, before,
            schematic_parity=True, sandboxed=False)
        if native != data['native'] or p.sha(folder/'final-drc.json') != data['native_report_sha256']:
            raise p.Rejected('final native report differs')
        classes = f.read_json(folder/'final-netclasses.json')
        class_audit = p.audit_candidate_netclasses(candidate, protected, classes)
        from autorouter import config as c
        f.process_check(folder, data, 'final-netclasses', [str(c.PYTHON),
            str(c.ROOT/'autorouter/native.py'), 'netclasses', str(candidate),
            str(folder/'final-netclasses.json')])
        return dict(path=str(candidate), candidate_sha256=data['candidate_sha256'],
            native_report_sha256=data['native_report_sha256'],
            native_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},
            native_rejection_reasons=p.native_rejection_reasons(native),
            original_design_checks=True, complete_schematic_native_checks=True,
            unchanged_original_warning_signatures=signatures(native)==signatures(original_native),
            original_native_class_targets=class_audit)

    def account():
        report.update(observed_audit_wall_seconds=time.monotonic()-START,
                      observed_audit_full_cpu_seconds=time.process_time()+f.child_cpu()-CPU0)
        valid = report['status']=='completed' and remaining()>0
        for row in rows:
            shared = spec['shared_original_qualification_cost']
            row['charged_wall_seconds'] = row['paired_charged_wall_seconds'] + max(0,outer['wall_seconds']-summary['batch_wall_seconds']) + cap + 1 + shared['wall_seconds']
            row['charged_full_cpu_seconds'] = row['paired_charged_full_cpu_seconds'] + max(0,outer['full_cpu_seconds']-summary['batch_cpu_seconds']) + cap + 1 + shared['full_cpu_seconds']
            row['within_equal120_wall_full_cpu_caps'] = max(row['charged_wall_seconds'],row['charged_full_cpu_seconds']) <= 120
            row['accepted'] = valid and row['native_accepted'] and row['within_equal120_wall_full_cpu_caps']
        by_id = {row['id']:row for row in rows}
        report.update(results=rows, comparison_eligible=valid and all(by_id.get(k,{}).get('accepted') for k in ('B1','B2_portfolio','C_feedback')),
                      comparisons=paired.comparisons(rows) if valid else [])
        if remaining() <= 0:
            report.update(status='budget_exceeded', comparison_eligible=False, comparisons=[])

    previous = {sig:signal.signal(sig, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt())) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        with p.validation_readback_session():
            stable()
            assert spec['system']=='native-all' and spec['git_head']==protocol['freeze']['tools']['git_head']
            assert spec['tools']==protocol['freeze']['tools']
            assert spec['wall_budget_per_arm_seconds']==spec['full_cpu_budget_per_arm_seconds']==120
            assert spec['source_original_native_receipt_sha256']==report['original_receipt_sha256']
            assert spec['source_original_native_readback_sha256']==report['original_readback_sha256']
            assert original_readback['controls_passed'] and original_readback['source_exact'] and original_readback['original_constraints_and_all_routes_exact']
            assert original_record['original_hashes']==p.tree_hash(source_receipt.parent/'original')
            assert original_native==original_record['parity_native']
            assert {k:original_native[k] for k in spec['original_expected_native']}==spec['original_expected_native']
            assert outer['prospective_protocol_sha256']==p.sha(prospective)
            assert outer['process']['status']=='success' and outer['process']['exit_code']==0 and outer['process']['cleanup_complete']
            assert summary['status']=='completed' and protocol['arm_order']==['B0','B1','B2_portfolio','C_feedback']
            portfolio = f.read_json(base/'run/B2_portfolio/portfolio-summary.json')
            paired.verify_portfolio(base/'run/B2_portfolio',portfolio,board,protocol['freeze'])
            finals, trials = [], []
            for old in summary['results']:
                row = copy.deepcopy(old)
                row.update(native_accepted=old['accepted'], paired_charged_wall_seconds=old['charged_wall_seconds'],
                           paired_charged_full_cpu_seconds=old['charged_cpu_seconds'])
                if row['id']!='B2_portfolio' and row.get('result'):
                    path = Path(row['result']); data = f.read_json(path)
                    assert p.sha(path)==row['result_sha256']
                    assert data['tools']==protocol['freeze']['tools'] and data['source_hashes']==protocol['freeze']['source_hashes']
                    if data.get('accepted'):
                        p.check_result(path)
                    if data.get('candidate_sha256') and data.get('native_report_sha256'):
                        final = final_candidate(path.parent,data)
                        if data.get('accepted') and not final['unchanged_original_warning_signatures']:
                            raise p.Rejected('accepted final original warnings changed')
                        finals.append(dict(id=row['id'],status=data['status'],**final))
                rows.append(row)
            for trial in portfolio['trials']:
                if not trial.get('result'):continue
                path=Path(trial['result']);data=f.read_json(path)
                if data.get('candidate_sha256') and data.get('native_report_sha256'):
                    final=final_candidate(path.parent,data)
                    if trial.get('eligible') and not final['unchanged_original_warning_signatures']:
                        raise p.Rejected('eligible B2 original warnings changed')
                    finals.append(dict(id='B2/'+trial['id'],status=data['status'],**final))
            c_path=base/'run/C_feedback/result.json'
            if c_path.is_file():
                c=f.read_json(c_path)
                for trial in c.get('trials',[]):
                    folder=base/'run/C_feedback/trials'/trial['id'];data=f.read_json(folder/'result.json')
                    assert trial['receipt']==str(folder/'result.json')
                    assert all(trial[k]==data[k] for k in ('id','status','accepted'))
                    row=dict(id=data['id'],status=data['status'],accepted_by_strategy=data['accepted'])
                    if data.get('candidate_sha256') and data.get('native_report_sha256'):
                        row.update(final_candidate(folder,data))
                        if data['accepted'] and not row['unchanged_original_warning_signatures']:
                            raise p.Rejected('accepted C trial original warnings changed')
                    else:row['final_native_available']=False
                    trials.append(row)
            report.update(status='completed', final_candidates=finals, C_trial_candidates=trials,
                          strong_B2_selected=portfolio.get('selected'),
                          source_sha256=protocol['freeze']['source_hashes'],tools=protocol['freeze']['tools'])
    except (Exception,KeyboardInterrupt) as exc:
        report.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',
                      comparison_eligible=False,reason=type(exc).__name__+': '+str(exc))
    f.publish(output,report,stable,account,remaining,owned=lambda:h.owned_destination(owner))
    try:
        p.save_json(output/'execution.json',dict(wall_seconds=time.monotonic()-START,
            full_cpu_seconds=time.process_time()+f.child_cpu()-CPU0,fixed_charge_seconds=cap,
            result_sha256=p.sha(output/'result.json'),scope='Before imports through final publication; interpreter startup separately charged1second to each arm.'))
        stable()
        assert f.read_json(output/'execution.json')['result_sha256']==p.sha(output/'result.json')
        if remaining()<=0:raise p.Rejected('final publication exceeds prospective allowance')
    except (Exception,KeyboardInterrupt) as exc:
        report.update(status='invalidated',comparison_eligible=False,comparisons=[],reason=type(exc).__name__+': '+str(exc))
        f.publish(output,report,lambda: (_ for _ in ()).throw(p.Rejected(report['reason'])),account,remaining,owned=lambda:h.owned_destination(owner))
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('base','prospective','output','source-receipt','source-readback'):
        parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    result=qualify(args.base,args.prospective,args.output,args.source_receipt,args.source_readback)
    print(json.dumps({k:result.get(k) for k in ('status','comparison_eligible','reason','observed_audit_wall_seconds','observed_audit_full_cpu_seconds')}))
    return 0 if result['status']=='completed' else 2


if __name__=='__main__':raise SystemExit(main())
