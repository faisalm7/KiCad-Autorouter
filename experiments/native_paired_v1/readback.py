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
import math
import signal
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, placement_clearance as pc
from autorouter import handoff as h, sexpr as sx
from scripts import experiment_paired as paired, experiment_quality as q
CPU0 += f.child_cpu()


def native_class_readback(folder, data, candidate, protected):
    """Require the same explicit class-map gate as the production validator."""
    policy = p.netclass_policy(candidate)
    mapping = folder/'final-netclasses.json'
    if policy is None:
        if mapping.exists() or mapping.is_symlink():
            raise p.Rejected('unexpected class map for native Default-only task')
        return None, False
    classes = f.read_json(mapping)
    audit = p.audit_candidate_netclasses(candidate, protected, classes)
    from autorouter import config as c
    f.process_check(folder, data, 'final-netclasses', [str(c.PYTHON),
        str(c.ROOT/'autorouter/native.py'), 'netclasses', str(candidate), str(mapping)])
    return audit, True


def inherited_trial_accounting(folder, data, parent):
    """Bind strategy trial workers to their actually charged parent envelope."""
    p.check_resource_accounting(parent)
    references=[row for row in parent.get('trials',[]) if row.get('id')==data.get('id')]
    if (len(references)!=1 or references[0].get('receipt')!=str(folder/'result.json')
            or any(references[0].get(key)!=data.get(key) for key in ('id','status','accepted'))):
        raise p.Rejected('trial is not bound to its charged parent')
    steps=data.get('steps')
    if not isinstance(steps,list) or steps!=[step for step in parent['steps'] if step.get('phase')==data['id']]:
        raise p.Rejected('trial workers differ from charged parent history')
    def number(value):
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:
            raise p.Rejected('invalid inherited trial accounting')
        return value
    start=number(data.get('started_elapsed_seconds'));finish=number(data.get('finished_elapsed_seconds'))
    cpu=number(data.get('finished_observed_cpu_seconds'))
    if (finish<start or finish>parent['wall_seconds']+1e-6 or cpu>parent['total_cpu_seconds']+1e-6
            or sum(number(step.get('wall_seconds')) for step in steps)>finish-start+1e-6
            or sum(number(step.get('cpu_seconds'))+number(step.get('monitor_cpu_seconds')) for step in steps)>cpu+1e-6):
        raise p.Rejected('trial exceeds its charged parent envelope')


def final_candidate_readback(folder, data, board, original, source_hashes, *, resource_parent=None):
    candidate = folder/'candidate'/board.name
    p.verify_candidate_files(candidate, source_hashes, data['candidate_sha256'])
    tree = sx.read(candidate)
    if p.immutable(tree) != p.immutable(original):
        raise p.Rejected('final immutable design differs')
    protected = p.protected_for_record({'scope':'whole_board_unlocked_routing'}, original)
    if any(route not in p.routes(tree) for route in protected):
        raise p.Rejected('final protected copper differs')
    p.check_protected_import(folder,data,original,candidate,protected)
    p.check_pour_evidence(folder,data,original,candidate,correction=data.get('adapter') in ('planes','both'))
    p.check_native_edge_transport(folder,data)
    if resource_parent is None:p.check_resource_accounting(data)
    else:inherited_trial_accounting(folder,data,resource_parent)
    before = dict(source_hashes)
    before[board.name] = data['candidate_sha256']
    native = f.check_drc_stage(folder, data, 'final-drc', candidate,
        folder/'final-drc-input'/board.name, False, before,
        schematic_parity=True, sandboxed=False)
    if native != data['native'] or p.sha(folder/'final-drc.json') != data['native_report_sha256']:
        raise p.Rejected('final native report differs')
    class_audit, class_required = native_class_readback(folder,data,candidate,protected)
    return dict(path=str(candidate), candidate_sha256=data['candidate_sha256'],
        native_report_sha256=data['native_report_sha256'],
        native_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},
        native_rejection_reasons=p.native_rejection_reasons(native),
        original_design_checks=True, complete_schematic_native_checks=True,
        original_native_class_targets=class_audit,
        original_native_class_audit_required=class_required)


