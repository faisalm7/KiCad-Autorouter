"""Five bounded real-native controls of the placement guidance floor contract.

Requires --run-native and a fresh accepted production receipt; never calls an engine. All cases share 60s
wall and parent + waited-child CPU. These controls do not route a new board,
establish broad support, or qualify physical/electrical suitability.
"""
from __future__ import annotations
import argparse
import copy
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import sys
import subprocess
import time
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
from autorouter import config as c,pipeline as p,sexpr as sx,floor_route as f

POLICY='placement-clearance-v1'
FIXTURE=ROOT/'evidence/placement-area-native-001/allowed_placement/candidate/fixture.kicad_pcb'
PURE_POSITIVE=ROOT/'.runs/placement-search-fixture-001/result.json'
CASES=('positive','narrow_track','small_via','missing_via','changed_rule')
POLICY_FILES=('floor-policy.json','floor-export-context.json','native.dsn','floor-guided.dsn')
SECONDS=60
CONTRACT_REASONS={'narrow_track':'generated track differs from derived guidance',
                  'small_via':'generated via differs from derived guidance/floor',
                  'changed_rule':'native context/source/DSN byte binding mismatch'}



def committed_sources():
    """Reject uncommitted implementation, tool pins, or control helpers before native work."""
    paths=[*sorted((ROOT/'autorouter').glob('*.py')),ROOT/'toolchain.lock.json',HERE/'driver.py',HERE/'test_driver.py']
    for path in paths:
        relative=str(owned(path).relative_to(ROOT))
        result=subprocess.run(['git','show','HEAD:'+relative],cwd=ROOT,capture_output=True,timeout=5,check=True)
        if result.stdout!=path.read_bytes():raise p.Rejected('control source differs from committed HEAD: '+relative)


def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime


def owned(path,*,exists=True):
    path=Path(path).absolute()
    if '..' in path.parts or not path.is_relative_to(ROOT) or any(x.is_symlink() for x in (path,*path.parents)):
        raise p.Rejected('path must be a real path inside this checkout')
    if exists and not path.exists():raise p.Rejected('missing owned input')
    return path


def uid(node):
    value=sx.one(node,'uuid')
    if value is None or len(value)!=2:raise p.Rejected('missing route UUID')
    return sx.unquote(value[1])


def xy(node,key):return tuple(float(x) for x in sx.one(node,key)[1:3])


def prepare(case,board_bytes,project_bytes):
    """Exact one-field/one-object mutations; never modify caller's inputs."""
    if case not in CASES:raise p.Rejected('unknown case')
    original=sx.parse(board_bytes.decode());tree=copy.deepcopy(original)
    routes=p.routes(tree);ids=[uid(x) for x in routes]
    if len(ids)!=len(set(ids)) or not routes:raise p.Rejected('ambiguous or missing generated routes')
    vias=[x for x in routes if x[0]=='via'];segments=[x for x in routes if x[0]=='segment']
    if len(vias)!=1 or not segments or any(x[0] not in {'segment','via'} or p.locked(x) for x in routes):
        raise p.Rejected('control requires exactly one unlocked through via and segments')
    via=vias[0]
    if (sx.one(via,'layers')!=['layers','"F.Cu"','"B.Cu"'] or sx.one(via,'size')!=['size','1.5']
            or sx.one(via,'drill')!=['drill','0.3'] or sx.unquote(sx.one(via,'net')[1])!='SIGNAL_A'):
        raise p.Rejected('unexpected qualified via geometry/net')
    adjacent=[x for x in segments if sx.one(x,'net')==sx.one(via,'net') and xy(via,'at') in (xy(x,'start'),xy(x,'end'))]
    if {sx.unquote(sx.one(x,'layer')[1]) for x in adjacent}!={'F.Cu','B.Cu'}:
        raise p.Rejected('required via does not join both copper sides')
    target=max(segments,key=lambda x:(math.dist(xy(x,'start'),xy(x,'end')),uid(x)))
    if sx.one(target,'width')!=['width','0.3']:raise p.Rejected('unexpected qualified segment width')
    project=json.loads(project_bytes);settings=project['board']['design_settings']['rule_severities']
    if settings.get('track_width')!='error':raise p.Rejected('original width severity differs')
    expected={'case':case,'positive_via_uuid':uid(via),'adjacent_route_uuids':sorted(uid(x) for x in adjacent),'changed_project':False,'target_uuid':None,'field':None}
    if case=='narrow_track':
        sx.one(target,'width')[1]='0.2';expected.update(target_uuid=uid(target),field='width',old='0.3',new='0.2')
    elif case=='small_via':
        sx.one(via,'size')[1]='0.6';expected.update(target_uuid=uid(via),field='size',old='1.5',new='0.6')
    elif case=='missing_via':
        tree.remove(via);expected.update(target_uuid=uid(via),field='remove_exact_via')
    elif case=='changed_rule':
        settings['track_width']='warning';expected.update(changed_project=True,field='board.design_settings.rule_severities.track_width',old='error',new='warning')
    if p.immutable(tree)!=p.immutable(original):raise p.Rejected('mutation changed immutable board geometry')
    board_out=board_bytes if case in ('positive','changed_rule') else (sx.dump(tree)+'\n').encode()
    project_out=project_bytes if case!='changed_rule' else (json.dumps(project,indent=2)+'\n').encode()
    expected.update(board_sha256=hashlib.sha256(board_out).hexdigest(),project_sha256=hashlib.sha256(project_out).hexdigest())
    return board_out,project_out,expected


