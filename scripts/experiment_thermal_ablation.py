#!/usr/bin/env python3
"""Fresh B0/B1/completion-only controls, cross-bound to an earlier thermal pair.

Every arm gets its own 120 s wall and CPU cap; all shared overhead is charged to
EACH arm. Prior C/B2 are references, never free inputs or a new jointly timed run.
Only Git HEAD and addition of this harness may differ from the prior frozen code.
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

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT))
from autorouter import config as c, pipeline as p
from scripts import experiment_quality as q, experiment_portfolio as portfolio, experiment_paired as paired

BUDGET = 120.0
SCRIPT = Path(__file__).resolve()
ARMS = (
    {'id':'B0_standard120','adapter':'none','engine_profile':'standard','operation':'route'},
    {'id':'B1_standard120','adapter':'both','engine_profile':'standard','operation':'route'},
    {'id':'B1_completion120','adapter':'both','engine_profile':'completion-only','operation':'route'},
)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read_bound(path, bindings):
    path=Path(path)
    if any(item.is_symlink() for item in (path,*path.parents)) or not path.is_file():
        raise p.Rejected('missing or symlinked evidence: '+str(path))
    before=p.sha(path)
    data=json.loads(path.read_text())
    if p.sha(path)!=before:raise p.Rejected('evidence changed during read')
    bindings[str(path)]=before
    return data


def unchanged(bindings):
    for name,digest in bindings.items():
        path=Path(name)
        if any(item.is_symlink() for item in (path,*path.parents)) or p.sha(path)!=digest:
            raise p.Rejected('bound prior evidence changed: '+name)


def freeze(board):
    frozen=portfolio.freeze(board)
    for path in (paired.SCRIPT,SCRIPT):
        relative=str(path.relative_to(c.ROOT))
        committed=subprocess.run(['git','show',frozen['tools']['git_head']+':'+relative],cwd=c.ROOT,capture_output=True,check=True).stdout
        if hashlib.sha256(committed).hexdigest()!=p.sha(path):raise p.Rejected('commit exact harness before running')
        frozen['files_sha256'][relative]=p.sha(path)
    return frozen


def cross_bind(prior,board,frozen):
    """Check the earlier pair with its own freeze; permit HEAD-only provenance delta."""
    prior=Path(prior)
    bindings={}
    prior_inventory=p.tree_hash(prior)
    protocol=read_bound(prior/'protocol.json',bindings)
    summary=read_bound(prior/'paired-summary.json',bindings)
    old=protocol['freeze']
    old_tools={k:v for k,v in old['tools'].items() if k!='git_head'}
    new_tools={k:v for k,v in frozen['tools'].items() if k!='git_head'}
    if old_tools!=new_tools or old['source_hashes']!=frozen['source_hashes'] or protocol.get('source')!=str(board):
        raise p.Rejected('prior pair production implementation, native tools or source differs')
    if (protocol.get('arm_order')!=['B2_portfolio','C_thermal'] or protocol.get('system_contract')!=paired.THERMAL_ARM
            or protocol.get('wall_budget_per_arm_seconds')!=BUDGET or protocol.get('cpu_budget_per_arm_seconds')!=BUDGET
            or summary.get('protocol_sha256')!=bindings[str(prior/'protocol.json')] or summary.get('status')!='completed'):
        raise p.Rejected('prior pair is not a completed matching thermal protocol')
    expected_old=set(frozen['files_sha256'])-{str(SCRIPT.relative_to(c.ROOT))}
    if set(old['files_sha256'])!=expected_old:raise p.Rejected('prior protocol file inventory differs beyond added harness')
    for name,digest in old['files_sha256'].items():
        if frozen['files_sha256'].get(name)!=digest or p.sha(prior/'frozen-code'/name)!=digest:
            raise p.Rejected('prior frozen production/protocol bytes changed')
        bindings[str(prior/'frozen-code'/name)]=digest
    rows=summary.get('results')
    if not isinstance(rows,list) or [row.get('id') for row in rows]!=protocol['arm_order']:
        raise p.Rejected('prior pair arm inventory differs')
    shared_wall=summary.get('shared_overhead_wall_seconds');shared_cpu=summary.get('shared_overhead_cpu_seconds')
    if not all(q.finite_nonnegative(x) for x in (shared_wall,shared_cpu)):raise p.Rejected('invalid prior shared accounting')
    for key,shared,invkey in [('batch_wall_seconds',shared_wall,'invocation_wall_seconds'),('batch_cpu_seconds',shared_cpu,'invocation_cpu_seconds')]:
        if not q.finite_nonnegative(summary.get(key)) or abs(summary[key]-sum(row[invkey] for row in rows)-shared)>1e-6:
            raise p.Rejected('inconsistent prior shared resource accounting')
    for row in rows:
        for charged,invocation,shared in [('charged_wall_seconds','invocation_wall_seconds',shared_wall),('charged_cpu_seconds','invocation_cpu_seconds',shared_cpu)]:
            if (not q.finite_nonnegative(row.get(invocation)) or not q.finite_nonnegative(row.get(charged))
                    or abs(row[charged]-row[invocation]-shared)>1e-6):
                raise p.Rejected('prior charged resource arithmetic differs')
        if row.get('accepted') and not all(row[key]<=BUDGET for key in ('charged_wall_seconds','charged_cpu_seconds')):
            raise p.Rejected('prior accepted arm exceeds charged caps')
    b2,crow=rows
    bsummary=read_bound(prior/'B2_portfolio/portfolio-summary.json',bindings)
    verified=paired.verify_portfolio(prior/'B2_portfolio',bsummary,board,old)
    for key in ('result_sha256','selected','pareto_frontier','trials'):
        if b2.get(key)!=verified.get(key):raise p.Rejected('prior portfolio index is inconsistent')
    if b2.get('accepted') and not verified['accepted']:raise p.Rejected('prior B2 receipt not accepted')
    for trial in bsummary.get('trials',[]):
        if trial.get('result'):
            data=read_bound(Path(trial['result']),bindings)
            if p.sha(trial['result'])!=trial['result_sha256']:raise p.Rejected('prior trial receipt changed')
            if trial.get('eligible'):
                for name in ('candidate','native_report_sha256'):
                    if data.get(name)!=trial.get(name):raise p.Rejected('prior trial binding differs')
                bindings[data['candidate']]=data['candidate_sha256']
                bindings[str(Path(trial['result']).parent/'final-drc.json')]=data['native_report_sha256']
    cpath=prior/'C_thermal/result.json';cresult=read_bound(cpath,bindings)
    if crow.get('result_sha256')!=bindings[str(cpath)]:raise p.Rejected('prior C receipt changed')
    if cresult.get('tools')!=old['tools'] or cresult.get('source_hashes')!=old['source_hashes']:
        raise p.Rejected('prior C source/tool provenance differs')
    if crow.get('accepted'):
        current=p.check_result(cpath)
        paired.verify_thermal_incumbent(prior/'C_thermal',cresult,board,old)
        if (cresult.get('accepted') is not True or cresult.get('strategy')!=paired.THERMAL_ARM['strategy']
                or crow.get('candidate_sha256')!=current['candidate_sha256']
                or crow.get('native_report_sha256')!=cresult.get('native_report_sha256')
                or crow.get('vias')!=cresult['metrics']['vias'] or crow.get('length_mm')!=cresult['metrics']['track_length_mm']):
            raise p.Rejected('prior accepted C summary differs from native receipt')
        bindings[current['candidate']]=current['candidate_sha256']
        bindings[str(cpath.parent/'final-drc.json')]=cresult['native_report_sha256']
    unchanged(bindings)
    if p.tree_hash(prior)!=prior_inventory:raise p.Rejected('prior evidence tree changed during verification')
    return {'prior_tree_sha256':prior_inventory,'prior_directory':str(prior),'prior_git_head':old['tools']['git_head'],'current_git_head':frozen['tools']['git_head'],
            'production_source_tools_and_existing_protocol_bytes_equal':True,'allowed_provenance_difference':'Git HEAD and addition of this harness only',
            'comparison_kind':'separate sequential runs with exact production/source/tool byte equality, not a new paired randomization',
            'results':copy.deepcopy(rows),'bound_files_sha256':bindings}


def verify_arm(arm,directory,data,board,frozen):
    if (data.get('tools')!=frozen['tools'] or data.get('source_hashes')!=frozen['source_hashes']
            or data.get('source')!=str(board) or data.get('budget_seconds')!=BUDGET
            or data.get('cpu_budget_seconds')!=BUDGET or data.get('scoring_variant') is not None
            or data.get('adapter')!=arm['adapter'] or data.get('engine_profile')!=arm['engine_profile']
            or data.get('scope')!='whole_board_unlocked_routing'):
        raise p.Rejected('arm source/constraints/profile/budget provenance differs')
    steps=[s for s in data.get('steps',[]) if s.get('name')=='engine']
    if not steps and not (directory/'engine-process.json').exists():
        if data.get('accepted') is True or data.get('status')=='drc_rejected' or (directory/'final-drc.json').exists():
            raise p.Rejected('native outcome has no retained engine execution')
        return {'engine_contract_verified':False,'engine_contract_scope':'failure before engine; no executed engine claim'}
    engine=data.get('engine_budget',{});left=engine.get('remaining_outer_wall_seconds_at_assignment')
    if not q.finite_nonnegative(left) or left>BUDGET:raise p.Rejected('invalid arm engine assignment')
    expected=p.engine_profile_settings(arm['engine_profile'],left,strict_class_targets=data.get('netclass_policy') is not None)
    if any(engine.get(k)!=v for k,v in expected.items()):raise p.Rejected('engine assigned settings differ')
    for key in ('outer_task_wall_budget_seconds','outer_task_cpu_budget_seconds'):
        if engine.get(key)!=BUDGET:raise p.Rejected('engine outer allowance differs')
    argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(c.JAVA),'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(c.JAR),'--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(directory/'engine-config'),'--logging.file.enabled=false',*expected['argv'],'-de',str(directory/'task.dsn'),'-do',str(directory/'routes.ses')]
    if (len(steps)!=1 or steps[0].get('argv')!=argv or steps[0].get('cwd')!=str(directory)
            or steps[0].get('cleanup_complete') is not True
            or json.loads((directory/'engine-process.json').read_text())!=steps[0]):raise p.Rejected('arm engine execution differs')
    for name,key in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
        if (directory/name).is_symlink() or p.sha(directory/name)!=data.get(key):raise p.Rejected('arm exported task differs')
    completed=steps[0].get('status')=='success' and steps[0].get('exit_code')==0
    if data.get('accepted') is True:
        if not completed:raise p.Rejected('accepted arm has unsuccessful engine execution')
        p.check_result(directory/'result.json')
    return {'engine_contract_verified':True,'engine_completed_successfully':completed,
            'engine_contract_scope':'actual invocation/options/exports verified, independent of native acceptance'}


def compare(rows,reference):
    system=next(row for row in reference['results'] if row['id']=='C_thermal')
    result=[]
    for row in rows:
        item={'baseline':row['id'],'system':'prior_C_thermal','baseline_accepted':row['accepted'],'C_accepted':system['accepted'],
              'completion_difference':int(system['accepted'])-int(row['accepted']),
              'interpretation':'separately charged policies; completion/profile/allocation effects are not a thermal-only ablation'}
        if row['accepted'] and system['accepted']:
            item.update(length_delta_mm=system['length_mm']-row['length_mm'],via_delta=system['vias']-row['vias'])
        result.append(item)
    return result


def experiment(out,prior,project_name='interf_u'):
    def interrupted(signum,frame):raise KeyboardInterrupt
    old={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        for sig in old:signal.signal(sig,interrupted)
        return _experiment(out,prior,project_name)
    finally:
        for sig,handler in old.items():signal.signal(sig,handler)


def _experiment(out,prior,project_name):
    start,cpu_start=time.monotonic(),q.total_process_cpu()
    out=Path(out).resolve();prior=Path(prior).absolute()
    if c.ROOT/'.runs' not in out.parents or c.ROOT/'.runs' not in prior.parents:raise p.Rejected('outputs and prior pair must be project-local .runs')
    if out==prior or prior in out.parents or out in prior.parents:raise p.Rejected('new output and prior evidence must be disjoint')
    out.mkdir(parents=True,exist_ok=False)
    summary={'schema':1,'status':'incomplete','kind':'thermal_comparator_ablation','started_utc':utc(),'results':[],'comparisons':[],
             'claims_limit':'one exposed family, separate frozen runs, no broad completion/novelty/electrical claim'}
    frozen=reference=board=None
    artifact_trees={};immutable_files={}
    def stable():
        unchanged(immutable_files)
        for name,inventory in artifact_trees.items():
            if p.tree_hash(Path(name))!=inventory:raise p.Rejected('completed arm or frozen-code evidence changed: '+name)
        if frozen is not None:q.verify_freeze(frozen,board)
        if reference is not None:
            unchanged(reference['bound_files_sha256'])
            if p.tree_hash(Path(reference['prior_directory']))!=reference['prior_tree_sha256']:
                raise p.Rejected('prior candidate project/native input/evidence tree changed')
    def account():
        summary.update(batch_wall_seconds=time.monotonic()-start,batch_cpu_seconds=q.total_process_cpu()-cpu_start,finished_utc=utc())
        sw=summary['batch_wall_seconds']-sum(r.get('invocation_wall_seconds',0) for r in summary['results'])
        sc=summary['batch_cpu_seconds']-sum(r.get('invocation_cpu_seconds',0) for r in summary['results'])
        summary.update(shared_overhead_wall_seconds=sw,shared_overhead_cpu_seconds=sc)
        for row in summary['results']:
            wall=row['invocation_wall_seconds']+sw;cpu=row['invocation_cpu_seconds']+sc
            within=all(q.finite_nonnegative(x) and x<=BUDGET for x in (wall,cpu))
            row.update(charged_wall_seconds=wall,charged_cpu_seconds=cpu,within_charged_budgets=within,
                       accepted=row['accepted_before_shared_charge'] and within and summary['status']=='completed')
        summary['comparisons']=compare(summary['results'],reference) if summary['status']=='completed' and reference else []
    def rejected_publication(exc):
        # Clear the canonical positive index before any correction write can fail.
        for path in (out/'summary.json',out/'summary.json.partial'):
            if path.exists():path.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+path.name))
        summary.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',reason=type(exc).__name__+': '+str(exc),comparisons=[])
        for row in summary['results']:row['accepted_before_shared_charge']=False;row['accepted']=False
        account();p.save_json(out/'summary.json',summary)
    try:
        p.check_storage();board,family=q.selected_source(project_name);frozen=freeze(board)
        reference=cross_bind(prior,board,frozen)
        (out/'frozen-code').mkdir()
        for name,digest in frozen['files_sha256'].items():
            dest=out/'frozen-code'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(c.ROOT/name,dest)
            if p.sha(dest)!=digest:raise p.Rejected('code changed during freeze copy')
        protocol={'schema':1,'freeze':frozen,'family':family,'source':str(board),'arms':list(ARMS),'prior_pair':reference,
                  'wall_budget_per_arm_seconds':BUDGET,'cpu_budget_per_arm_seconds':BUDGET,'fixed_order':True,
                  'accounting':'entire measured shared setup, prior-check, freeze/copy and final-publication overhead charged to EACH new arm; prior arms retain their original charges',
                  'cpu_enforcement':'measured acceptance cap, not OS preemption','prior_cost':'prior B2/C are not rerun or used as candidate input; historical charges retained, new verification charged to new arms',
                  'interpretation':'B0/B1 isolates representation; completion-only isolates profile/allocation; prior C comparison does not by itself isolate thermal repair',
                  'editor_policy':'operator closes PCB Editor and keeps other native/engine jobs idle','claims_limit':summary['claims_limit']}
        p.save_json(out/'protocol.json',protocol);summary.update(protocol_sha256=p.sha(out/'protocol.json'),prior_pair=reference)
        immutable_files[str(out/'protocol.json')]=summary['protocol_sha256']
        artifact_trees[str(out/'frozen-code')]=p.tree_hash(out/'frozen-code')
        for arm in ARMS:
            row={**arm,'status':'invocation_error','accepted':False,'accepted_before_shared_charge':False,'started_utc':utc(),'host_load_average_1_5_15_minutes_begin':list(os.getloadavg())}
            summary['results'].append(row);wall0,cpu0=time.monotonic(),q.total_process_cpu();directory=out/arm['id']
            try:
                stable();data=p.route(board,directory,BUDGET,False,arm['adapter'],arm['engine_profile'])
                if q.cancelled(data):raise KeyboardInterrupt
                contract=verify_arm(arm,directory,data,board,frozen)
                row.update(contract)
                row.update(q.summarize(arm,directory,data,time.monotonic()-wall0,q.total_process_cpu()-cpu0))
                artifact_trees[str(directory)]=p.tree_hash(directory)
                stable()
            except KeyboardInterrupt:
                row.update(accepted=False,status='cancelled');raise
            except Exception as exc:
                row.update(accepted=False,status='invocation_error',reason=type(exc).__name__+': '+str(exc));stable()
            finally:
                row.update(invocation_wall_seconds=time.monotonic()-wall0,invocation_cpu_seconds=q.total_process_cpu()-cpu0,finished_utc=utc(),host_load_average_1_5_15_minutes_end=list(os.getloadavg()))
                row['accepted_before_shared_charge']=row['accepted'] and all(q.finite_nonnegative(row[k]) and row[k]<=BUDGET for k in ('invocation_wall_seconds','invocation_cpu_seconds'))
                p.save_json(out/(arm['id']+'-invocation.json'),row)
        stable();summary['status']='completed'
        summary['completed_arm_and_frozen_code_trees']=copy.deepcopy(artifact_trees)
    except KeyboardInterrupt as exc:
        summary.update(status='cancelled',reason='interrupted ablation')
    except Exception as exc:
        summary.update(status='invalidated',reason=type(exc).__name__+': '+str(exc))
    summary['accounting_point']='stored totals precede final summary write/freshness check; acceptance caps checked after both; correction may finish outside cap'
    try:
        stable();account();p.save_json(out/'summary.json',summary)
        if json.loads((out/'summary.json').read_text())!=summary:raise p.Rejected('final summary differs from emitted record')
        before=[r['accepted'] for r in summary['results']]
        stable();account()
        if before!=[r['accepted'] for r in summary['results']]:
            rejected_publication(p.Rejected('final publication crossed charged acceptance cap'))
    except (Exception,KeyboardInterrupt) as exc:rejected_publication(exc)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--prior-pair',required=True)
    parser.add_argument('--project',choices=tuple(q.PROJECTS),default='interf_u');args=parser.parse_args()
    lock=c.ROOT/'.runs/quality-experiment.lock';lock.parent.mkdir(exist_ok=True)
    if lock.is_symlink():parser.error('experiment lock cannot be a symlink')
    with lock.open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        data=experiment(Path(args.output),Path(args.prior_pair),args.project)
    print(json.dumps({'status':data['status'],'summary':str(Path(args.output)/'summary.json')}))
    return 0 if data['status']=='completed' else 2

if __name__=='__main__':raise SystemExit(main())
