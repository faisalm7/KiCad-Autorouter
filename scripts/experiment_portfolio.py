#!/usr/bin/env python3
"""Fixed, sequential development B2 portfolio with one shared wall/CPU budget.

No routing job may run alongside this experiment. The output indexes retained
native-validated trial receipts; it is not itself a pipeline routing receipt.
No reference route is used for parameter selection, ranking, or scoring.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import config as c, pipeline as p, floor_route as f, placement_clearance as pc
from scripts import experiment_quality as q

BUDGET = 120.0
MAX_OPERATIONAL_BUDGET = 900.0
FINAL_RESERVE = 15.0
VARIANTS = ('via_default', 'via_low', 'via_high')
SCRIPT = Path(__file__).resolve()
RESUME_POLICY = 'single-default-strict-targets-resume-v1'
COMPLETED_PREFIX_POLICY = 'completed-default-prefix-resume-v1'
COMPLETED_PREFIX_PROJECTS = ('arcdice',)
COMPLETED_PREFIX_BUDGET = 100.0
RESUME_SCRIPT = 'scripts/experiment_portfolio.py'


def rank(row):
    return row['vias'], row['length_mm'], row['index']


def valid_metrics(metrics):
    return (type(metrics.get('vias')) is int and metrics['vias'] >= 0
            and q.finite_nonnegative(metrics.get('track_length_mm')))


def frontier(rows):
    eligible = [row for row in rows if row.get('eligible') is True]
    return [row['id'] for row in eligible if not any(
        other['vias'] <= row['vias'] and other['length_mm'] <= row['length_mm']
        and (other['vias'] < row['vias'] or other['length_mm'] < row['length_mm'])
        for other in eligible)]


def freeze(board):
    frozen = q.freeze(board)
    relative = str(SCRIPT.relative_to(c.ROOT))
    digest = p.sha(SCRIPT)
    committed = subprocess.run(['git', 'show', frozen['tools']['git_head'] + ':' + relative],
                               cwd=c.ROOT, capture_output=True, check=True).stdout
    if hashlib.sha256(committed).hexdigest() != digest:
        raise p.Rejected('commit exact portfolio script before running')
    frozen['files_sha256'][relative] = digest
    return frozen


def verify_row(row, board, frozen):
    """Consistency check before ranking and again at final selection.

    p.check_result checks immutable/native evidence. This additional check binds
    the retained receipt, metrics, and profile to the predeclared experiment.
    Neither function authenticates mutable JSON.
    """
    if not q.finite_nonnegative(row.get('assigned_seconds')) or not 0 < row['assigned_seconds'] <= MAX_OPERATIONAL_BUDGET:
        raise p.Rejected('invalid bounded assigned trial allowance')
    allocation_keys={'allocation','remaining_wall_full_cpu_seconds_at_assignment','unattempted_variants_at_assignment'}
    if allocation_keys & row.keys():
        if (not allocation_keys<=row.keys() or row['allocation'] not in ('remaining','balanced')
                or not q.finite_nonnegative(row['remaining_wall_full_cpu_seconds_at_assignment'])
                or type(row['unattempted_variants_at_assignment']) is not int
                or row['unattempted_variants_at_assignment']!=len(VARIANTS)-row['index']
                or not 1<=row['unattempted_variants_at_assignment']<=len(VARIANTS)
                or row['assigned_seconds']!=(row['remaining_wall_full_cpu_seconds_at_assignment']-FINAL_RESERVE)/(row['unattempted_variants_at_assignment'] if row['allocation']=='balanced' else 1)):
            raise p.Rejected('trial differs from its recorded allocation')
    receipt = Path(row['result'])
    if receipt.is_symlink() or p.sha(receipt) != row['result_sha256']:
        raise p.Rejected('trial receipt changed')
    data = json.loads(receipt.read_text())
    if (data.get('source') != str(board) or data.get('source_hashes') != frozen['source_hashes']
            or data.get('tools') != frozen['tools'] or data.get('engine_profile') != 'tuned'
            or data.get('adapter') != 'both' or data.get('scoring_variant') != row['id']
            or (row.get('guidance_policy')=='placement-search-v1' and (data.get('schema')!=4 or data.get('input_policy')!='placement-search-v1'))
            or (row.get('guidance_policy') is None and data.get('input_policy') is not None)
            or data.get('scope') != 'whole_board_unlocked_routing'
            or data.get('budget_seconds') != row['assigned_seconds']
            or data.get('cpu_budget_seconds') != row['assigned_seconds']):
        raise p.Rejected('trial differs from frozen portfolio contract')
    engine = data.get('engine_budget', {})
    width_guard=p.check_minimum_width_record(data,receipt.parent)
    expected = p.engine_profile_settings('tuned', engine.get('remaining_outer_wall_seconds_at_assignment'),
        strict_class_targets=data.get('netclass_policy') is not None or row.get('guidance_policy')=='placement-search-v1' or width_guard is not None, scoring_variant=row['id'])
    if (any(engine.get(key) != value for key, value in expected.items())
            or engine.get('outer_task_wall_budget_seconds') != row['assigned_seconds']
            or engine.get('outer_task_cpu_budget_seconds') != row['assigned_seconds']):
        raise p.Rejected('trial engine profile differs from declared variant')
    engine_steps = [step for step in data.get('steps', []) if step.get('name') == 'engine']
    if len(engine_steps) != 1:
        raise p.Rejected('missing unique engine step')
    engine_step = engine_steps[0]
    if ([arg for arg in engine_step.get('argv', []) if arg.startswith('--router.')] != expected['argv']
            or engine_step.get('status') != 'success' or engine_step.get('exit_code') != 0
            or engine_step.get('cleanup_complete') is not True):
        raise p.Rejected('engine execution arguments differ from declared variant')
    process = receipt.parent/'engine-process.json'
    if process.is_symlink() or json.loads(process.read_text()) != engine_step:
        raise p.Rejected('engine step differs from retained process')
    verified = p.check_result(receipt)
    metrics = data.get('metrics', {})
    if not valid_metrics(metrics):
        raise p.Rejected('invalid native trial metrics')
    if (metrics['vias'] != row['vias'] or metrics['track_length_mm'] != row['length_mm']
            or verified['candidate'] != row['candidate']
            or verified['candidate_sha256'] != row['candidate_sha256']
            or data.get('native_report_sha256') != row['native_report_sha256']):
        raise p.Rejected('trial summary differs from bound evidence')
    if p.sha(receipt) != row['result_sha256']:
        raise p.Rejected('trial receipt changed while checking')
    return verified


def _resume_path(value):
    path=Path(value)
    if (not path.is_absolute() or '..' in path.parts or c.ROOT/'.runs' not in path.parents
            or any(x.is_symlink() for x in (path,*path.parents))):
        raise p.Rejected('resume artifacts must be exact non-symlink local run paths')
    return path


def compatible_resume_freeze(old,current):
    """Only HEAD and this checker script may differ; no native/source waiver."""
    if set(old)!=set(current) or set(old)!={'tools','source_hashes','files_sha256'}:
        raise p.Rejected('resume freeze schema differs')
    a,b=copy.deepcopy(old),copy.deepcopy(current)
    if (RESUME_SCRIPT not in a['files_sha256'] or RESUME_SCRIPT not in b['files_sha256']
            or 'git_head' not in a['tools'] or 'git_head' not in b['tools']):
        raise p.Rejected('resume exception witness absent')
    for row in (a,b):
        row['tools'].pop('git_head');row['files_sha256'].pop(RESUME_SCRIPT)
    if a!=b:raise p.Rejected('resume source/tools/core/protocol changed')


def resume_basis(path,pin,board,current,budget,project_name,guidance_policy):
    """Read a prospectively pinned, single completed-default failure prefix."""
    if not q.finite_nonnegative(budget) or not 60<=budget<=BUDGET:
        raise p.Rejected('resume remains within its legacy120 planning budget')
    path=_resume_path(path);raw=pc.read_bytes(path,32*1024*1024)
    if hashlib.sha256(raw).hexdigest()!=pin:raise p.Rejected('resume plan pin differs')
    plan=json.loads(raw);directory=_resume_path(plan['old_directory']);base=directory.parent
    completed=plan.get('policy')==COMPLETED_PREFIX_POLICY
    old_budget=plan.get('old_budget_seconds') if completed else budget
    if completed and (project_name not in COMPLETED_PREFIX_PROJECTS or budget!=COMPLETED_PREFIX_BUDGET
            or not q.finite_nonnegative(old_budget) or not 60<=old_budget<budget
            or plan.get('new_budget_seconds')!=budget or plan.get('outer_arm_budget_seconds')!=BUDGET
            or plan.get('full_arm_charge_required') is not True):
        raise p.Rejected('unsupported completed-prefix allocation/outer-charge contract')
    paths={str(base/name) for name in ('paired-summary.json','protocol.json','B2_portfolio-invocation.json')}
    paths|={str(directory/name) for name in ('portfolio-summary.json','protocol.json')}
    if (plan.get('schema')!=(2 if completed else 1)
            or (not completed and (plan.get('policy')!=RESUME_POLICY or project_name!='nus-usb-led'))
            or plan.get('project')!=project_name or guidance_policy is not None or plan.get('guidance_policy') is not None
            or plan.get('source')!=str(board) or plan.get('budget_seconds')!=budget
            or plan.get('retained_variants')!=['via_default'] or plan.get('continue_variants')!=['via_low','via_high']
            or plan.get('allowed_compatibility_changes')!=['tools.git_head','files_sha256/'+RESUME_SCRIPT]
            or set(plan.get('artifacts',{}))!=paths):
        raise p.Rejected('unsupported narrow resume contract')
    for name,digest in plan['artifacts'].items():
        if p.sha(_resume_path(name))!=digest:raise p.Rejected('retained resume artifact changed')
    old=json.loads((directory/'portfolio-summary.json').read_text());protocol=json.loads((directory/'protocol.json').read_text())
    pair=json.loads((base/'paired-summary.json').read_text());paired_protocol=json.loads((base/'protocol.json').read_text())
    invoice=json.loads((base/'B2_portfolio-invocation.json').read_text())
    rows=[r for r in pair['results'] if r.get('id')=='B2_portfolio']
    if len(rows)!=1:raise p.Rejected('unique paired cost witness required')
    charged=rows[0];prior=(plan['prior_invocation_wall_seconds'],plan['prior_invocation_cpu_seconds'])
    if (any(not q.finite_nonnegative(x) or x>old_budget for x in prior)
            or tuple(charged.get(k) for k in ('invocation_wall_seconds','invocation_cpu_seconds'))!=prior
            or tuple(invoice.get(k) for k in ('invocation_wall_seconds','invocation_cpu_seconds'))!=prior
            or charged.get('assigned_seconds')!=old_budget or charged.get('result')!=str(directory/'portfolio-summary.json')
            or charged.get('result_sha256')!=plan['artifacts'][str(directory/'portfolio-summary.json')]
            or paired_protocol.get('inner_allowance_seconds')!=old_budget):
        raise p.Rejected('resume must charge complete measured paired invocation')
    prefix_valid=(old.get('status')=='completed' and old.get('comparison_eligible') is True
        and old.get('stop_reason')=='insufficient remaining budget for another attempt and reserves'
        and isinstance(old.get('selected'),dict) and old['selected'].get('id')=='via_default') if completed else (
        old.get('status')=='invalidated' and old.get('comparison_eligible') is False and old.get('selected') is None
        and old.get('reason')=='Rejected: trial engine profile differs from declared variant')
    if (not prefix_valid
            or old.get('source')!=str(board) or old.get('guidance_policy') is not None
            or old.get('protocol_sha256')!=plan['artifacts'][str(directory/'protocol.json')]
            or any(old.get(k)!=old_budget or protocol.get(k)!=old_budget for k in ('wall_budget_seconds','cpu_budget_seconds'))
            or protocol.get('variants')!=list(VARIANTS) or protocol.get('fixed_order') is not True
            or protocol.get('allocation','remaining')!='remaining' or old.get('allocation','remaining')!='remaining'
            or protocol.get('guidance_policy') is not None or protocol.get('source')!=str(board)
            or protocol.get('scoring')!={name:p.engine_scoring_settings(name) for name in VARIANTS}
            or protocol.get('root_finalization_reserve_seconds')!=FINAL_RESERVE
            or len(old.get('trials',[]))!=1):
        raise p.Rejected('only the exact interrupted default portfolio may resume')
    row=copy.deepcopy(old['trials'][0]);trial=directory/'01-via_default/result.json'
    if (row.get('index')!=0 or row.get('id')!='via_default' or row.get('eligible') is not (True if completed else False)
            or row.get('accepted_in_trial_receipt') is not True or row.get('status')!='routing_accepted'
            or row.get('guidance_policy') is not None or row.get('result')!=str(trial)
            or {x.name for x in directory.iterdir()}!={'portfolio-summary.json','protocol.json','frozen-code','01-via_default'}
            or any(not q.finite_nonnegative(row.get(k)) or row[k]>row['assigned_seconds'] for k in ('invocation_wall_seconds','invocation_cpu_seconds'))
            or any(not q.finite_nonnegative(old.get(k)) or old[k]>prior[i] for i,k in enumerate(('wall_seconds','total_cpu_seconds')))):
        raise p.Rejected('retained trial prefix or costs differ')
    if completed:
        if (paired_protocol.get('wall_budget_per_arm_seconds')!=BUDGET
                or paired_protocol.get('cpu_budget_per_arm_seconds')!=BUDGET
                or any(old['selected'].get(key)!=row.get(key) for key in (
                    'id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm'))
                or old.get('pareto_frontier')!=['via_default']
                or not q.finite_nonnegative(row.get('assigned_seconds')) or row['assigned_seconds']>old_budget):
            raise p.Rejected('completed default selection or old allocation differs')
    compatible_resume_freeze(protocol['freeze'],current)
    if pc.inventory(directory/'frozen-code')!=protocol['freeze']['files_sha256']:
        raise p.Rejected('retained frozen portfolio code differs from original contract')
    if protocol['freeze']['tools']!=paired_protocol['freeze']['tools'] or protocol['freeze']['source_hashes']!=paired_protocol['freeze']['source_hashes']:
        raise p.Rejected('old portfolio/paired frozen contract differs')
    retained=json.loads(f.canonical(pc.inventory(directory,with_directories=True)))
    if completed and hashlib.sha256(f.canonical(retained).encode()).hexdigest()!=plan.get('retained_inventory_sha256'):
        raise p.Rejected('completed prefix artifact population differs from prospective pin')
    verify_row(row,board,protocol['freeze']);row['eligible']=True
    row.update(retained_from=str(directory/'portfolio-summary.json'),retained_contract_sha256=hashlib.sha256(f.canonical(protocol['freeze']).encode()).hexdigest())
    return {'plan_path':str(path),'plan_sha256':pin,'plan':plan,'prior_freeze':protocol['freeze'],'retained_trial':row,
            'prior_wall_seconds':prior[0],'prior_cpu_seconds':prior[1],'retained_inventory':retained}


def verify_resume_basis(basis):
    if p.sha(_resume_path(basis['plan_path']))!=basis['plan_sha256']:raise p.Rejected('resume plan changed')
    for name,digest in basis['plan']['artifacts'].items():
        if p.sha(_resume_path(name))!=digest:raise p.Rejected('retained resume artifact changed')
    if f.canonical(pc.inventory(_resume_path(basis['plan']['old_directory']),with_directories=True))!=f.canonical(basis['retained_inventory']):
        raise p.Rejected('retained completed portfolio changed')


def trial_freeze(protocol,row):
    """New rows use current freeze; the sole retained row uses its old contract."""
    basis=protocol.get('resume')
    if basis and row.get('result')==basis['retained_trial']['result']:
        expected=basis['retained_trial']
        if row!=expected:raise p.Rejected('retained row differs from prospective resume contract')
        return basis['prior_freeze']
    if 'retained_from' in row or 'retained_contract_sha256' in row:raise p.Rejected('unknown retained row')
    return protocol['freeze']


def experiment(out, project_name='sonde', *, guidance_policy=None, budget=BUDGET,
               resume_plan=None, resume_plan_sha256=None, allocation='remaining',
               outer_ceiling=MAX_OPERATIONAL_BUDGET):
    if guidance_policy not in (None,'placement-search-v1'):raise p.Rejected('unsupported portfolio guidance')
    if (allocation not in ('remaining','balanced') or not q.finite_nonnegative(outer_ceiling)
            or not 60<=outer_ceiling<=MAX_OPERATIONAL_BUDGET
            or not q.finite_nonnegative(budget) or not 60<=budget<=outer_ceiling):
        raise p.Rejected('invalid bounded portfolio allowance or allocation')
    if resume_plan is not None and (allocation!='remaining' or budget>BUDGET):
        raise p.Rejected('resume requires legacy remaining allocation within120')
    started, cpu_started = time.monotonic(), q.total_process_cpu()
    if (resume_plan is None)!=(resume_plan_sha256 is None):raise p.Rejected('resume requires plan and exact SHA together')
    prior_wall=prior_cpu=0.;basis=None
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    out = Path(out).resolve()
    if resume_plan is not None:
        raw=pc.read_bytes(_resume_path(resume_plan),32*1024*1024)
        if hashlib.sha256(raw).hexdigest()!=resume_plan_sha256:raise p.Rejected('resume plan pin differs')
        pinned_plan=json.loads(raw)
        original_root=_resume_path(pinned_plan['old_directory']).parent
        if out==original_root or original_root in out.parents or out in original_root.parents:
            raise p.Rejected('fresh resumed output must be outside original comparison')
    if c.ROOT / '.runs' not in out.parents:
        raise p.Rejected('portfolio output must be under this checkout .runs')
    out.mkdir(parents=True, exist_ok=False)
    summary = {'schema': 1, 'kind': 'experimental_baseline_portfolio', 'status': 'incomplete',
               'comparison_eligible': False, 'selected': None, 'trials': [], 'pareto_frontier': [], 'guidance_policy':guidance_policy,
               'wall_budget_seconds': budget, 'cpu_budget_seconds': budget,
               'allocation':allocation, 'operational_outer_ceiling_seconds':outer_ceiling,
               'cpu_enforcement': 'postcompletion acceptance cap; no total-CPU preemption',
               'selection_rule': 'minimum (native via count, native track length, fixed attempt index)',
               'started_utc': started_utc,
               'host_load_average_1_5_15_minutes_begin': list(os.getloadavg()),
               'claims_limit': 'exposed development experiment; no population superiority or electrical adequacy claim',
               'receipt_scope': 'selected trial receipt charges that trial only; this summary charges the entire portfolio',
               'physical_electrical_validation': False, 'applied': False}

    def totals():
        return prior_wall+time.monotonic() - started, prior_cpu+q.total_process_cpu() - cpu_started

    def remaining():
        wall, cpu = totals()
        return min(budget - wall, budget - cpu)

    def preserve_partial():
        partial = out / 'portfolio-summary.json.partial'
        if partial.exists():
            if partial.is_symlink() or not partial.is_file():
                raise p.Rejected('invalid interrupted portfolio summary')
            with (out/'cancelled-summary.partial').open('xb') as retained:
                retained.write(partial.read_bytes())
            partial.unlink()

    try:
        if resume_plan is not None:
            prior_wall,prior_cpu=pinned_plan['prior_invocation_wall_seconds'],pinned_plan['prior_invocation_cpu_seconds']
            if any(not q.finite_nonnegative(value) or value>budget for value in (prior_wall,prior_cpu)):
                raise p.Rejected('invalid prior invocation costs')
            summary.update(prior_invocation_wall_seconds=prior_wall,prior_invocation_cpu_seconds=prior_cpu)
        p.check_storage()
        board, family = q.selected_source(project_name)
        frozen = freeze(board)
        if resume_plan is not None:
            basis=resume_basis(resume_plan,resume_plan_sha256,board,frozen,budget,project_name,guidance_policy)
            prior_wall,prior_cpu=basis['prior_wall_seconds'],basis['prior_cpu_seconds']
            summary.update(schema=2,kind='experimental_baseline_portfolio_resume',resume_plan_sha256=resume_plan_sha256,
                prior_invocation_wall_seconds=prior_wall,prior_invocation_cpu_seconds=prior_cpu,
                startup_clock_scope='experiment includes new setup/readback/trials/selection; caller additionally charges full new startup/outer finalization and records calendar gap')
            summary['trials'].append(basis['retained_trial'])
        for relative, digest in frozen['files_sha256'].items():
            copied = out / 'frozen-code' / relative
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(c.ROOT / relative, copied)
            if p.sha(copied) != digest:
                raise p.Rejected('frozen code changed while copying')
        protocol = {'schema': 1, 'family': family, 'source': str(board), 'freeze': frozen,
                    'allocation':allocation, 'operational_outer_ceiling_seconds':outer_ceiling,
                    'variants': list(VARIANTS), 'fixed_order': True, 'guidance_policy':guidance_policy,
                    'scoring': {name: p.engine_scoring_settings(name) for name in VARIANTS},
                    'selection_rule': summary['selection_rule'], 'wall_budget_seconds': budget,
                    'cpu_budget_seconds': budget, 'root_finalization_reserve_seconds': FINAL_RESERVE,
                    'attempt_allocation': ('min(remaining global wall, remaining global CPU) minus finalization reserve; route helper then withholds its engine grace/native reserves' if allocation=='remaining' else
                        '(min(remaining global wall, remaining global CPU) minus finalization reserve) / unattempted variants; route helper preserves its engine grace/native reserves'),
                    'constraints': 'same immutable source, targets, adapter, native validation, and per-board support policy for every attempt',
                    'validation': 'every accepted trial receives native validation; final selection rechecks exact unchanged receipt/candidate. No candidate is copied or mutated during selection.',
                    'cpu_accounting': 'RUSAGE_SELF + RUSAGE_CHILDREN deltas over this whole invocation, including all setup, attempts, checks, and selection; never sum nested receipt CPU into this value',
                    'claim_scope': summary['claims_limit']}
        if basis:
            protocol.update(schema=2,resume=basis)
            if basis['plan']['policy']==COMPLETED_PREFIX_POLICY:
                prefix_allocation={'policy':COMPLETED_PREFIX_POLICY,'old_budget_seconds':basis['plan']['old_budget_seconds'],
                    'new_budget_seconds':budget,'outer_arm_budget_seconds':BUDGET,'full_arm_charge_required':True,
                    'accounting_limit':'Planning budget includes full prior invocation plus new helper costs; caller must additionally charge all old/new shared, prerequisite, startup, outer and final audit costs to unchanged120wall/fullCPU before a paired claim.'}
                protocol['completed_prefix_allocation']=prefix_allocation;summary['completed_prefix_allocation']=copy.deepcopy(prefix_allocation)
        p.save_json(out / 'protocol.json', protocol)
        summary.update(protocol_sha256=p.sha(out / 'protocol.json'), source=str(board), family=family)
        def stable():
            q.verify_freeze(frozen,board)
            if basis:verify_resume_basis(basis)
        def verified(row):return verify_row(row,board,trial_freeze(protocol,row))
        for index, variant in enumerate(VARIANTS):
            if basis and index==0:continue
            stable()
            available = remaining()
            unattempted = len(VARIANTS)-index
            assigned = (available-FINAL_RESERVE) / (unattempted if allocation=='balanced' else 1)
            # Do not start expensive preparation when even the current engine
            # minimum cannot fit. route() repeats this check after preparation.
            if assigned < p.ENGINE_GRACE_RESERVE_SECONDS + p.ENGINE_NATIVE_RESERVE_SECONDS + 1:
                summary['stop_reason'] = 'insufficient remaining budget for another attempt and reserves'
                summary['skipped_variants'] = [{'id':name,'reason':summary['stop_reason'],
                    'available_wall_full_cpu_seconds':available,'allocation':allocation,'assigned_if_started_seconds':assigned}
                    for name in VARIANTS[index:]]
                break
            directory = out / f'{index + 1:02d}-{variant}'
            before_wall, before_cpu = time.monotonic(), q.total_process_cpu()
            trial_started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            try:
                result = p.route(board, directory, assigned, False, 'both', 'tuned', scoring_variant=variant) if guidance_policy is None else f.route(board,directory,assigned,False,'both','tuned',variant,guidance_policy=guidance_policy)
            except (Exception, KeyboardInterrupt) as exc:
                # Preserve an invocation failure even when route() fails before
                # creating its own receipt. Cancellation invalidates the whole
                # portfolio and is never hidden by an earlier accepted trial.
                summary['trials'].append({'index': index, 'id': variant, 'assigned_seconds': assigned, 'guidance_policy':guidance_policy,
                    'remaining_wall_full_cpu_seconds_at_assignment':available,'unattempted_variants_at_assignment':unattempted,'allocation':allocation,
                    'status': 'cancelled' if isinstance(exc, KeyboardInterrupt) else 'invocation_error',
                    'eligible': False, 'reason': type(exc).__name__ + ': ' + str(exc),
                    'invocation_wall_seconds': time.monotonic() - before_wall,
                    'invocation_cpu_seconds': q.total_process_cpu() - before_cpu,
                    'directory': str(directory)})
                raise
            trial_wall, trial_cpu = time.monotonic() - before_wall, q.total_process_cpu() - before_cpu
            receipt = directory / 'result.json'
            metrics = result.get('metrics', {})
            row = {'index': index, 'id': variant, 'assigned_seconds': assigned, 'guidance_policy':guidance_policy,
                   'remaining_wall_full_cpu_seconds_at_assignment':available,
                   'unattempted_variants_at_assignment':unattempted,
                   'allocation':allocation,
                   'started_utc': trial_started_utc,
                   'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'status': result.get('status'), 'reason': result.get('reason'),
                   'accepted_in_trial_receipt': result.get('accepted') is True,
                   'eligible': False, 'invocation_wall_seconds': trial_wall,
                   'invocation_cpu_seconds': trial_cpu,
                   'result': str(receipt), 'result_sha256': p.sha(receipt),
                   'candidate': result.get('candidate'), 'candidate_sha256': result.get('candidate_sha256'),
                   'native_report_sha256': result.get('native_report_sha256'),
                   'vias': metrics.get('vias'), 'length_mm': metrics.get('track_length_mm'),
                   'peak_child_rss_bytes': result.get('peak_child_rss_bytes'),
                   'peak_polled_group_rss_bytes': max([step.get('sampled_peak_group_rss_bytes') or 0 for step in result.get('steps', [])] + [0]),
                   'native': result.get('native')}
            summary['trials'].append(row)
            if q.cancelled(result):
                raise KeyboardInterrupt
            stable()
            if row['accepted_in_trial_receipt']:
                if not all(q.finite_nonnegative(value) and value <= assigned for value in (trial_wall, trial_cpu)):
                    row['verification_error'] = 'trial invocation exceeded its assigned wall/CPU allowance'
                else:
                    verified(row)
                    row['eligible'] = True
            p.save_json(out / 'portfolio-summary.json', summary)
            if remaining() <= FINAL_RESERVE:
                summary['stop_reason'] = 'global finalization reserve reached'
                break
        # Recheck every retained eligible receipt before computing the frontier;
        # stale losers must not remain an apparently valid stronger baseline.
        for row in summary['trials']:
            if row['eligible']:
                verified(row)
        stable()
        summary['pareto_frontier'] = frontier(summary['trials'])
        candidates = [row for row in summary['trials'] if row['eligible']]
        if candidates:
            chosen = min(candidates, key=rank)
            selected_check = verified(chosen)
            summary['selected'] = {key: chosen[key] for key in ('id', 'result', 'result_sha256', 'candidate', 'candidate_sha256', 'native_report_sha256', 'vias', 'length_mm')}
            summary['selected']['consistency'] = selected_check
            stable()
            summary.update(status='completed', comparison_eligible=True)
        else:
            summary['status'] = 'no_valid_candidate'
    except KeyboardInterrupt:
        summary.update(status='cancelled', comparison_eligible=False, selected=None)
    except Exception as exc:
        summary.update(status='invalidated', comparison_eligible=False, selected=None,
                       reason=type(exc).__name__ + ': ' + str(exc))

    def account():
        wall, cpu = totals()
        summary.update(wall_seconds=wall, total_cpu_seconds=cpu)
        attempted=[row['id'] for row in summary['trials']]
        summary.update(attempted_variants=attempted,unattempted_variants=[name for name in VARIANTS if name not in attempted],
                       all_variants_attempted=attempted==list(VARIANTS))
        if summary['unattempted_variants'] and 'skipped_variants' not in summary:
            summary['skipped_variants']=[{'id':name,'reason':summary.get('stop_reason',summary.get('reason',summary['status']))}
                for name in summary['unattempted_variants']]
        if not all(q.finite_nonnegative(value) and value <= budget for value in (wall, cpu)):
            summary.update(status='budget_exceeded', comparison_eligible=False, selected=None)

    def archive_failed_index():
        # Preserve any emitted positive as failure evidence before corrections.
        index=out/'portfolio-summary.json'
        if index.is_symlink():raise p.Rejected('unsafe portfolio index during invalidation')
        if index.exists():index.rename(out/('invalidated-portfolio-summary-'+uuid.uuid4().hex+'.json'))

    summary['accounting_point'] = 'sample before summary write; caps checked again after write; over-cap correction can finish outside cap'
    summary['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    summary['host_load_average_1_5_15_minutes_end'] = list(os.getloadavg())
    summary['peak_child_rss_bytes'] = max([row.get('peak_child_rss_bytes') or 0 for row in summary['trials']] + [0])
    summary['peak_polled_group_rss_bytes'] = max([row.get('peak_polled_group_rss_bytes') or 0 for row in summary['trials']] + [0])
    try:
        if summary['status'] == 'cancelled':
            preserve_partial()
        if basis:stable()
        account()
        p.save_json(out / 'portfolio-summary.json', summary)
        if basis:
            stable()
            if json.loads((out/'portfolio-summary.json').read_text())!=summary:raise p.Rejected('resume summary changed during publication')
        if remaining() < 0:
            account()
            p.save_json(out / 'portfolio-summary.json', summary)
    except KeyboardInterrupt:
        # Final publication is still part of the cancellable operation. Keep
        # an interrupted write as evidence before emitting a rejected summary.
        # Never modify any underlying trial receipt or source project.
        archive_failed_index();preserve_partial()
        wall, cpu = totals()
        summary.update(status='cancelled', comparison_eligible=False, selected=None,
                       wall_seconds=wall, total_cpu_seconds=cpu)
        p.save_json(out / 'portfolio-summary.json', summary)
    except Exception as exc:
        archive_failed_index()
        if not basis:raise
        summary.update(status='invalidated',comparison_eligible=False,selected=None,reason=type(exc).__name__+': '+str(exc))
        account();p.save_json(out/'portfolio-summary.json',summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--project', choices=tuple(q.PROJECTS), default='sonde')
    parser.add_argument('--budget',type=float,default=BUDGET)
    parser.add_argument('--allocation',choices=('remaining','balanced'),default='remaining')
    parser.add_argument('--outer-ceiling',type=float,default=MAX_OPERATIONAL_BUDGET)
    parser.add_argument('--resume-plan')
    parser.add_argument('--resume-plan-sha256')
    args = parser.parse_args()
    lock_path = c.ROOT / '.runs/quality-experiment.lock'
    lock_path.parent.mkdir(exist_ok=True)
    if lock_path.is_symlink():
        parser.error('experiment lock must not be a symlink')
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        with lock_path.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = experiment(Path(args.output), args.project,budget=args.budget,
                resume_plan=args.resume_plan,resume_plan_sha256=args.resume_plan_sha256,
                allocation=args.allocation,outer_ceiling=args.outer_ceiling)
        print(json.dumps({'status': result['status'], 'summary': str(Path(args.output) / 'portfolio-summary.json')}))
        return 0 if result['comparison_eligible'] else 2
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == '__main__':
    raise SystemExit(main())
