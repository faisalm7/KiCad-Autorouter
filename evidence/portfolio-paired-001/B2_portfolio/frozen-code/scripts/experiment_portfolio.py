#!/usr/bin/env python3
"""Fixed, sequential development B2 portfolio with one shared wall/CPU budget.

No routing job may run alongside this experiment. The output indexes retained
native-validated trial receipts; it is not itself a pipeline routing receipt.
No reference route is used for parameter selection, ranking, or scoring.
"""
from __future__ import annotations

import argparse
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import config as c, pipeline as p
from scripts import experiment_quality as q

BUDGET = 120.0
FINAL_RESERVE = 15.0
VARIANTS = ('via_default', 'via_low', 'via_high')
SCRIPT = Path(__file__).resolve()


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
    receipt = Path(row['result'])
    if receipt.is_symlink() or p.sha(receipt) != row['result_sha256']:
        raise p.Rejected('trial receipt changed')
    data = json.loads(receipt.read_text())
    if (data.get('source') != str(board) or data.get('source_hashes') != frozen['source_hashes']
            or data.get('tools') != frozen['tools'] or data.get('engine_profile') != 'tuned'
            or data.get('adapter') != 'both' or data.get('scoring_variant') != row['id']
            or data.get('scope') != 'whole_board_unlocked_routing'
            or data.get('budget_seconds') != row['assigned_seconds']
            or data.get('cpu_budget_seconds') != row['assigned_seconds']):
        raise p.Rejected('trial differs from frozen portfolio contract')
    engine = data.get('engine_budget', {})
    expected = p.engine_profile_settings('tuned', engine.get('remaining_outer_wall_seconds_at_assignment'),
        strict_class_targets=data.get('netclass_policy') is not None, scoring_variant=row['id'])
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


