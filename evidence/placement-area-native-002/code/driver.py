"""Falsify the placement-node explanation for actual001 native DRC omissions.

Explicit --run-native required. One 60-second wall/CPU cap; export + native DRC
only, never an engine or adapter transformation. Deliberately invalid fixtures
are diagnostic material, not corpus inputs or routing candidates.
"""
from __future__ import annotations
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import signal
import sys
import time
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT),str(HERE)]
from autorouter import config as c,pipeline as p,floor_route as f,sexpr as sx
import fixture_recipe as recipe
import native_areas as worker
import support as s

FAILED=ROOT/'.runs/placement-area-native-001'
SOURCE_SUMMARY_SHA='c61d54b5508f0508528e1236ead7bf97ad21ef336e32448994c6239db56b058f'
SECONDS=60
HELPERS=('driver.py','fixture_recipe.py','native_areas.py','support.py','test_driver.py')
WRAPPER=c.PYTHON.parent.parent/'lib/python3.9/site-packages/pcbnew.py'


def native_expected(case,native,expected,ignored):
    for key in ('opens','blocking','warnings','exclusions'):
        if type(native.get(key)) is not int or native[key]<0:return False,[]
    if native['opens'] or native['warnings'] or native['exclusions'] or native.get('ignored_checks')!=ignored:
        return False,[]
    findings=native.get('findings')
    if not isinstance(findings,list):return False,[]
    targets=set(expected['prohibited_target_uuids'])
    if not targets:return p.native_accepted(native) and not findings,[]
    hits=[];seen=set()
    for row in findings:
        if not isinstance(row,dict) or row.get('type')!='items_not_allowed' or row.get('severity')!='error' or row.get('excluded',False):return False,[]
        items=row.get('items')
        if not isinstance(items,list) or any(not isinstance(x,dict) for x in items):return False,[]
        intersect=targets & {x.get('uuid') for x in items}
        if not intersect:return False,[]
        seen.update(intersect);hits.append(row)
    return seen==targets and bool(hits) and not p.native_accepted(native),hits


def audit_context(job,board,observed,expected,dsn,code):
    before=p.tree_hash(board.parent)
    if (observed.get('source')!=str(board) or observed.get('board_sha256')!=p.sha(board)
            or observed.get('project_sha256')!=p.sha(board.with_suffix('.kicad_pro')) or observed.get('dsn_sha256')!=p.sha(dsn)
            or observed.get('input_hashes_before')!=before or observed.get('input_hashes_after')!=before
            or observed.get('limits')!=worker.LIMITS):raise p.Rejected('native area source/project/export binding differs')
    verdict=recipe.verify_observation(observed,expected)
    argv=[*f.SANDBOX,str(c.PYTHON),'-B',str(code/'native_areas.py'),str(board),str(job.out/'areas.json'),str(dsn)]
    f.process_check(job.out,{'steps':job.steps},'area-export',argv)
    return verdict


def omission_expected(native,old_native):
    """A matching omission is a diagnostic observation, never constraint acceptance."""
    return (p.native_accepted(native) and not native['findings'] and
            native['ignored_checks']==old_native['ignored_checks'] and
            all(type(native.get(k))is int and native[k]==0 for k in ('opens','blocking','warnings','exclusions')))


def audit_recorded_evidence(root,data):
    """Check recorded historical evidence before adopting any current tree freeze."""
    root=s.owned(root)
    names=('allowed_placement',*recipe.CASES)
    recorded=data.get('completed_evidence');freeze=data.get('freeze')
    if not isinstance(recorded,dict) or set(recorded)!={str(root/name) for name in names} or not isinstance(freeze,dict):
        raise p.Rejected('actual001 recorded evidence population differs')
    for name in ('fixtures','code'):
        if not isinstance(freeze.get(name),dict) or p.tree_hash(s.owned(root/name))!=freeze[name]:
            raise p.Rejected('actual001 recorded '+name+' inventory changed')
    for name in names:
        path=s.owned(root/name);expected=recorded[str(path)]
        if not isinstance(expected,dict) or p.tree_hash(path)!=expected:
            raise p.Rejected('actual001 recorded case evidence changed: '+name)