def diagnostic_pass(case,native,expected,ignored):
    """Strict expected native observations, independent from production checks."""
    # Parse's schema/policy validation must not be replaced by truthiness checks.
    for key in ('opens','blocking','warnings','exclusions'):
        if type(native.get(key)) is not int or native[key]<0:return False,[]
    if native.get('ignored_checks')!=ignored or native['exclusions'] or not isinstance(native.get('findings'),list):return False,[]
    if case in ('positive','changed_rule'):
        return p.native_accepted(native) and native['warnings']==0 and not native['findings'],[]
    if case=='missing_via':
        required=set(expected['adjacent_route_uuids'])
        hits=[row for row in native['findings'] if row.get('type')=='unconnected_items' and row.get('severity')=='error'
              and not row.get('excluded',False) and required<={x.get('uuid') for x in row.get('items',[])}]
        return native['opens']>0 and not p.native_accepted(native) and bool(hits),hits
    kind={'narrow_track':'track_width','small_via':'via_diameter'}[case]
    hits=[row for row in native['findings'] if row.get('type')==kind and row.get('severity')=='error'
          and not row.get('excluded',False) and expected['target_uuid'] in {x.get('uuid') for x in row.get('items',[])}]
    return native['opens']==0 and not p.native_accepted(native) and bool(hits),hits


class SharedJob(f.FloorJob):
    def __init__(self,out,remaining,steps):
        available=remaining()
        if available<=0:raise p.Rejected('shared diagnostic budget exhausted')
        self.all_steps=steps
        super().__init__(out,available,remaining)
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        before=len(self.steps)
        try:return super().step(name,argv,allowed,already_sandboxed=already_sandboxed)
        finally:
            self.all_steps.extend(self.steps[before:])
            if any(x.get('status')=='cancelled' for x in self.steps[before:]):raise KeyboardInterrupt


def check_drc(job,name,board,native):
    """Bind actual raw report/process/copied native input to an exact candidate."""
    before=p.tree_hash(board.parent);path=job.out/(name+'-binding.json');binding=f.read_json(path)
    copied=job.out/(name+'-input')/board.name
    if binding.get('source')!=str(board) or binding.get('input')!=str(copied) or binding.get('saved') is not False or binding.get('before')!=before:
        raise p.Rejected('native candidate binding differs')
    after=binding.get('after')
    if not isinstance(after,dict) or any(after.get(k)!=v for k,v in before.items()) or set(after)-set(before)-{board.with_suffix('.kicad_prl').name}:
        raise p.Rejected('native copy/rules changed')
    if p.tree_hash(copied.parent)!=after or p.parse_report(job.out/(name+'.json'),board.name)!=native:
        raise p.Rejected('raw native report/input mismatch')
    expected=[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones',
              '--exit-code-violations','--output',str(job.out/(name+'.json')),str(copied)]
    f.process_check(job.out,{'steps':job.steps},name,expected,allowed=(5 if native['findings'] else 0,))
    return {'candidate_sha256':p.sha(board),'native_report_sha256':p.sha(job.out/(name+'.json')),'native_binding_sha256':p.sha(path),'input_hashes':after}