def experiment(out, project_name='sonde'):
    started, cpu_started = time.monotonic(), q.total_process_cpu()
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    out = Path(out).resolve()
    if c.ROOT / '.runs' not in out.parents:
        raise p.Rejected('portfolio output must be under this checkout .runs')
    out.mkdir(parents=True, exist_ok=False)
    summary = {'schema': 1, 'kind': 'experimental_baseline_portfolio', 'status': 'incomplete',
               'comparison_eligible': False, 'selected': None, 'trials': [], 'pareto_frontier': [],
               'wall_budget_seconds': BUDGET, 'cpu_budget_seconds': BUDGET,
               'cpu_enforcement': 'postcompletion acceptance cap; no total-CPU preemption',
               'selection_rule': 'minimum (native via count, native track length, fixed attempt index)',
               'started_utc': started_utc,
               'host_load_average_1_5_15_minutes_begin': list(os.getloadavg()),
               'claims_limit': 'exposed development experiment; no population superiority or electrical adequacy claim',
               'receipt_scope': 'selected trial receipt charges that trial only; this summary charges the entire portfolio',
               'physical_electrical_validation': False, 'applied': False}

    def totals():
        return time.monotonic() - started, q.total_process_cpu() - cpu_started

    def remaining():
        wall, cpu = totals()
        return min(BUDGET - wall, BUDGET - cpu)

    def preserve_partial():
        partial = out / 'portfolio-summary.json.partial'
        if partial.exists():
            if partial.is_symlink() or not partial.is_file():
                raise p.Rejected('invalid interrupted portfolio summary')
            with (out/'cancelled-summary.partial').open('xb') as retained:
                retained.write(partial.read_bytes())
            partial.unlink()

    try:
        p.check_storage()
        board, family = q.selected_source(project_name)
        frozen = freeze(board)
        for relative, digest in frozen['files_sha256'].items():
            copied = out / 'frozen-code' / relative
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(c.ROOT / relative, copied)
            if p.sha(copied) != digest:
                raise p.Rejected('frozen code changed while copying')
        protocol = {'schema': 1, 'family': family, 'source': str(board), 'freeze': frozen,
                    'variants': list(VARIANTS), 'fixed_order': True,
                    'scoring': {name: p.engine_scoring_settings(name) for name in VARIANTS},
                    'selection_rule': summary['selection_rule'], 'wall_budget_seconds': BUDGET,
                    'cpu_budget_seconds': BUDGET, 'root_finalization_reserve_seconds': FINAL_RESERVE,
                    'attempt_allocation': 'min(remaining global wall, remaining global CPU) minus finalization reserve; route helper then withholds its engine grace/native reserves',
                    'constraints': 'same immutable source, targets, adapter, native validation, and per-board support policy for every attempt',
                    'validation': 'every accepted trial receives native validation; final selection rechecks exact unchanged receipt/candidate. No candidate is copied or mutated during selection.',
                    'cpu_accounting': 'RUSAGE_SELF + RUSAGE_CHILDREN deltas over this whole invocation, including all setup, attempts, checks, and selection; never sum nested receipt CPU into this value',
                    'claim_scope': summary['claims_limit']}
        p.save_json(out / 'protocol.json', protocol)
        summary.update(protocol_sha256=p.sha(out / 'protocol.json'), source=str(board), family=family)
        for index, variant in enumerate(VARIANTS):
            q.verify_freeze(frozen, board)
            assigned = remaining() - FINAL_RESERVE
            # Do not start expensive preparation when even the current engine
            # minimum cannot fit. route() repeats this check after preparation.
            if assigned < p.ENGINE_GRACE_RESERVE_SECONDS + p.ENGINE_NATIVE_RESERVE_SECONDS + 1:
                summary['stop_reason'] = 'insufficient remaining budget for another attempt and reserves'
                break
            directory = out / f'{index + 1:02d}-{variant}'
            before_wall, before_cpu = time.monotonic(), q.total_process_cpu()
            trial_started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            try:
                result = p.route(board, directory, assigned, False, 'both', 'tuned', scoring_variant=variant)
            except (Exception, KeyboardInterrupt) as exc:
                # Preserve an invocation failure even when route() fails before
                # creating its own receipt. Cancellation invalidates the whole
                # portfolio and is never hidden by an earlier accepted trial.
                summary['trials'].append({'index': index, 'id': variant, 'assigned_seconds': assigned,
                    'status': 'cancelled' if isinstance(exc, KeyboardInterrupt) else 'invocation_error',
                    'eligible': False, 'reason': type(exc).__name__ + ': ' + str(exc),
                    'invocation_wall_seconds': time.monotonic() - before_wall,
                    'invocation_cpu_seconds': q.total_process_cpu() - before_cpu,
                    'directory': str(directory)})
                raise
            trial_wall, trial_cpu = time.monotonic() - before_wall, q.total_process_cpu() - before_cpu
            receipt = directory / 'result.json'
            metrics = result.get('metrics', {})
            row = {'index': index, 'id': variant, 'assigned_seconds': assigned,
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
            q.verify_freeze(frozen, board)
            if row['accepted_in_trial_receipt']:
                if not all(q.finite_nonnegative(value) and value <= assigned for value in (trial_wall, trial_cpu)):
                    row['verification_error'] = 'trial invocation exceeded its assigned wall/CPU allowance'
                else:
                    verify_row(row, board, frozen)
                    row['eligible'] = True
            p.save_json(out / 'portfolio-summary.json', summary)
            if remaining() <= FINAL_RESERVE:
                summary['stop_reason'] = 'global finalization reserve reached'
                break
        # Recheck every retained eligible receipt before computing the frontier;
        # stale losers must not remain an apparently valid stronger baseline.
        for row in summary['trials']:
            if row['eligible']:
                verify_row(row, board, frozen)
        q.verify_freeze(frozen, board)
        summary['pareto_frontier'] = frontier(summary['trials'])
        candidates = [row for row in summary['trials'] if row['eligible']]
        if candidates:
            chosen = min(candidates, key=rank)
            verified = verify_row(chosen, board, frozen)
            summary['selected'] = {key: chosen[key] for key in ('id', 'result', 'result_sha256', 'candidate', 'candidate_sha256', 'native_report_sha256', 'vias', 'length_mm')}
            summary['selected']['consistency'] = verified
            q.verify_freeze(frozen, board)
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
        if not all(q.finite_nonnegative(value) and value <= BUDGET for value in (wall, cpu)):
            summary.update(status='budget_exceeded', comparison_eligible=False, selected=None)

    summary['accounting_point'] = 'sample before summary write; caps checked again after write; over-cap correction can finish outside cap'
    summary['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    summary['host_load_average_1_5_15_minutes_end'] = list(os.getloadavg())
    summary['peak_child_rss_bytes'] = max([row.get('peak_child_rss_bytes') or 0 for row in summary['trials']] + [0])
    summary['peak_polled_group_rss_bytes'] = max([row.get('peak_polled_group_rss_bytes') or 0 for row in summary['trials']] + [0])
    try:
        if summary['status'] == 'cancelled':
            preserve_partial()
        account()
        p.save_json(out / 'portfolio-summary.json', summary)
        if remaining() < 0:
            account()
            p.save_json(out / 'portfolio-summary.json', summary)
    except KeyboardInterrupt:
        # Final publication is still part of the cancellable operation. Keep
        # an interrupted write as evidence before emitting a rejected summary.
        # Never modify any underlying trial receipt or source project.
        preserve_partial()
        wall, cpu = totals()
        summary.update(status='cancelled', comparison_eligible=False, selected=None,
                       wall_seconds=wall, total_cpu_seconds=cpu)
        p.save_json(out / 'portfolio-summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--project', choices=tuple(q.PROJECTS), default='sonde')
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
            result = experiment(Path(args.output), args.project)
        print(json.dumps({'status': result['status'], 'summary': str(Path(args.output) / 'portfolio-summary.json')}))
        return 0 if result['comparison_eligible'] else 2
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == '__main__':
    raise SystemExit(main())
