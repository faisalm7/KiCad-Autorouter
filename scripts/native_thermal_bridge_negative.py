#!/usr/bin/env python3
"""One <=30 s native bridge-removal counterfactual; explicit --run-native required.

Never edits the positive candidate. This is a diagnostic, not accepted routing or
an equal-budget end-to-end comparison. Lead must assign the sole native lane.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as s
import argparse,copy,datetime,fcntl,json,resource,shutil,signal,time
POSITIVE=ROOT/'.runs/interf-thermal-bridge-002'
BASE=ROOT/'.runs/interf-native-003'
POSITIVE_HASH='2368bbf1804db1b1de5ccc8980a96d01d35052aaa9f305b73337a0b90c24a2d4'
BASE_HASH='922c6ce93556732940b5bccc06794c84b35fd164f86abd0ac3f6faf5b76e3f41'
REPORT_HASH='e45eacf60d0b8d429fbe7b437e0441dfd677302f16a8e765470e28e8a5bc7fa0'
PROTOCOL_HASH='d322f55dadfb6dff5fb31d434a3a66cdc158a2157feefe05427cd71457ca9a37'
UID='4a77607c-3e2e-5b32-bf20-dd4d9b737f1f'
PAD='387e8928-4a73-4b3a-ae74-249440996e94'
ZONE='00000000-0000-0000-0000-00004cdec22b'
BUDGET=30.0

def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime

def read(path):return json.loads(path.read_text())
def require(condition,message):
    if not condition:raise p.Rejected(message)

def main(out):
    started,initial_cpu=time.monotonic(),cpu()
    out=Path(out).resolve()
    require(ROOT/'.runs' in out.parents,'output outside project .runs')
    for preserved in (POSITIVE,BASE,Path(__file__).resolve().parent):
        require(out!=preserved and preserved not in out.parents,'output inside preserved evidence')
    out.mkdir(parents=True,exist_ok=False)
    summary={'schema':1,'status':'incomplete','control_passed':False,'candidate_accepted':False,'comparison_eligible':False,'native_executed':False,'applied':False,'wall_budget_seconds':BUDGET,'cpu_budget_seconds':BUDGET,'cpu_enforcement':'postcompletion measured acceptance cap, not OS preemption','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'steps':[]}
    try:
        require(p.sha(POSITIVE/'protocol.json')==PROTOCOL_HASH,'positive protocol changed')
        positive_protocol=read(POSITIVE/'protocol.json');positive=read(POSITIVE/'bridge-01/diagnostic-result.json')
        source=Path(positive_protocol['source']);good=Path(positive['candidate']);hashes=positive_protocol['source_hashes']
        require(ROOT/'.data/boards' in source.resolve().parents and good==POSITIVE/'bridge-01/candidate'/source.name,'input path outside pinned task')
        tools=p.tool_manifest();evidence_before=p.tree_hash(POSITIVE)
        require(tools['files']==positive_protocol['tools']['files'] and tools['implementation_sha256']==positive_protocol['tools']['implementation_sha256'],'review required after validator/tool change')
        def stable():
            require(p.tree_hash(source.parent)==hashes,'source changed')
            require(p.tree_hash(POSITIVE)==evidence_before,'positive evidence changed')
            require(p.tree_hash(BASE/'snapshot')==hashes,'original snapshot changed')
            require(p.sha(BASE/'candidate'/source.name)==BASE_HASH,'failed incumbent changed')
            require(p.tool_manifest()==tools,'tool/code freeze changed')
        stable();p.check_storage()
        require(p.sha(good)==POSITIVE_HASH==positive['candidate_sha256'],'positive candidate binding changed')
        p.verify_candidate_files(good,hashes,POSITIVE_HASH)
        require(p.sha(POSITIVE/'bridge-01/final-drc.json')==REPORT_HASH==positive['native_report_sha256'],'positive native report hash changed')
        positive_native=p.parse_report(POSITIVE/'bridge-01/final-drc.json',source.name)
        require(positive_native==positive['native'] and all(positive_native[k]==0 for k in ('opens','blocking','warnings','exclusions')),'positive native report invalid')
        expected_good=dict(hashes);expected_good[source.name]=POSITIVE_HASH
        binding=read(POSITIVE/'bridge-01/final-drc-binding.json')
        require(binding['before']==expected_good and binding['after']==p.tree_hash(POSITIVE/'bridge-01/final-drc-input') and all(binding['after'].get(k)==v for k,v in expected_good.items()),'positive native input stale')
        original=p.preflight(source);protected=[r for r in p.routes(original) if p.locked(r)]
        native_map=read(POSITIVE/'bridge-01/final-netclasses.json');class_audit=p.audit_candidate_netclasses(good,protected,native_map)
        class_audit['native_map_file_sha256']=p.sha(POSITIVE/'bridge-01/final-netclasses.json')
        require(class_audit==read(POSITIVE/'bridge-01/final-netclass-audit.json'),'positive strict class audit mismatch')
        baseline=p.parse_report(BASE/'final-drc.json',source.name);base_receipt=read(BASE/'result.json')
        require(baseline==base_receipt['native'] and p.sha(BASE/'final-drc.json')==base_receipt['native_report_sha256']==positive_protocol['base_native_report_sha256'],'negative expectation stale')
        tree=s.read(good);matches=[r for r in p.routes(tree) if s.one(r,'uuid')==['uuid','"'+UID+'"']]
        require(len(matches)==1 and matches[0]==positive_protocol['proposals'][0]['node'],'removal not exactly the declared bridge')
        removed=copy.deepcopy(tree);removed.remove(matches[0])
        require(p.immutable(removed)==p.immutable(original),'negative immutable mismatch')
        remaining=min(BUDGET-(time.monotonic()-started),BUDGET-(cpu()-initial_cpu))-2
        require(remaining>=5,'not enough budget for native control')
        job=p.Job(out/'trial',remaining);summary['steps']=job.steps
        shutil.copytree(good.parent,job.out/'candidate');candidate=job.out/'candidate'/source.name;s.write(candidate,removed)
        require(p.sha(candidate)==BASE_HASH,'bridge removal does not recreate exact failed incumbent')
        p.verify_candidate_files(candidate,hashes,BASE_HASH)
        shutil.copytree(source.parent,out/'snapshot')
        shutil.copy2(__file__,out/'control.py')
        for name,digest in tools['implementation_sha256'].items():
            saved=out/'code'/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,saved)
            require(p.sha(saved)==digest,'code changed during snapshot')
        protocol={'schema':1,'kind':'negative bridge-removal diagnostic; one native trial, no engine','source':str(source),'source_hashes':hashes,'tools':tools,'script_sha256':p.sha(__file__),'positive_evidence_hashes':evidence_before,'positive_candidate_sha256':POSITIVE_HASH,'positive_report_sha256':REPORT_HASH,'removed_uuid':UID,'expected_negative_candidate_sha256':BASE_HASH,'expected_native':baseline,'wall_budget_seconds':BUDGET,'cpu_budget_seconds':BUDGET,'cost_scope':'negative diagnostic only; not full route acquisition'}
        p.save_json(out/'protocol.json',protocol);summary['protocol_sha256']=p.sha(out/'protocol.json')
        stable();require(p.tree_hash(out/'snapshot')==hashes,'snapshot changed before native control')
        final,native=p.validate_candidate(job,original,candidate,hashes,protected)
        require(p.routes(s.read(candidate))==p.routes(removed),'native validation changed negative routing')
        require(final==BASE_HASH,'native refill unexpectedly changed counterfactual bytes')
        p.verify_candidate_files(candidate,hashes,final)
        stable();require(p.tree_hash(out/'snapshot')==hashes,'snapshot changed after native control')
        errors=[finding for finding in native['findings'] if finding['severity']=='error']
        expected=native==baseline and native['opens']==native['warnings']==native['exclusions']==0 and native['blocking']==1 and len(errors)==1 and errors[0]['type']=='starved_thermal' and {i['uuid'] for i in errors[0]['items']}=={PAD,ZONE}
        summary.update(status='expected_native_rejection' if expected else 'unexpected_native_outcome',control_passed=expected,candidate=str(candidate),candidate_sha256=final,native=native,native_report_sha256=p.sha(job.out/'final-drc.json'))
        require(all(step.get('cleanup_complete') and not step.get('log_truncated') and step.get('status') in ('success','nonzero_exit') for step in job.steps),'native process cleanup incomplete')
    except KeyboardInterrupt:summary.update(status='cancelled',control_passed=False)
    except Exception as exc:summary.update(status='control_error',control_passed=False,reason=type(exc).__name__+': '+str(exc))
    def account():
        summary.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=cpu()-initial_cpu,native_executed=bool(summary['steps']))
        if summary['wall_seconds']>BUDGET or summary['total_cpu_seconds']>BUDGET:summary.update(status='budget_exceeded',control_passed=False)
    try:
        account();p.save_json(out/'negative-summary.json',summary)
        if time.monotonic()-started>BUDGET or cpu()-initial_cpu>BUDGET:account();p.save_json(out/'negative-summary.json',summary)
    except KeyboardInterrupt:
        summary.update(status='cancelled',control_passed=False)
        partial=out/'negative-summary.json.partial'
        if partial.exists():partial.rename(out/'cancelled-summary.partial')
        account();p.save_json(out/'negative-summary.json',summary)
    print(json.dumps({'status':summary['status'],'control_passed':summary['control_passed'],'candidate_accepted':False,'output':str(out)}))
    return 0 if summary['control_passed'] else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--run-native',action='store_true')
    args=parser.parse_args()
    if not args.run_native:parser.error('Explicit --run-native is required in a lead-assigned quiet slot')
    def interrupt(signum,frame):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupt)
    lock=ROOT/'.runs/quality-experiment.lock'
    require(not lock.is_symlink(),'experiment lock symlink')
    with lock.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raise SystemExit(main(args.output))