def baseline():
    s.owned(FAILED)
    if p.sha(FAILED/'summary.json')!=SOURCE_SUMMARY_SHA:raise p.Rejected('actual001 receipt changed')
    data=f.read_json(FAILED/'summary.json')
    if data.get('status')!='completed' or data.get('controls_passed') is not False:raise p.Rejected('actual001 must remain failed controls')
    audit_recorded_evidence(FAILED,data)
    selected={}
    for case in recipe.CASES:
        rows=[r for r in data['cases'] if r['case']==case]
        if len(rows)!=1:raise p.Rejected('actual001 case denominator differs')
        row=rows[0];source=s.owned(FAILED/'fixtures'/case/'fixture.kicad_pcb')
        if row['source']!=str(source) or p.tree_hash(source.parent)!=row['source_hashes'] or p.sha(source)!=row['board_sha256']:
            raise p.Rejected('actual001 fixture source changed')
        if row['passed'] is not False or not row['expected']['prohibited_target_uuids'] or not omission_expected(row['native'],row['native']):
            raise p.Rejected('actual001 omitted negative finding differs')
        selected[case]=row
    return selected


def unsupported(board):
    try:p.preflight(board)
    except p.Rejected as exc:
        if 'rule-area restrictions not qualified by pinned native validator' not in str(exc):raise
        return {'supported':False,'reason':str(exc),'native_diagnostic_only':True}
    raise p.Rejected('production guard unexpectedly accepts genuine rule-area restriction')