def source_evidence_contract(spec, record, review, receipt_pin, review_pin,
                             original_files, native_files):
    """Read either frozen source-evidence schema without inventing proof flags."""
    if spec['source_original_native_receipt_sha256'] != receipt_pin:
        raise p.Rejected('original receipt differs from prospective source pin')
    legacy = 'source_original_native_readback_sha256' in spec
    if legacy:
        files = spec.get('source_files', spec.get('source_five_files'))
        if not isinstance(files, dict) or not files:
            raise p.Rejected('complete original source inventory missing')
        expected = {name: meta['sha256'] for name, meta in files.items()}
        if (spec['source_original_native_readback_sha256'] != review_pin
                or any(review.get(key) is not True for key in
                    ('controls_passed', 'source_exact', 'original_constraints_and_all_routes_exact'))
                or expected != original_files or review['native'] != record['parity_native']):
            raise p.Rejected('legacy original readback differs from its frozen source evidence')
        return dict(schema='original-native-readback', source_files=expected,
                    native=review['native'], claims_limit=spec['limits'])

    # This independently reviewed source schema was frozen before the larger
    # CellScan run. Its reviewer observes an incomplete original, not acceptance.
    if (spec.get('kind') != 'prospective larger CellScan complete-schematic four-arm development experiment'
            or spec.get('source_original_native_review_sha256') != review_pin
            or any(key in spec for key in ('source_files', 'source_five_files'))
            or record.get('project') != 'cellscan'
            or record.get('kind') != 'original_hardware_native_diagnostic'
            or record.get('status') != 'observed'
            or review.get('kind') != 'CellScan original actual native diagnostic independent readback'
            or review.get('passed') is not True or review.get('failures') != []
            or review.get('new_native_execution') is not False
            or review.get('new_network_requests') != 0):
        raise p.Rejected('unsupported or unbound independent original review schema')
    checks = review['checks']
    required = ('exact_acquired_source_and_eight_input_files',
                'exact_original_shell_routes_and_protection',
                'actual_native_refill_full_schematic_and_all_workers',
                'exact_fifty_field_mismatch_descriptions_and_original_fields',
                'whole_costs_and_immutable_retained_evidence')
    if (any(key not in checks for key in required)
            or any(check.get('passed') is not True for check in checks.values())):
        raise p.Rejected('independent original review has missing or failed checks')
    source, design, stages, fields, costs = (checks[key] for key in required)
    expected_native = spec['original_source_sha256']
    root_native = {name.removeprefix('hardware/'): digest
                   for name, digest in original_files.items() if name.startswith('hardware/')}
    if (original_files != record['original_hashes']
            or source['copied_original_hashes'] != original_files
            or len(original_files) != 8 or source['native_input_files'] != 8
            or record['source_file_count'] != 8 or len(expected_native) != 6
            or source['native_input_bytes'] != record['source_bytes']
            or native_files != expected_native or root_native != expected_native
            or spec['freeze']['source_hashes'] != expected_native
            or source.get('source_unchanged') is not True
            or source['source_commit'] != record['source_commit']
            or record['source_commit'] != spec['source_revision']
            or any(record.get(key) is not True for key in ('original_preserved',
                'acquired_source_still_exact', 'original_shell_nonfill_ast_equal', 'all_original_route_records_exact'))
            or any(design.get(key) is not True for key in
                ('all_original_route_records_exact', 'immutable_original_design_and_companions_exact'))
            or design['candidate_sha256'] != record['final_candidate_sha256']
            or costs['native_receipt_sha256'] != receipt_pin
            or costs.get('all_retained_evidence_unchanged') is not True
            or costs['record_wall_seconds'] != record['wall_seconds']
            or costs['record_full_cpu_seconds'] != record['total_cpu_seconds']
            or spec['shared_original_qualification_cost']['wall_seconds'] != 25
            or spec['shared_original_qualification_cost']['full_cpu_seconds'] != 25
            or spec['final_readback_allowance_wall_full_cpu_seconds'] != 15
            or spec['bootstrap_publication_allowance_seconds_each_arm'] != 1):
        raise p.Rejected('independent original review source or immutable design differs')
    native = record['parity_native']
    if (stages.get('worker_count') != len(record['steps'])
            or stages.get('worker_count') != 4 or stages.get('drc_worker_count') != 2
            or stages.get('additional_field_netlist_and_audit_workers') != 2
            or stages.get('native_acceptance') != p.native_accepted(native)
            or stages['native_rejection_reasons'] != p.native_rejection_reasons(native)
            or fields['ignored_checks'] != native['ignored_checks']
            or fields.get('native_observation_not_normalized_or_waived') is not True):
        raise p.Rejected('independent original review native observations differ')
    return dict(schema='independent-original-review-cellscan-v1', source_files=original_files,
                native=native, claims_limit=[spec['coverage'], spec['initial_reference_feasibility'], spec['warnings']])


