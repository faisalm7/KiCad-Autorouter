#!/usr/bin/env python3
"""Paired exposed-development experiment: B2 portfolio, then C feedback.

Public callable: experiment(out: Path, project_name='sonde') -> summary dict.
CLI after promotion: python3 scripts/experiment_paired.py --project sonde
                    --output "$PWD/.runs/paired-001"
Commit this wrapper and its imported implementation before running. The caller
must keep the native/engine lane idle; CLI shares the existing experiment lock.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
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
from autorouter import config as c, pipeline as p, floor_route as f, placement_strategy as ps
from autorouter.strategy import prune
from autorouter.recovery import recover
from scripts import experiment_portfolio as portfolio, experiment_quality as q

BUDGET = 120.0
SCRIPT = Path(__file__).resolve()
C_ARM = {'id': 'C_feedback', 'adapter': 'both', 'engine_profile': 'tuned',
         'operation': 'prune', 'proposal_policy': 'feedback'}
THERMAL_ARM = {'id': 'C_thermal', 'adapter': 'both', 'engine_profile': 'completion-only',
               'operation': 'recover', 'strategy': 'native_validated_thermal_bridge'}


def cancelled_publication(path, data):
    data['status'] = 'cancelled'
    if 'accepted' in data:data['accepted'] = False
    if 'comparisons' in data:data['comparisons'] = []
    for row in data.get('results', []):
        row['accepted'] = False
        for observation in row.get('observations', []):observation['final_delivery_accepted'] = False
    partial = path.with_suffix(path.suffix+'.partial')
    if partial.exists():
        if partial.is_symlink() or not partial.is_file():
            raise p.Rejected('invalid interrupted paired output')
        with partial.with_name(partial.name+'.cancelled').open('xb') as retained:
            retained.write(partial.read_bytes())
        partial.unlink()
    p.save_json(path, data)


def publish(path, data):
    try:
        p.save_json(path, data)
    except KeyboardInterrupt:
        cancelled_publication(path, data)
        raise


def verify_portfolio(directory, returned, board, frozen):
    """Bind selection and every frontier point to unchanged native trial evidence."""
    receipt = directory/'portfolio-summary.json'
    digest = p.sha(receipt)
    data = json.loads(receipt.read_text())
    protocol = json.loads((directory/'protocol.json').read_text())
    if (receipt.is_symlink() or data != returned
            or data.get('protocol_sha256') != p.sha(directory/'protocol.json')
            or protocol.get('freeze', {}).get('tools') != frozen['tools']
            or protocol.get('freeze', {}).get('source_hashes') != frozen['source_hashes']
            or protocol.get('variants') != list(portfolio.VARIANTS)):
        raise p.Rejected('portfolio index differs from frozen paired protocol')
    cancelled = data.get('status') == 'cancelled'
    for row in data.get('trials', []):
        cancelled = cancelled or row.get('status') == 'cancelled'
        if row.get('result'):
            trial_path = Path(row['result'])
            if trial_path.parent.parent != directory or trial_path.name != 'result.json':
                raise p.Rejected('portfolio trial escaped this arm')
            cancelled = cancelled or q.cancelled(json.loads(trial_path.read_text()))
        if row.get('eligible') is True:
            portfolio.verify_row(row, board, frozen)
    if cancelled:
        raise KeyboardInterrupt
    if data.get('comparison_eligible') is True:
        valid = [row for row in data['trials'] if row.get('eligible') is True]
        if (not valid or data.get('pareto_frontier') != portfolio.frontier(data['trials'])
                or data.get('selected', {}).get('id') != min(valid, key=portfolio.rank)['id']
                or not all(q.finite_nonnegative(value) and value <= BUDGET
                           for value in (data.get('wall_seconds'), data.get('total_cpu_seconds')))):
            raise p.Rejected('portfolio selection/frontier/budget is inconsistent')
        chosen = min(valid, key=portfolio.rank)
        if any(data['selected'].get(key) != chosen[key] for key in
               ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm')):
            raise p.Rejected('selected portfolio candidate differs from winning trial')
    if p.sha(receipt) != digest:
        raise p.Rejected('portfolio index changed while checking')
    return {'id': 'B2_portfolio', 'status': data['status'], 'accepted': data['comparison_eligible'] is True,
            'result': str(receipt), 'result_sha256': digest, 'selected': data.get('selected'),
            'pareto_frontier': data.get('pareto_frontier', []), 'trials': data.get('trials', []),
            'peak_child_rss_bytes': data.get('peak_child_rss_bytes'),
            'peak_polled_group_rss_bytes': data.get('peak_polled_group_rss_bytes')}


def comparisons(rows):
    """Report every valid baseline frontier point; do not hide tradeoffs."""
    by_id = {row['id']: row for row in rows}
    baseline = by_id.get('B2_portfolio')
    system = by_id.get('C_feedback') or by_id.get('C_thermal')
    if not system or not system['accepted']:
        return []
    result = []
    for row in (baseline['trials'] if baseline and baseline['accepted'] else []):
        if row['id'] not in baseline['pareto_frontier']:
            continue
        length_delta = system['length_mm'] - row['length_mm']
        via_delta = system['vias'] - row['vias']
        result.append({'baseline_variant': row['id'], 'system': system['id'],
            'baseline_selected': baseline['selected']['id'] == row['id'],
            'length_delta_mm': length_delta, 'via_delta': via_delta,
            'C_dominates_with_1e_6mm_tolerance': length_delta <= 1e-6 and via_delta <= 0 and (length_delta < -1e-6 or via_delta < 0),
            'baseline_dominates_with_1e_6mm_tolerance': length_delta >= -1e-6 and via_delta >= 0 and (length_delta > 1e-6 or via_delta > 0)})
    for name in ('B0','B1'):
        row=by_id.get(name)
        if row and row['accepted']:
            length_delta=system['length_mm']-row['length_mm'];via_delta=system['vias']-row['vias']
            result.append({'baseline':name,'system':system['id'],'length_delta_mm':length_delta,'via_delta':via_delta,
                'pareto_improvement':length_delta<=1e-9 and via_delta<=0 and (length_delta< -1e-9 or via_delta<0)})
    return result


def verify_thermal_incumbent(directory, result, board, frozen):
    """Bind the fresh C engine attempt to the declared comparator contract."""
    path = directory/'incumbent/result.json'
    record = result.get('incumbent', {})
    if (any(q.is_symlink() for q in (path,*path.parents)) or record.get('receipt') != str(path)
            or record.get('receipt_sha256') != p.sha(path)):
        raise p.Rejected('thermal incumbent receipt binding mismatch')
    assigned = result.get('incumbent_assigned_seconds')
    if not q.finite_nonnegative(assigned) or not 5 <= assigned <= BUDGET-40:
        raise p.Rejected('thermal incumbent assignment outside declared reserve')
    data = json.loads(path.read_text())
    if (data.get('source') != str(board) or data.get('source_hashes') != frozen['source_hashes']
            or data.get('tools') != frozen['tools'] or data.get('adapter') != 'both'
            or data.get('engine_profile') != 'completion-only' or data.get('scoring_variant') is not None
            or data.get('scope') != 'whole_board_unlocked_routing'
            or data.get('budget_seconds') != result.get('incumbent_assigned_seconds')
            or data.get('cpu_budget_seconds') != result.get('incumbent_assigned_seconds')
            or data.get('status') != record.get('status') or data.get('accepted') != record.get('accepted')):
        raise p.Rejected('thermal incumbent differs from frozen contract')
    engine = data.get('engine_budget', {})
    left = engine.get('remaining_outer_wall_seconds_at_assignment')
    if not q.finite_nonnegative(left) or left > assigned:
        raise p.Rejected('thermal engine remaining allowance exceeds assignment')
    expected = p.engine_profile_settings('completion-only', engine.get('remaining_outer_wall_seconds_at_assignment'),
                                         strict_class_targets=data.get('netclass_policy') is not None)
    if (any(engine.get(k) != v for k,v in expected.items())
            or engine.get('outer_task_wall_budget_seconds') != data['budget_seconds']
            or engine.get('outer_task_cpu_budget_seconds') != data['cpu_budget_seconds']):
        raise p.Rejected('thermal incumbent engine settings mismatch')
    steps = [s for s in data.get('steps', []) if s.get('name') == 'engine']
    expected_argv = ['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(c.JAVA),
                     '-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(c.JAR),
                     '--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da',
                     '--user_data_path='+str(path.parent/'engine-config'),'--logging.file.enabled=false',
                     *expected['argv'],'-de',str(path.parent/'task.dsn'),'-do',str(path.parent/'routes.ses')]
    if (len(steps) != 1 or steps[0].get('status') != 'success' or steps[0].get('exit_code') != 0
            or steps[0].get('cleanup_complete') is not True
            or steps[0].get('argv') != expected_argv or steps[0].get('cwd') != str(path.parent)
            or json.loads((path.parent/'engine-process.json').read_text()) != steps[0]):
        raise p.Rejected('thermal incumbent engine execution mismatch')
    for name,field in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
        if (path.parent/name).is_symlink() or p.sha(path.parent/name) != data.get(field):
            raise p.Rejected('thermal incumbent export changed')
    if result.get('accepted') is True and data.get('status') not in {'routing_accepted','drc_rejected'}:
        raise p.Rejected('thermal recovery used an ineligible incumbent')
    if p.sha(path) != record['receipt_sha256']:
        raise p.Rejected('thermal incumbent changed during verification')


def experiment(out, project_name='sonde', system='feedback'):
    batch_started, batch_cpu = time.monotonic(), q.total_process_cpu()
    if system not in {'feedback','thermal','placement'}:
        raise p.Rejected('unknown paired system')
    c_arm = ({**C_ARM,'operation':'placement_prune','input_policy':ps.POLICY,'strategy':ps.STRATEGY} if system=='placement' else C_ARM if system=='feedback' else THERMAL_ARM)
    if system=='placement' and project_name!='multichannel':raise p.Rejected('placement comparison currently frozen for multichannel')
    out = Path(out).resolve()
    if c.ROOT/'.runs' not in out.parents:
        raise p.Rejected('paired output must be a new project-local .runs directory')
    out.mkdir(parents=True, exist_ok=False)
    summary = {'schema': 1, 'kind': 'paired_development_comparison', 'status': 'incomplete',
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'results': [], 'comparisons': [], 'claims_limit': 'one exposed family; no population, novelty, human-review, or electrical-adequacy claim'}
    completed_arms={}
    def stable_arms():
        if system=='placement':
            for folder,expected in completed_arms.items():
                if ps.pc.inventory(folder,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2)!=expected:raise p.Rejected('completed comparison arm changed')
    # Entry and exit are inside shared accounting, before final publication.
    with p.validation_readback_session() if system=='placement' else nullcontext():
        try:
            if BUDGET != q.BUDGET or BUDGET != portfolio.BUDGET:
                raise p.Rejected('imported arm budgets differ')
            board, family = q.selected_source(project_name)
            frozen = portfolio.freeze(board)
            relative = str(SCRIPT.relative_to(c.ROOT))
            committed = subprocess.run(['git', 'show', frozen['tools']['git_head'] + ':' + relative],
                                       cwd=c.ROOT, capture_output=True, check=True).stdout
            if hashlib.sha256(committed).hexdigest() != p.sha(SCRIPT):
                raise p.Rejected('commit exact paired wrapper before running')
            frozen['files_sha256'][relative] = p.sha(SCRIPT)
            for name, digest in frozen['files_sha256'].items():
                target = out/'frozen-code'/name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(c.ROOT/name, target)
                if p.sha(target) != digest:
                    raise p.Rejected('code changed while preserving paired freeze')
            protocol = {'schema': 1, 'freeze': frozen, 'family': family, 'source': str(board),
                'arm_order': (['B0','B1','B2_portfolio',c_arm['id']] if system=='placement' else ['B2_portfolio', c_arm['id']]), 'wall_budget_per_arm_seconds': BUDGET,
                'cpu_budget_per_arm_seconds': BUDGET, 'cpu_enforcement': 'measured acceptance cap, not OS preemption',
                'baseline': 'fixed three search-cost variants, same adapter and native constraints; full frontier retained',
                'system': ('single tuned default-cost incumbent plus feedback pruning' if system in {'feedback','placement'} else 'fresh completion-only default-cost incumbent, fresh native geometry and bounded thermal bridge recovery')+'; no free use of the portfolio winner',
                'system_contract': c_arm,
                'accounting': 'each raw enclosing arm includes pre/post freeze verification, invocation, failed attempts, receipt checks, and arm-index emission; the entire shared initial freeze/copy/paired-summary overhead is then conservatively charged to EACH arm, with caps rechecked after final publication',
                'fairness_limit': 'equal total budgets and constraints, different predeclared allocation policies; C is not initialized by the portfolio',
                'editor_policy': 'operator closes PCB Editor and keeps other native/engine jobs idle',
                'claims_limit': summary['claims_limit']}
            if system=='placement':
                protocol.update(guidance_policy='placement-search-v1',system_contract={**c_arm,'strategy':ps.STRATEGY},
                    allocation_formula='120 - max(shared setup wall, shared setup CPU) - 5; same frozen inner allowance for all four arms',
                    wrapper_reserve_seconds=5,baseline_order=['B0stock','B1standard','B2tuned-default-low-high','Cfresh-tuned-default-feedback'])
                protocol['inner_allowance_seconds']=BUDGET-max(time.monotonic()-batch_started,q.total_process_cpu()-batch_cpu)-5
                if protocol['inner_allowance_seconds']<60:raise p.Rejected('shared setup leaves insufficient equal inner allowance')
            assigned=protocol.get('inner_allowance_seconds',BUDGET)
            p.save_json(out/'protocol.json', protocol)
            summary['protocol_sha256'] = p.sha(out/'protocol.json')
            for arm_id in protocol['arm_order']:
                started, cpu_started = time.monotonic(), q.total_process_cpu()
                row = {'id': arm_id, 'accepted': False, 'status': 'invocation_error',
                    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'host_load_average_1_5_15_minutes_begin': list(os.getloadavg())}
                summary['results'].append(row)
                material=None;directory=out/arm_id
                try:
                    q.verify_freeze(frozen, board)
                    stable_arms()
                    if arm_id == 'B2_portfolio':
                        result = (portfolio.experiment(directory, project_name,guidance_policy='placement-search-v1',budget=assigned)
                                  if system=='placement' else portfolio.experiment(directory, project_name))
                        if system=='placement':material=ps.pc.inventory(directory,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2)
                        row.update(verify_portfolio(directory, result, board, frozen))
                        if system=='placement':
                            if result.get('guidance_policy')!='placement-search-v1' or result.get('wall_budget_seconds')!=assigned or result.get('cpu_budget_seconds')!=assigned:raise p.Rejected('placement portfolio allocation differs')
                            if any(x.get('guidance_policy')!='placement-search-v1' for x in result['trials']):raise p.Rejected('mixed placement portfolio trials')
                    else:
                        selected_arm=c_arm
                        if system=='placement':
                            if arm_id=='B0':
                                selected_arm={'id':'B0','adapter':'none','engine_profile':'standard','operation':'route'}
                                result=p.route(board,directory,assigned,False,'none','standard')
                            elif arm_id=='B1':
                                selected_arm={'id':'B1','adapter':'both','engine_profile':'standard','operation':'route'}
                                result=f.route(board,directory,assigned,False,'both','standard','via_default',guidance_policy='placement-search-v1')
                            else:result=ps.prune(board,directory,assigned)
                        else:
                            result = (prune(board, directory, BUDGET, proposal_policy='feedback')
                                      if system=='feedback' else recover(board, directory, BUDGET))
                        if system=='placement':material=ps.pc.inventory(directory,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2)
                        row.update(q.summarize(selected_arm, directory, result,
                            time.monotonic()-started, q.total_process_cpu()-cpu_started))
                        if system=='thermal' and result.get('strategy')!=THERMAL_ARM['strategy']:
                            raise p.Rejected('thermal strategy contract mismatch')
                        if system=='thermal' and result.get('accepted') is True:
                            verify_thermal_incumbent(directory, result, board, frozen)
                        if q.cancelled(result):
                            raise KeyboardInterrupt
                        if result.get('tools') != frozen['tools'] or result.get('source_hashes') != frozen['source_hashes']:
                            raise p.Rejected('C receipt differs from paired source/code freeze')
                        row['observations'] = q.observations(directory, result, row)
                        if row['accepted'] and not portfolio.valid_metrics({'vias': row['vias'], 'track_length_mm': row['length_mm']}):
                            raise p.Rejected('invalid C metrics for comparison')
                    q.verify_freeze(frozen, board)
                except KeyboardInterrupt:
                    row.update(status='cancelled', accepted=False)
                    raise
                except Exception as exc:
                    row.update(accepted=False, status='invocation_error', reason=type(exc).__name__+': '+str(exc))
                    # Failed outcomes are retained, but source/code changes must
                    # invalidate the pair rather than running a mismatched next arm.
                    q.verify_freeze(frozen, board)
                finally:
                    row.update(invocation_wall_seconds=time.monotonic()-started,
                        invocation_cpu_seconds=q.total_process_cpu()-cpu_started,
                        finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        host_load_average_1_5_15_minutes_end=list(os.getloadavg()))
                    row['within_enclosing_budgets'] = all(q.finite_nonnegative(value) and value <= BUDGET
                        for value in (row['invocation_wall_seconds'], row['invocation_cpu_seconds']))
                    row['accepted'] = row['accepted'] and row['within_enclosing_budgets']
                    publish(out/(arm_id+'-invocation.json'), row)
                    wall, cpu = time.monotonic()-started, q.total_process_cpu()-cpu_started
                    if wall > BUDGET or cpu > BUDGET:
                        row.update(accepted=False, within_enclosing_budgets=False,
                            invocation_wall_seconds=wall, invocation_cpu_seconds=cpu)
                        publish(out/(arm_id+'-invocation.json'), row)
                if system=='placement' and directory.is_dir():
                    current=ps.pc.inventory(directory,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2)
                    if material is not None and current!=material:raise p.Rejected('current comparison arm changed during readback/publication')
                    completed_arms[directory]=current if material is None else material
            q.verify_freeze(frozen, board);stable_arms()
            summary.update(status='completed', comparisons=comparisons(summary['results']))
        except KeyboardInterrupt:
            summary.update(status='cancelled', comparisons=[])
            for row in summary['results']:row['accepted']=False
        except Exception as exc:
            summary.update(status='invalidated', comparisons=[], reason=type(exc).__name__+': '+str(exc))
            for row in summary['results']:row['accepted']=False
    for row in summary['results']:
        row['accepted_before_shared_charge'] = row['accepted']
    def account_shared():
        summary.update(batch_wall_seconds=time.monotonic()-batch_started,
                       batch_cpu_seconds=q.total_process_cpu()-batch_cpu,
                       finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        shared_wall = summary['batch_wall_seconds']-sum(row.get('invocation_wall_seconds',0) for row in summary['results'])
        shared_cpu = summary['batch_cpu_seconds']-sum(row.get('invocation_cpu_seconds',0) for row in summary['results'])
        summary.update(shared_overhead_wall_seconds=shared_wall, shared_overhead_cpu_seconds=shared_cpu)
        for row in summary['results']:
            wall = row.get('invocation_wall_seconds', 0)+shared_wall
            cpu = row.get('invocation_cpu_seconds', 0)+shared_cpu
            within = all(q.finite_nonnegative(value) and value <= BUDGET for value in (wall,cpu))
            row.update(charged_wall_seconds=wall, charged_cpu_seconds=cpu,
                       within_charged_budgets=within,
                       accepted=row['accepted_before_shared_charge'] and within)
            for observation in row.get('observations', []):
                observation['final_delivery_accepted'] = row['accepted']
        summary['comparisons'] = comparisons(summary['results']) if summary['status']=='completed' else []
    summary['shared_charge_policy'] = 'entire measured shared overhead charged to EACH arm; raw invocation measurements retained separately'
    summary['accounting_point'] = 'sample before final summary write; full charged caps rechecked after publication; any over-cap correction is rejected and may finish outside cap'
    try:
        if system=='placement':q.verify_freeze(frozen,board);stable_arms()
        account_shared()
        publish(out/'paired-summary.json', summary)
        if system=='placement':q.verify_freeze(frozen,board);stable_arms()
        published_eligibility = [row['accepted'] for row in summary['results']]
        account_shared()
        if published_eligibility != [row['accepted'] for row in summary['results']]:
            # The correction itself also costs time. Conservatively invalidate
            # this paired comparison instead of publishing another positive
            # paired acceptance while writing the over-cap correction.
            summary['comparison_gate_reason'] = 'final publication crossed a charged cap; paired comparison invalidated'
            summary['comparisons'] = []
            for row in summary['results']:
                row['accepted'] = False
                row['paired_publication_budget_rejected'] = True
                for observation in row.get('observations', []):observation['final_delivery_accepted'] = False
            publish(out/'paired-summary.json', summary)
    except KeyboardInterrupt:
        cancelled_publication(out/'paired-summary.json', summary)
    except Exception as exc:
        summary.update(status='invalidated',comparisons=[],reason=type(exc).__name__+': '+str(exc))
        for row in summary['results']:row['accepted']=False
        publish(out/'paired-summary.json',summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--project', choices=tuple(q.PROJECTS), default='sonde')
    parser.add_argument('--system', choices=('feedback','thermal','placement'), default='feedback')
    args=parser.parse_args()
    lock_path=c.ROOT/'.runs/quality-experiment.lock';lock_path.parent.mkdir(exist_ok=True)
    if lock_path.is_symlink():parser.error('experiment lock must not be a symlink')
    def interrupted(signum,frame):raise KeyboardInterrupt
    previous={sig:signal.signal(sig,interrupted) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        with lock_path.open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            result=experiment(Path(args.output),args.project,args.system)
        print(json.dumps({'status':result['status'],'summary':str(Path(args.output)/'paired-summary.json')}))
        return 0 if result['status']=='completed' else 2
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)


if __name__=='__main__':raise SystemExit(main())