def experiment(out,*,run_native=False):
    if run_native is not True:raise p.Rejected('explicit --run-native required')
    started=time.monotonic();cpu0=s.cpu();out=s.owned(out,exists=False)
    if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('fresh direct .runs output required')
    out.mkdir();steps=[];completed={};freeze=None
    record={'schema':1,'status':'running','controls_passed':False,'routing_accepted':False,'comparison_eligible':False,
            'adapter_policy_qualified':False,'constraint_qualification_passed':False,'adapter_transformation_performed':False,'engine_executed':False,
            'diagnostic_kind':'placement_node_removal_omission_falsification',
            'claims_limit':'controls_passed means omission reproduced after removing only placement metadata; genuine constraints remain unqualified and production unsupported',
            'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,
            'predeclared_cases':list(recipe.CASES),'cases':[],'steps':steps,'fixture_scope':'Copies of actual001 negative fixtures; deliberately invalid geometry retained; no corpus promotion.',
            'accounting_point':'Stored totals precede final publication/freshness; actual wall and parent+waited-child CPU ceilings include those checks.'}
    def remaining():return max(0,min(started+SECONDS-time.monotonic(),SECONDS-(s.cpu()-cpu0)))
    def account():
        record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=s.cpu()-cpu0,native_executed=bool(steps),
                      native_step_cpu_seconds=sum(x.get('cpu_seconds') or 0 for x in steps),monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds') or 0 for x in steps))
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
        if not record['within_budget']:record['controls_passed']=False
    def stable():
        if freeze is None:return
        if p.tree_hash(FAILED)!=freeze['actual001']:raise p.Rejected('original failed native001 evidence changed')
        if p.tool_manifest()!=freeze['tools'] or p.sha(WRAPPER)!=freeze['pcbnew_wrapper_sha256']:raise p.Rejected('current core/tool/HEAD/wrapper changed')
        if any(p.sha(s.owned(HERE/name))!=digest for name,digest in freeze['helpers'].items()) or p.tree_hash(out/'code')!=freeze['code']:
            raise p.Rejected('frozen diagnostic code changed')
        for path,inventory in completed.items():
            if p.tree_hash(Path(path))!=inventory:raise p.Rejected('completed diagnostic evidence changed')
    try:
        p.check_storage();old=baseline();original_tree=p.tree_hash(FAILED);tools=p.tool_manifest()
        helpers={name:p.sha(s.owned(HERE/name)) for name in HELPERS};(out/'code').mkdir();(out/'fixtures').mkdir()
        for name in HELPERS:shutil.copy2(HERE/name,out/'code'/name)
        for relative,digest in tools['implementation_sha256'].items():
            dest=out/'code'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,dest)
            if p.sha(dest)!=digest:raise p.Rejected('current core changed during snapshot')
        freeze={'actual001':original_tree,'tools':tools,'helpers':helpers,'code':p.tree_hash(out/'code'),'pcbnew_wrapper_sha256':p.sha(WRAPPER)}
        record.update(freeze=freeze,actual001_summary_sha256=SOURCE_SUMMARY_SHA)
        for case in recipe.CASES:
            stable()
            if remaining()<=0:raise p.Rejected('shared diagnostic budget exhausted')
            prior=s.owned(Path(old[case]['source']));source=out/'fixtures'/case/prior.name
            shutil.copytree(prior.parent,source.parent)
            encoded,expected,removed=recipe.prepare(case,prior.read_bytes(),old[case]['expected']);source.write_bytes(encoded)
            expected_files=dict(old[case]['source_hashes']);expected_files[source.name]=expected['board_sha256']
            if p.tree_hash(source.parent)!=expected_files:raise p.Rejected('diagnostic copy changed files besides expected board')
            scope=unsupported(source);completed[str(source.parent)]=expected_files
            entry={'case':case,'source':str(source),'source_hashes':expected_files,'expected':expected,'removed_placement_nodes':removed,
                   'production_scope':scope,'passed':False,'routing_accepted':False,'constraint_qualification_passed':False};record['cases'].append(entry)
            job=s.SharedJob(out/case,remaining,steps)
            try:
                shutil.copytree(source.parent,job.out/'candidate');board=job.out/'candidate'/source.name;dsn=job.out/'native.dsn'
                job.step('area-export',[c.PYTHON,'-B',out/'code/native_areas.py',board,job.out/'areas.json',dsn])
                observed=f.read_json(job.out/'areas.json');entry['area_observation']=observed
                entry['native_context_audit']=audit_context(job,board,observed,expected,dsn,out/'code')
                entry['export_keepout_audit']=recipe.verify_dsn(dsn.read_bytes(),expected)
                native=job.drc('diagnostic-drc',board);entry['native']=native;entry['native_binding']=s.check_drc(job,'diagnostic-drc',board,native)
                actual_rejection,hits=native_expected(case,native,expected,old[case]['native']['ignored_checks'])
                if p.tree_hash(board.parent)!=expected_files:raise p.Rejected('native stage changed copied fixture')
                entry.update(passed=omission_expected(native,old[case]['native']),omission_reproduced=omission_expected(native,old[case]['native']),
                             native_rejected_known_invalid_constraint=actual_rejection,targeted_native_findings=hits,
                             native_dsn_sha256=p.sha(dsn),area_context_sha256=p.sha(job.out/'areas.json'),board_sha256=p.sha(board),source_unchanged=True)
            except Exception as exc:entry.update(error=type(exc).__name__+': '+str(exc))
            p.save_json(job.out/'case.json',entry);completed[str(job.out)]=p.tree_hash(job.out)
        stable();record.update(status='completed',controls_passed=len(record['cases'])==len(recipe.CASES) and all(x['passed'] for x in record['cases']),
                               original_actual001_unchanged=True,completed_evidence=completed)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    return s.publish(out,record,stable,account)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--run-native',action='store_true');args=parser.parse_args(argv)
    if not args.run_native:parser.error('--run-native required; native work not executed')
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,interrupted)
        with s.owned(ROOT/'.runs/quality-experiment.lock',exists=False).open('a') as stream:
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.out,run_native=True)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    print(json.dumps({'status':result['status'],'omission_controls_passed':result['controls_passed'],'constraint_qualification':False,'output':str(args.out)}))
    return 0 if result['controls_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