def original_review_native_readback(folder, record, review, board):
    """Check retained original workers and candidate with existing native helpers."""
    from experiments.original_project_native_v1.driver import completed_evidence, route_records
    witness = completed_evidence(folder)
    if hashlib.sha256(f.canonical(witness).encode()).hexdigest() != record['completed_evidence_sha256']:
        raise p.Rejected('independently reviewed original native evidence changed')
    source = folder/'original/hardware'/board.name
    candidate = Path(record['final_candidate'])
    if candidate != folder/'candidate'/board.name:
        raise p.Rejected('original candidate path differs')
    p.verify_candidate_files(candidate, p.tree_hash(source.parent), record['final_candidate_sha256'])
    original, tree = sx.read(source), sx.read(candidate)
    if p.immutable(original) != p.immutable(tree) or route_records(original) != route_records(tree):
        raise p.Rejected('reviewed original constraints or route records differ')
    design = review['checks']['exact_original_shell_routes_and_protection']
    if design['original_route_records'] != len(route_records(original)):
        raise p.Rejected('reviewed original route count differs')
    job = folder/'job'
    stages = review['checks']['actual_native_refill_full_schematic_and_all_workers']
    observed = []
    for name, native_board, saved, key in (
            ('original-refill', folder/'saved'/board.name, True, 'original_native'),
            ('original-final', candidate, False, 'parity_native')):
        binding = f.read_json(job/(name+'-binding.json'))
        native = f.check_drc_stage(job, record, name, native_board,
            native_board if saved else job/(name+'-input')/board.name,
            saved, binding['before'], schematic_parity=not saved)
        if native != record[key]:
            raise p.Rejected('reviewed original retained native report differs')
        observed.append(dict(name=name, report_sha256=p.sha(job/(name+'.json')),
            binding_sha256=p.sha(job/(name+'-binding.json')),
            native_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},
            full_schematic_parity_requested=not saved))
    if (observed != stages['native_drc_stages']
            or p.sha(job/'original-final.json') != record['final_native_report_sha256']):
        raise p.Rejected('reviewed original native stage pins differ')
    workers = []
    for step in record['steps']:
        f.process_check(job, record, step['name'], step['argv'], allowed=(0,5))
        workers.append({**{k:step[k] for k in ('name','status','exit_code','wall_seconds','cpu_seconds','cleanup_complete')},
            'process_sha256':p.sha(job/(step['name']+'-process.json')),
            'log_sha256':p.sha(Path(step['log']))})
    if workers != stages['workers'] or completed_evidence(folder) != witness:
        raise p.Rejected('reviewed original worker journals changed')
    for outer in review['checks']['whole_costs_and_immutable_retained_evidence']['outer_executions']:
        path = Path(outer['path'])
        if p.sha(path) != outer['sha256'] or f.read_json(path) != outer['record']:
            raise p.Rejected('reviewed original outer execution changed')


def pruning_incumbent_readback(folder, parent, board, original, source_hashes):
    """Retain native proof for the fresh incumbent even when pruning rejects it."""
    path = folder/'incumbent/result.json'
    data = f.read_json(path)
    marker = parent['incumbent']
    p.check_resource_accounting(parent)
    if (marker['receipt'] != str(path)
            or any(marker[key] != data[key] for key in ('status','accepted','metrics','wall_seconds'))
            or data['tools'] != parent['tools'] or data['source_hashes'] != source_hashes
            or data['source'] != str(board)
            or [dict(step,phase='incumbent') for step in data['steps']]
                != [step for step in parent['steps'] if step.get('phase')=='incumbent']
            or data['wall_seconds'] > parent['wall_seconds']+1e-6
            or data['total_cpu_seconds'] > parent['total_cpu_seconds']+1e-6):
        raise p.Rejected('fresh pruning incumbent differs from charged parent')
    p.check_engine_profile_record(data, path.parent)
    return data, final_candidate_readback(path.parent,data,board,original,source_hashes)


