"""Observe placement-area/native-keepout behavior on four owned fixtures.

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

POSITIVE=ROOT/'.runs/board-floor-production-native-001/result.json'
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


def experiment(out,*,run_native=False):
    if run_native is not True:raise p.Rejected('explicit --run-native required')
    started=time.monotonic();cpu0=s.cpu();out=s.owned(out,exists=False)
    if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('fresh direct .runs output required')
    out.mkdir();steps=[];completed={};freeze=None
    record={'schema':1,'status':'running','controls_passed':False,'routing_accepted':False,'comparison_eligible':False,
            'adapter_policy_qualified':False,'adapter_transformation_performed':False,'engine_executed':False,
            'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,
            'cases':[],'steps':steps,'fixture_scope':'Owned exposed diagnostic derivatives; genuine prohibition cases deliberately invalid; no corpus promotion.',
            'accounting_point':'Stored totals precede final publication/freshness checks; acceptance wall/CPU cap includes those checks. Corrective rejection can finish outside cap.',
            'resource_limits':'One foreground native worker; measured parent+waited-child CPU cap, bounded runner RSS/disk/log guards; no OS aggregate CPU quota.'}
    def remaining():return max(0,min(started+SECONDS-time.monotonic(),SECONDS-(s.cpu()-cpu0)))
    def account():
        record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=s.cpu()-cpu0,native_executed=bool(steps),
                      native_step_cpu_seconds=sum(x.get('cpu_seconds') or 0 for x in steps),monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds') or 0 for x in steps))
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
        if not record['within_budget']:record['controls_passed']=False
    def stable():
        if freeze is None:return
        if p.tree_hash(POSITIVE.parent)!=freeze['positive'] or p.tree_hash(original_source.parent)!=freeze['original_source']:
            raise p.Rejected('accepted original input/evidence changed')
        if p.tree_hash(HERE/'fixtures')!=freeze['fixtures'] or p.tree_hash(out/'fixtures')!=freeze['fixtures']:
            raise p.Rejected('own source fixtures changed')
        if p.tool_manifest()!=freeze['tools'] or p.sha(WRAPPER)!=freeze['pcbnew_wrapper_sha256'] or p.tree_hash(out/'code')!=freeze['code']:
            raise p.Rejected('code/tool/native-wrapper/HEAD changed')
        if any(p.sha(s.owned(HERE/name))!=digest for name,digest in freeze['helpers'].items()):raise p.Rejected('control helper changed')
        for path,inventory in completed.items():
            if p.tree_hash(Path(path))!=inventory:raise p.Rejected('completed native evidence changed')
    try:
        p.check_storage();s.owned(POSITIVE);positive_tree=p.tree_hash(POSITIVE.parent);p.check_result(POSITIVE)
        positive=f.read_json(POSITIVE);base=s.owned(positive['candidate']);original_source=s.owned(positive['source'])
        if p.sha(base)!=recipe.BASE_SHA or p.sha(base.with_suffix('.kicad_pro'))!=recipe.PROJECT_SHA:
            raise p.Rejected('accepted base candidate/project changed')
        if not p.native_accepted(positive['native']) or positive['native']['findings']:raise p.Rejected('base must be native clean')
        tools=p.tool_manifest()
        if tools['implementation_sha256']!=positive['tools']['implementation_sha256'] or tools['files']!=positive['tools']['files']:
            raise p.Rejected('current core/tool files differ from qualified base')
        helpers={name:p.sha(s.owned(HERE/name)) for name in HELPERS}
        fixture_hashes=p.tree_hash(HERE/'fixtures');shutil.copytree(HERE/'fixtures',out/'fixtures');(out/'code').mkdir()
        for name in HELPERS:shutil.copy2(HERE/name,out/'code'/name)
        for relative,digest in tools['implementation_sha256'].items():
            dest=out/'code'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,dest)
            if p.sha(dest)!=digest:raise p.Rejected('core changed during freeze')
        freeze={'positive':positive_tree,'original_source':p.tree_hash(original_source.parent),'fixtures':fixture_hashes,'tools':tools,
                'pcbnew_wrapper_sha256':p.sha(WRAPPER),'helpers':helpers,'code':p.tree_hash(out/'code')}
        record.update(freeze=freeze,positive_result_sha256=p.sha(POSITIVE),base_candidate_sha256=recipe.BASE_SHA,original_project_sha256=recipe.PROJECT_SHA)
        stable()
        for case in recipe.CASES:
            stable()
            if remaining()<=0:raise p.Rejected('global native diagnostic cap exhausted')
            source=out/'fixtures'/case/base.name;board_bytes,expected=recipe.prepare(case,base.read_bytes())
            expected_files=dict(p.tree_hash(base.parent));expected_files[base.name]=expected['board_sha256']
            if source.read_bytes()!=board_bytes or p.tree_hash(source.parent)!=expected_files:raise p.Rejected('prepared complete fixture differs from exact recipe')
            p.preflight(source)
            entry={'case':case,'source':str(source),'source_hashes':expected_files,'expected':expected,'passed':False};record['cases'].append(entry)
            job=s.SharedJob(out/case,remaining,steps)
            try:
                shutil.copytree(source.parent,job.out/'candidate');board=job.out/'candidate'/base.name;dsn=job.out/'native.dsn'
                job.step('area-export',[c.PYTHON,'-B',out/'code/native_areas.py',board,job.out/'areas.json',dsn])
                observed=f.read_json(job.out/'areas.json');entry['area_observation']=observed
                entry['native_context_audit']=audit_context(job,board,observed,expected,dsn,out/'code')
                entry['export_keepout_audit']=recipe.verify_dsn(dsn.read_bytes(),expected)
                native=job.drc('diagnostic-drc',board);entry['native']=native
                entry['native_binding']=s.check_drc(job,'diagnostic-drc',board,native)
                ok,hits=native_expected(case,native,expected,positive['native']['ignored_checks'])
                if p.tree_hash(board.parent)!=expected_files or p.tree_hash(source.parent)!=expected_files:
                    raise p.Rejected('native stage changed source/candidate/rules')
                entry.update(passed=ok,targeted_native_findings=hits,native_dsn_sha256=p.sha(dsn),area_context_sha256=p.sha(job.out/'areas.json'),
                             board_sha256=p.sha(board),source_unchanged=True,project_sha256=p.sha(board.with_suffix('.kicad_pro')))
            except Exception as exc:entry.update(error=type(exc).__name__+': '+str(exc))
            p.save_json(job.out/'case.json',entry);completed[str(job.out)]=p.tree_hash(job.out)
        stable();record.update(status='completed',controls_passed=len(record['cases'])==len(recipe.CASES) and all(x['passed'] for x in record['cases']),
                               original_inputs_unchanged=True,completed_evidence=completed)
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
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.out,run_native=True)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    print(json.dumps({'status':result['status'],'controls_passed':result['controls_passed'],'output':str(args.out)}))
    return 0 if result['controls_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