def publish(out,record,stable,account):
    """Never retain a canonical positive after failed final validation/write."""
    def archive():
        for path in (out/'summary.json',out/'summary.json.partial'):
            if path.exists():path.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+path.name))
    try:
        stable();account()
        if not record['within_budget']:raise p.Rejected('shared budget exceeded before publication')
        expected=f.canonical(record)
        p.save_json(out/'summary.json',record)
        if f.canonical(f.read_json(out/'summary.json'))!=expected:raise p.Rejected('summary changed during write')
        stable();account()
        if f.canonical(f.read_json(out/'summary.json'))!=expected:raise p.Rejected('summary changed during final check')
        if not record['within_budget']:raise p.Rejected('shared budget exceeded during publication')
    except (Exception,KeyboardInterrupt) as exc:
        archive();record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',controls_passed=False,
                                error=type(exc).__name__+': '+str(exc))
        account()
        try:p.save_json(out/'summary.json',record)
        except (Exception,KeyboardInterrupt):archive()
    return record


def experiment(out,*,positive=None,run_native=False):
    if run_native is not True:raise p.Rejected('explicit --run-native required')
    POSITIVE=owned(positive) if positive is not None else None
    if POSITIVE is None:raise p.Rejected('accepted production receipt required')
    start=time.monotonic();cpu0=cpu();out=owned(out,exists=False)
    if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('output must be a fresh direct .runs child')
    out.mkdir();steps=[];completed={};freeze=None
    record={'schema':1,'status':'running','controls_passed':False,'routing_accepted':False,'comparison_eligible':False,
            'new_engine_execution':False,'physical_electrical_validation':False,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'positive_result':str(POSITIVE),'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'cases':[],'steps':steps,
            'scope':'Five expected observations on a stored exposed production fixture; diagnostic and fresh production validator only.',
            'accounting_point':'Stored totals precede final summary write and freshness checks; final acceptance caps include both. Corrective rejection may finish outside cap.',
            'cpu_enforcement':'Measured total parent+waited-child acceptance cap and cooperative remaining timeout; not an OS aggregate quota.'}
    def remaining():return max(0,min(start+SECONDS-time.monotonic(),SECONDS-(cpu()-cpu0)))
    def account():
        record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=cpu()-cpu0,
                      native_executed=bool(steps),child_step_cpu_seconds=sum(x.get('cpu_seconds') or 0 for x in steps),
                      monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds') or 0 for x in steps))
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
        if not record['within_budget']:record['controls_passed']=False
    def stable():
        if freeze is None:return
        if p.tree_hash(POSITIVE.parent)!=freeze['positive'] or p.tree_hash(source.parent)!=freeze['source']:
            raise p.Rejected('positive evidence/source project changed')
        if p.tool_manifest()!=freeze['tools'] or p.tree_hash(out/'code')!=freeze['code']:
            raise p.Rejected('code/tool/HEAD snapshot changed')
        if p.tree_hash(out/'source')!=freeze['source'] or p.tree_hash(out/'positive-candidate')!=freeze['candidate']:
            raise p.Rejected('copied source/positive changed')
        if any(p.sha(owned(HERE/name))!=digest for name,digest in freeze['helpers'].items()):raise p.Rejected('diagnostic helper changed')
        for location,inventory in completed.items():
            if p.tree_hash(Path(location))!=inventory:raise p.Rejected('completed case evidence changed')
    try:
        p.check_storage();committed_sources();owned(POSITIVE);positive_before=p.tree_hash(POSITIVE.parent);p.check_result(POSITIVE)
        positive=f.read_json(POSITIVE);source=owned(positive['source']);candidate=owned(positive['candidate'])
        if source!=FIXTURE or positive['candidate_sha256']!=p.sha(candidate):
            raise p.Rejected('not the pinned accepted production fixture')
        if positive.get('input_policy')!=POLICY or positive.get('adapter')!='both' or positive.get('engine_profile')!='completion-only':
            raise p.Rejected('positive policy/profile differs')
        original=p.preflight(source);hashes=p.tree_hash(source.parent)
        if hashes!=positive['source_hashes'] or p.routes(original) or len(sx.children(original,'zone'))!=1:
            raise p.Rejected('expected original no-route/one-placement-area fixture differs')
        if positive['native']['findings'] or not p.native_accepted(positive['native']):raise p.Rejected('positive native report is not clean')
        tools=p.tool_manifest()
        if tools['implementation_sha256']!=positive['tools']['implementation_sha256'] or tools['files']!=positive['tools']['files']:
            raise p.Rejected('current implementation/tools differ from qualified positive')
        shutil.copytree(source.parent,out/'source');shutil.copytree(candidate.parent,out/'positive-candidate');(out/'code').mkdir()
        helpers={name:p.sha(owned(HERE/name)) for name in ('driver.py','test_driver.py')}
        for relative,digest in tools['implementation_sha256'].items():
            dest=out/'code'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(owned(ROOT/relative),dest)
            if p.sha(dest)!=digest:raise p.Rejected('source changed during code freeze')
        for name in helpers:shutil.copy2(HERE/name,out/'code'/name)
        freeze={'positive':positive_before,'source':hashes,'candidate':p.tree_hash(candidate.parent),'tools':tools,'helpers':helpers,'code':p.tree_hash(out/'code')}
        record.update(freeze=freeze,production_input_policy=POLICY,source=str(source),positive_result_sha256=p.sha(POSITIVE),positive_candidate_sha256=p.sha(candidate))
        stable();board_bytes=candidate.read_bytes();project_bytes=candidate.with_suffix('.kicad_pro').read_bytes()
        for case in CASES:
            stable()
            if remaining()<=0:raise p.Rejected('shared diagnostic budget exhausted')
            board_out,project_out,expected=prepare(case,board_bytes,project_bytes)
            case_out=out/case;case_out.mkdir();entry={'case':case,'passed':False,'expected':expected};record['cases'].append(entry)
            try:
                diagnostic=SharedJob(case_out/'diagnostic',remaining,steps)
                shutil.copytree(candidate.parent,diagnostic.out/'candidate');board=diagnostic.out/'candidate'/candidate.name
                board.write_bytes(board_out);board.with_suffix('.kicad_pro').write_bytes(project_out)
                native=diagnostic.drc('diagnostic-drc',board)
                entry['diagnostic_binding']=check_drc(diagnostic,'diagnostic-drc',board,native)
                entry['native']=native;ok,hits=diagnostic_pass(case,native,expected,positive['native']['ignored_checks'])
                entry.update(diagnostic_passed=ok,targeted_native_findings=hits)
                validation=SharedJob(case_out/'validation',remaining,steps)
                shutil.copytree(candidate.parent,validation.out/'candidate');board=validation.out/'candidate'/candidate.name
                board.write_bytes(board_out);board.with_suffix('.kicad_pro').write_bytes(project_out)
                for name in POLICY_FILES:shutil.copy2(POSITIVE.parent/name,validation.out/name)
                contract=f.read_json(validation.out/'floor-policy.json');entry['production_validation_invoked']=True
                try:
                    final,native_final=p.validate_candidate(validation,original,board,hashes,[],guidance_contract=contract)
                    entry.update(production_native=native_final,production_native_accepted=p.native_accepted(native_final),
                                 production_binding=check_drc(validation,'final-drc',board,native_final),candidate_sha256=final)
                    if native_final!=native:raise p.Rejected('separate production/diagnostic native observations differ')
                    if final!=expected['board_sha256']:raise p.Rejected('all-allowed-area control changed during finalization')
                    p.verify_candidate_files(board,hashes,final)
                    production_ok=(case=='positive' and p.native_accepted(native_final) and native_final['warnings']==0) or (
                        case=='missing_via' and diagnostic_pass(case,native_final,expected,positive['native']['ignored_checks'])[0])
                except (p.Rejected,ValueError) as exc:
                    reason=str(exc);entry.update(production_rejection=type(exc).__name__+': '+reason,production_native_accepted=False)
                    production_ok=case in CONTRACT_REASONS and reason==CONTRACT_REASONS[case] and not validation.steps
                entry.update(production_expected_outcome=production_ok,passed=ok and production_ok,production_steps=validation.steps)
            except Exception as exc:entry.update(error=type(exc).__name__+': '+str(exc))
            p.save_json(case_out/'case.json',entry);completed[str(case_out)]=p.tree_hash(case_out)
        stable();record.update(status='completed',controls_passed=len(record['cases'])==len(CASES) and all(x['passed'] for x in record['cases']),
                               original_inputs_unchanged=True,completed_evidence=completed)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    return publish(out,record,stable,account)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--run-native',action='store_true');parser.add_argument('--positive',required=True,type=Path);args=parser.parse_args(argv)
    if not args.run_native:parser.error('--run-native required; no native work performed')
    prior={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def cancelled(*_):raise KeyboardInterrupt
    try:
        for sig in prior:signal.signal(sig,cancelled)
        with owned(ROOT/'.runs/quality-experiment.lock',exists=False).open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            result=experiment(args.out,positive=args.positive,run_native=True)
    finally:
        for sig,handler in prior.items():signal.signal(sig,handler)
    print(json.dumps({'status':result['status'],'controls_passed':result['controls_passed'],'output':str(args.out)}))
    return 0 if result['controls_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