def qualify(base, prospective, output, source_receipt, source_readback, *, completion_prospective=None):
    base, prospective, output = map(lambda x: Path(x).resolve(), (base, prospective, output))
    source_receipt, source_readback = map(lambda x: Path(x).resolve(), (source_receipt, source_readback))
    output.mkdir()
    owner = {}
    h.capture_destination(owner, output)
    spec = f.read_json(prospective)
    completion_path = Path(completion_prospective).resolve() if completion_prospective else None
    completion = f.read_json(completion_path) if completion_path else None
    direct = completion_path.with_name(completion_path.name.removesuffix('-protocol.json')) if completion else None
    direct_witness = pc.inventory(direct,max_bytes=64*1024**2,max_files=6000,max_entries=12000,with_directories=True) if direct else None
    completion_pin = p.sha(completion_path) if completion else None
    high_outer = f.read_json(direct/'execution.json') if direct else None
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
    original_native = original_record['parity_native']
    source_contract = None
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
                  claims_limit=spec.get('limits', []),
                  stock_scope='raw stock DSN with the same class-target safety settings; not untouched Freerouting defaults')
    if completion:
        report.update(completion_prospective_sha256=completion_pin,
                      cumulative_audit_closure_required=True,
                      cumulative_audit_closure_passed=False)

    def remaining():
        return min(cap-(time.monotonic()-START), cap-(time.process_time()+f.child_cpu()-CPU0))

    def stable():
        h.owned_destination(owner)
        q.verify_freeze(protocol['freeze'], board)
        if completion:
            q.verify_freeze(completion['freeze'],board)
            if p.sha(completion_path)!=completion_pin or pc.inventory(direct,max_bytes=64*1024**2,max_files=6000,max_entries=12000,with_directories=True)!=direct_witness:
                raise p.Rejected('direct completion evidence changed')
            for name,pin in completion['artifacts'].items():
                if p.sha(Path(name))!=pin:raise p.Rejected('completed prefix pin changed')
        if pc.inventory(base, max_bytes=96*1024**2, max_files=6000,
                        max_entries=12000, with_directories=True) != witness:
            raise p.Rejected('completed comparison changed during readback')
        for path, key in ((prospective,'prospective_protocol_sha256'),
                          (source_receipt,'original_receipt_sha256'),
                          (source_readback,'original_readback_sha256')):
            if p.sha(path) != report[key]:
                raise p.Rejected('prospective or original evidence changed')
        contract = source_evidence_contract(spec, original_record, original_readback,
            report['original_receipt_sha256'], report['original_readback_sha256'],
            p.tree_hash(source_receipt.parent/'original'), p.tree_hash(board.parent))
        if source_contract is not None and contract != source_contract:
            raise p.Rejected('original source evidence changed during readback')
        if report['comparison_eligible'] and remaining() <= 0:
            raise p.Rejected('complete readback exceeds its prospective allowance')

    def final_candidate(folder, data, *, resource_parent=None):
        result = final_candidate_readback(folder,data,board,original,protocol['freeze']['source_hashes'],resource_parent=resource_parent)
        result['unchanged_original_warning_signatures'] = signatures(data['native'])==signatures(original_native)
        return result

    def account():
        report.update(observed_audit_wall_seconds=time.monotonic()-START,
                      observed_audit_full_cpu_seconds=time.process_time()+f.child_cpu()-CPU0)
        valid = report['status']=='completed' and remaining()>0
        for row in rows:
            shared = spec['shared_original_qualification_cost']
            row['charged_wall_seconds'] = row['paired_charged_wall_seconds'] + max(0,outer['wall_seconds']-summary['batch_wall_seconds']) + cap + 1 + shared['wall_seconds']
            row['charged_full_cpu_seconds'] = row['paired_charged_full_cpu_seconds'] + max(0,outer['full_cpu_seconds']-summary['batch_cpu_seconds']) + cap + 1 + shared['full_cpu_seconds']
            if completion:
                row['charged_wall_seconds'] += completion['additional_shared_original_qualification_seconds']
                row['charged_full_cpu_seconds'] += completion['additional_shared_original_qualification_seconds']
                if row['id']=='B2_portfolio':
                    row['charged_wall_seconds'] += high_outer['whole_new_wall_seconds']+1
                    row['charged_full_cpu_seconds'] += high_outer['whole_new_full_cpu_seconds']+1
            row['within_equal120_wall_full_cpu_caps'] = max(row['charged_wall_seconds'],row['charged_full_cpu_seconds']) <= 120
            row['accepted'] = valid and row['native_accepted'] and row['within_equal120_wall_full_cpu_caps']
        by_id = {row['id']:row for row in rows}
        report.update(results=rows, comparison_eligible=valid and not completion and all(by_id.get(k,{}).get('accepted') for k in ('B1','B2_portfolio','C_feedback')),
                      comparisons=paired.comparisons(rows) if valid else [])
        if remaining() <= 0:
            report.update(status='budget_exceeded', comparison_eligible=False, comparisons=[])

    previous = {sig:signal.signal(sig, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt())) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        with p.validation_readback_session():
            stable()
            source_contract = source_evidence_contract(spec, original_record, original_readback,
                report['original_receipt_sha256'], report['original_readback_sha256'],
                p.tree_hash(source_receipt.parent/'original'), p.tree_hash(board.parent))
            report.update(source_evidence_schema=source_contract['schema'],
                          claims_limit=source_contract['claims_limit'])
            if source_contract['schema']=='independent-original-review-cellscan-v1':
                original_review_native_readback(source_receipt.parent,original_record,original_readback,board)
            assert spec['system']=='native-all' and spec['git_head']==protocol['freeze']['tools']['git_head']
            assert spec['tools']==protocol['freeze']['tools']
            assert spec.get('external_reserve_seconds',0)==protocol.get('external_reserve_seconds',0)
            assert spec['wall_budget_per_arm_seconds']==spec['full_cpu_budget_per_arm_seconds']==120
            assert spec['source_original_native_receipt_sha256']==report['original_receipt_sha256']
            assert original_record['original_hashes']==p.tree_hash(source_receipt.parent/'original')
            assert original_native==source_contract['native']
            assert {k:original_native[k] for k in spec['original_expected_native']}==spec['original_expected_native']
            assert outer['prospective_protocol_sha256']==p.sha(prospective)
            assert outer['process']['status']=='success' and outer['process']['exit_code']==0 and outer['process']['cleanup_complete']
            assert summary['status']=='completed' and protocol['arm_order']==['B0','B1','B2_portfolio','C_feedback']
            portfolio = f.read_json(base/'run/B2_portfolio/portfolio-summary.json')
            paired.verify_portfolio(base/'run/B2_portfolio',portfolio,board,protocol['freeze'])
            if completion:
                from scripts import experiment_portfolio as portfolio_module
                if (completion['freeze']!=portfolio_module.freeze(board)
                        or completion['source']!=str(board) or completion['variant']!='via_high'
                        or completion['earlier_variants']!=['via_default','via_low']
                        or [row['id'] for row in portfolio['trials']]!=completion['earlier_variants']
                        or portfolio['stop_reason']!='insufficient remaining budget for another attempt and reserves'
                        or completion['outer_wall_full_cpu_cap_seconds']!=120
                        or completion['new_final_readback_allowance_wall_full_cpu_seconds']!=cap
                        or completion['additional_shared_original_qualification_seconds']!=3
                        or completion['shared_original_qualification_total_seconds']!=18
                        or high_outer['protocol_sha256']!=completion_pin
                        or high_outer['process']['status']!='success' or high_outer['process']['exit_code'] not in (0,2)
                        or high_outer['process']['cleanup_complete'] is not True
                        or high_outer['already_committed_charge']!=completion['already_committed_charge']):
                    raise p.Rejected('direct High differs from unchanged completed prefix')
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
                if c.get('incumbent'):
                    data, final = pruning_incumbent_readback(c_path.parent,c,board,original,protocol['freeze']['source_hashes'])
                    final['unchanged_original_warning_signatures'] = signatures(data['native'])==signatures(original_native)
                    finals.append(dict(id='C/incumbent',status=data['status'],**final))
                for trial in c.get('trials',[]):
                    folder=base/'run/C_feedback/trials'/trial['id'];data=f.read_json(folder/'result.json')
                    assert trial['receipt']==str(folder/'result.json')
                    assert all(trial[k]==data[k] for k in ('id','status','accepted'))
                    inherited_trial_accounting(folder,data,c)
                    row=dict(id=data['id'],status=data['status'],accepted_by_strategy=data['accepted'])
                    if data.get('candidate_sha256') and data.get('native_report_sha256'):
                        row.update(final_candidate(folder,data,resource_parent=c))
                        if data['accepted'] and not row['unchanged_original_warning_signatures']:
                            raise p.Rejected('accepted C trial original warnings changed')
                    else:row['final_native_available']=False
                    trials.append(row)
            if completion:
                high_path=direct/'trial/result.json';high=f.read_json(high_path)
                highrow=dict(index=2,id='via_high',assigned_seconds=completion['assigned_inner_seconds'],guidance_policy=None,
                    result=str(high_path),result_sha256=p.sha(high_path),candidate=high['candidate'],candidate_sha256=high['candidate_sha256'],
                    native_report_sha256=high['native_report_sha256'],vias=high['metrics']['vias'],length_mm=high['metrics']['track_length_mm'],
                    eligible=high.get('accepted') is True,status=high['status'],native=high['native'])
                if highrow['eligible']:portfolio_module.verify_row(highrow,board,completion['freeze'])
                elif high['status']!='drc_rejected' or not p.native_rejection_reasons(high['native']):
                    raise p.Rejected('unqualified direct High terminal state')
                final=final_candidate(direct/'trial',high)
                if highrow['eligible'] and not final['unchanged_original_warning_signatures']:
                    raise p.Rejected('direct High changed original warnings')
                finals.append(dict(id='B2/via_high',status=high['status'],**final))
                all_trials=copy.deepcopy(portfolio['trials'])+[highrow]
                chosen=min((row for row in all_trials if row['eligible']),key=portfolio_module.rank)
                b2=next(row for row in rows if row['id']=='B2_portfolio')
                inherited={'wall_seconds':b2['paired_charged_wall_seconds']+max(0,outer['wall_seconds']-summary['batch_wall_seconds'])+cap+1+spec['shared_original_qualification_cost']['wall_seconds']+3+1,
                    'full_cpu_seconds':b2['paired_charged_full_cpu_seconds']+max(0,outer['full_cpu_seconds']-summary['batch_cpu_seconds'])+cap+1+spec['shared_original_qualification_cost']['full_cpu_seconds']+3+1}
                if (inherited!=completion['already_committed_charge']
                        or completion['inherited_remaining_wall_seconds']!=120-inherited['wall_seconds']
                        or completion['inherited_remaining_full_cpu_seconds']!=120-inherited['full_cpu_seconds']
                        or any(not q.finite_nonnegative(high_outer[key]) for key in ('whole_new_wall_seconds','whole_new_full_cpu_seconds'))
                        or high_outer['combined_charged_wall_seconds']!=inherited['wall_seconds']+high_outer['whole_new_wall_seconds']
                        or high_outer['combined_charged_full_cpu_seconds']!=inherited['full_cpu_seconds']+high_outer['whole_new_full_cpu_seconds']):
                    raise p.Rejected('direct High inherited costs differ')
                b2.update(trials=all_trials,selected=chosen,pareto_frontier=portfolio_module.frontier(all_trials),
                    selected_receipt_is_trial_only=True,aggregate_cost_index=str(output/'result.json'))
                b2.update({key:chosen[key] for key in ('result','result_sha256','candidate_sha256','native_report_sha256','vias','length_mm')})
                report.update(strong_B2_variants=list(portfolio_module.VARIANTS),direct_high_execution_sha256=p.sha(direct/'execution.json'),
                    additional_shared_source_wall_full_cpu_charge_seconds=3,shared_source_total_wall_full_cpu_charge_seconds=18,
                    audit_policy='Original15 allowance retained once. All failed/successful readbacks, probe, independent audits and bootstrap/emission costs must close cumulatively before comparison eligibility.',
                    calendar_gap='Costs are cumulative active wall; original completed candidates and trials were not rerouted.')
            report.update(status='completed', final_candidates=finals, C_trial_candidates=trials,
                          strong_B2_selected=b2['selected'] if completion else portfolio.get('selected'),
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


def qualify_continuation(prior_qualification, continuation, direct, prospective, output):
    """Add only an unattempted trial; preserve original and prefix charges.

    Shares the native-stage/portfolio/publication checks with the four-arm
    readback above. No solver or native process runs during this readback.
    """
    from scripts import experiment_portfolio as portfolio
    prior_qualification, continuation, direct, prospective, output = map(
        lambda x:Path(x).resolve(), (prior_qualification,continuation,direct,prospective,output))
    output.mkdir(); owner={}; h.capture_destination(owner,output)
    spec=f.read_json(prospective); cap=spec['new_final_readback_allowance_wall_full_cpu_seconds']
    if cap!=15 or spec['outer_wall_full_cpu_cap_seconds']!=120:
        raise p.Rejected('unsupported continuation charge')
    prior=f.read_json(prior_qualification); prefix=f.read_json(continuation/'portfolio/portfolio-summary.json')
    protocol=f.read_json(continuation/'portfolio/protocol.json')
    outer=f.read_json(continuation/'execution.json'); high_outer=f.read_json(direct/'execution.json')
    board=Path(spec['source']); original=p.preflight(board); rows=[]
    roots=(continuation,direct,Path(protocol['resume']['plan']['old_directory']).parent.parent)
    inventories={str(x):pc.inventory(x,max_bytes=96*1024**2,max_files=6000,max_entries=12000,with_directories=True) for x in roots}
    pins={**spec['artifacts'],str(prospective):p.sha(prospective)}
    report=dict(schema=1,kind='native-all-additive-completed-prefix-readback-v1',status='incomplete',accepted=False,
        comparison_eligible=False,new_native_execution=False,default_trial_repeated=False,
        physical_electrical_validation=False,controller_sha256=p.sha(Path(__file__)),
        prospective_protocol_sha256=p.sha(prospective),audit_wall_and_full_cpu_charge_seconds=cap,
        old_qualification_sha256=p.sha(prior_qualification),claims_limit=spec['limits'],
        metadata_correction='Earlier100 wrapper new_native_variants describes intended low/high; actual bound prefix contains only default+low. High ran once in separate deadline-bounded invocation. Earlier receipt unchanged.',
        bootstrap_publication_scope='Wrapper samples exclude interpreter imports and final small receipt write; two1second startup/publication allowances are explicit conservative charges, not measured durations. Preparation/research is outside normal routing cost.',
        calendar_gap='Cumulative active wall includes all original and two new invocations; not uninterrupted120 elapsed calendar seconds.')
    def remaining():return min(cap-(time.monotonic()-START),cap-(time.process_time()+f.child_cpu()-CPU0))
    def stable():
        h.owned_destination(owner);q.verify_freeze(spec['freeze'],board)
        portfolio.verify_resume_basis(protocol['resume'])
        for name,pin in pins.items():
            if p.sha(Path(name))!=pin:raise p.Rejected('continuation input pin changed')
        for root in roots:
            if pc.inventory(root,max_bytes=96*1024**2,max_files=6000,max_entries=12000,with_directories=True)!=inventories[str(root)]:
                raise p.Rejected('completed native evidence changed during additive readback')
        if report['comparison_eligible'] and remaining()<=0:raise p.Rejected('additive audit exceeds allowance')
    def account():
        report.update(observed_audit_wall_seconds=time.monotonic()-START,
            observed_audit_full_cpu_seconds=time.process_time()+f.child_cpu()-CPU0)
        valid=report['status']=='completed' and remaining()>0
        for row in rows:
            row['within_equal120_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_full_cpu_seconds'])<=120
            row['accepted']=valid and row['native_accepted'] and row['within_equal120_wall_full_cpu_caps']
        by_id={row['id']:row for row in rows}
        report.update(results=rows,comparison_eligible=valid and all(by_id.get(k,{}).get('accepted') for k in ('B1','B2_portfolio','C_feedback')),
            comparisons=paired.comparisons(rows) if valid else [])
        if remaining()<=0:report.update(status='budget_exceeded',comparison_eligible=False,comparisons=[])
    previous={sig:signal.signal(sig,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt())) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        with p.validation_readback_session():
            stable()
            assert prior['status']=='completed' and prior['comparison_eligible']
            assert prefix['status']=='completed' and prefix['comparison_eligible'] and prefix['protocol_sha256']==p.sha(continuation/'portfolio/protocol.json')
            assert [row['id'] for row in prefix['trials']]==['via_default','via_low']
            assert prefix['stop_reason']=='insufficient remaining budget for another attempt and reserves'
            portfolio.compatible_resume_freeze(protocol['freeze'],spec['freeze'])
            for invocation in (outer,high_outer):
                process=invocation['process']
                assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']
            assert outer['within_enclosing_budget'] and high_outer['within_full120_caps']
            assert outer['combined_active_wall_seconds']==protocol['resume']['prior_wall_seconds']+outer['whole_new_wall_seconds']
            assert outer['combined_full_cpu_seconds']==protocol['resume']['prior_cpu_seconds']+outer['whole_new_full_cpu_seconds']
            assert high_outer['protocol_sha256']==p.sha(prospective)
            high=f.read_json(direct/'trial/result.json'); metrics=high['metrics']
            highrow=dict(index=2,id='via_high',assigned_seconds=spec['assigned_inner_seconds'],guidance_policy=None,
                result=str(direct/'trial/result.json'),result_sha256=p.sha(direct/'trial/result.json'),
                candidate=high['candidate'],candidate_sha256=high['candidate_sha256'],native_report_sha256=high['native_report_sha256'],
                vias=metrics['vias'],length_mm=metrics['track_length_mm'],eligible=high.get('accepted') is True,
                status=high['status'],native=high['native'])
            trials=copy.deepcopy(prefix['trials'])+[highrow]; finals=[]
            for row in trials:
                path=Path(row['result']);data=f.read_json(path)
                assert p.sha(path)==row['result_sha256']
                if row['eligible']:
                    portfolio.verify_row(row,board,spec['freeze'] if row['id']=='via_high' else portfolio.trial_freeze(protocol,row))
                else:
                    assert data['accepted'] is False and data['status']=='drc_rejected' and p.native_rejection_reasons(data['native'])
                finals.append(dict(id='B2/'+row['id'],status=data['status'],**final_candidate_readback(path.parent,data,board,original,spec['freeze']['source_hashes'])))
            eligible=[row for row in trials if row['eligible']];chosen=min(eligible,key=portfolio.rank)
            for old in prior['results']:
                row=copy.deepcopy(old)
                row['native_accepted']=old['native_accepted']
                if row['id']=='B2_portfolio':
                    for key,cost in (('charged_wall_seconds','whole_new_wall_seconds'),('charged_full_cpu_seconds','whole_new_full_cpu_seconds')):
                        row[key]=old[key]+outer[cost]+2.+cap+high_outer[cost]
                        assert spec['already_committed_charge']['wall_seconds' if key=='charged_wall_seconds' else 'full_cpu_seconds']==old[key]+outer[cost]+2.+cap
                    row.update(trials=trials,selected={k:chosen[k] for k in ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm')},pareto_frontier=portfolio.frontier(trials),native_accepted=True,
                        selected_receipt_is_trial_only=True,aggregate_cost_index=str(output/'result.json'))
                    row.update({key:chosen[key] for key in ('result','result_sha256','candidate_sha256','native_report_sha256','vias','length_mm')})
                else:
                    path=Path(row['result']);data=f.read_json(path);assert p.sha(path)==row['result_sha256']
                    if row['native_accepted']:p.check_result(path)
                    finals.append(dict(id=row['id'],status=data['status'],**final_candidate_readback(path.parent,data,board,original,spec['freeze']['source_hashes'])))
                    row['charged_wall_seconds']=old['charged_wall_seconds']+cap
                    row['charged_full_cpu_seconds']=old['charged_full_cpu_seconds']+cap
                rows.append(row)
            warning_signatures=[f.canonical([x for x in f.read_json(Path(row['result']))['native']['findings'] if x['severity']=='warning']) for row in (chosen,rows[1],rows[3])]
            assert len(set(warning_signatures))==1
            report.update(status='completed',final_candidates=finals,actual_tuned_variants=list(portfolio.VARIANTS),
                strong_B2_selected=chosen['id'],selected_B2_length_mm=chosen['length_mm'],C_length_mm=rows[3]['length_mm'],
                C_gain_vs_B2_mm=chosen['length_mm']-rows[3]['length_mm'],unchanged_original_warning_signatures=True,
                high_deadline_seconds=spec['inherited_remaining_wall_seconds'],high_nominal_inner_seconds=spec['assigned_inner_seconds'])
    except (Exception,KeyboardInterrupt) as exc:
        report.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',comparison_eligible=False,reason=type(exc).__name__+': '+str(exc))
    f.publish(output,report,stable,account,remaining,owned=lambda:h.owned_destination(owner))
    try:
        p.save_json(output/'execution.json',dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=time.process_time()+f.child_cpu()-CPU0,
            fixed_charge_seconds=cap,result_sha256=p.sha(output/'result.json'),scope='Module start before imports through publication; final independent review/emission must also fit combined15 allowance.'))
        stable();assert f.read_json(output/'execution.json')['result_sha256']==p.sha(output/'result.json')
        if remaining()<=0:raise p.Rejected('additive publication exceeds allowance')
    except (Exception,KeyboardInterrupt) as exc:
        report.update(status='invalidated',comparison_eligible=False,comparisons=[],reason=type(exc).__name__+': '+str(exc))
        f.publish(output,report,lambda:(_ for _ in ()).throw(p.Rejected(report['reason'])),account,remaining,owned=lambda:h.owned_destination(owner))
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('base','prospective','output','source-receipt','source-readback'):
        parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--completion-prospective',type=Path)
    args=parser.parse_args()
    result=qualify(args.base,args.prospective,args.output,args.source_receipt,args.source_readback,completion_prospective=args.completion_prospective)
    print(json.dumps({k:result.get(k) for k in ('status','comparison_eligible','reason','observed_audit_wall_seconds','observed_audit_full_cpu_seconds')}))
    return 0 if result['status']=='completed' else 2


if __name__=='__main__':raise SystemExit(main())
