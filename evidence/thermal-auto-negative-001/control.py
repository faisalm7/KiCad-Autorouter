#!/usr/bin/env python3
"""One <=30s native bridge-removal counterfactual. Lead runs with --run-native.

Original and positive evidence remain immutable. This never accepts a candidate
or claims equal-budget routing performance. No router/engine is launched.
"""
import argparse,copy,fcntl,hashlib,json,math,os,resource,shutil,signal,sys,time,uuid
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit as a
from autorouter import pipeline as p,sexpr as sx
ROOT=a.ROOT;BUDGET=30.0

def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);children=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime
def require(ok,message):
    if not ok:raise p.Rejected(message)
def local(path):
    path=Path(path)
    if not path.is_absolute():path=ROOT/path
    require('..' not in path.parts,'parent traversal is unsupported')
    try:path.relative_to(ROOT)
    except ValueError:raise p.Rejected('outside local checkout') from None
    require(not any(x.is_symlink() for x in (path,*path.parents)),'symlink in local path')
    return path

def publish(summary,out,totals,verify,save):
    def account():
        summary['wall_seconds'],summary['total_cpu_seconds']=totals()
        if any(not math.isfinite(v) or v<0 or v>BUDGET for v in totals()):summary.update(status='budget_exceeded',control_passed=False)
    def partial():
        file=out/'negative-summary.json.partial'
        if file.exists():
            local(file);file.rename(out/('interrupted-'+uuid.uuid4().hex+'.partial'))
    try:
        partial();verify();account();save(out/'negative-summary.json',summary)
        verify();account();save(out/'negative-summary.json',summary)
        if any(v>BUDGET for v in totals()):account();summary.update(status='budget_exceeded',control_passed=False);save(out/'negative-summary.json',summary)
    except KeyboardInterrupt:
        partial();summary.update(status='cancelled',control_passed=False);account();save(out/'negative-summary.json',summary)
    except Exception as exc:
        partial();summary.update(status='invalidated',control_passed=False,publication_reason=type(exc).__name__+': '+str(exc));account();save(out/'negative-summary.json',summary)

def main(output):
    started,initial_cpu=time.monotonic(),cpu();out=local(output)
    require(out.parent==ROOT/'.runs' and out.name.startswith('thermal-auto-negative-') and not out.exists(),'fresh direct .runs/thermal-auto-negative-* output required')
    out.mkdir()
    summary={'schema':1,'status':'preparing','control_passed':False,'candidate_accepted':False,'routing_accepted':False,'comparison_eligible':False,'applied':False,'native_executed':False,'original_inputs_unchanged':None,'wall_budget_seconds':BUDGET,'cpu_budget_seconds':BUDGET,'cost_scope':'single bridge-removal negative diagnostic; excludes acquisition and positive repair','steps':[]}
    ready=False;job=None
    def totals():return time.monotonic()-started,cpu()-initial_cpu
    def remaining():return min(BUDGET-v for v in totals())
    class NativeJob(p.Job):
        def step(self,name,argv,allowed=(0,)):
            require(remaining()>2,'global budget reserve exhausted')
            self.deadline=time.monotonic()+remaining()-1
            return super().step(name,['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',*argv],allowed)
        def native(self,name,action,board,result,*extra):
            return self.step(name,[p.c.PYTHON,'-B',out/'code/autorouter/native.py',action,board,result,*extra])
    try:
        positive_inventory=p.tree_hash(local(a.POSITIVE));base_inventory=p.tree_hash(local(a.BASE))
        positive=a.verify_positive();source=local(positive['source']);good=local(positive['candidate']);hashes=positive['source_hashes']
        tools=p.tool_manifest();helper_hash=p.sha(HERE/'audit.py');script_hash=p.sha(__file__)
        require(tools['files']==positive['tools']['files'],'native tools changed from positive experiment')
        p.check_storage();original=p.preflight(source);protected=[r for r in p.routes(original) if p.locked(r)]
        tree=sx.read(good);matches=[r for r in p.routes(tree) if sx.one(r,'uuid')==['uuid','"'+a.UID+'"']]
        require(len(matches)==1 and matches[0][0]=='segment','exact one owned bridge UUID required')
        negative=copy.deepcopy(tree);negative.remove(matches[0])
        require(hashlib.sha256((sx.dump(negative)+'\n').encode()).hexdigest()==a.BASE_HASH,'removal must recreate exact original failed candidate')
        require(p.immutable(negative)==p.immutable(original),'negative source invariants differ')
        require(remaining()>8,'insufficient global time/CPU for native negative control')
        job=NativeJob(out/'trial',remaining()-2);summary['steps']=job.steps
        env={k:v for k,v in job.env.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')}
        for k in ('KICAD_CONFIG_HOME','KICAD_CACHE_HOME','KICAD_DOCUMENTS_HOME'):env[k]=job.env[k]
        (job.out/'tmp').mkdir();env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(job.out/'tmp'));job.env=env
        shutil.copytree(good.parent,job.out/'candidate');candidate=job.out/'candidate'/source.name;sx.write(candidate,negative)
        p.verify_candidate_files(candidate,hashes,a.BASE_HASH)
        shutil.copytree(source.parent,out/'snapshot');shutil.copy2(__file__,out/'control.py');shutil.copy2(HERE/'audit.py',out/'positive_audit.py')
        for relative,h in tools['implementation_sha256'].items():
            saved=out/'code'/relative;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,saved)
            require(p.sha(saved)==h,'code changed during freeze')
        frozen_code=p.tree_hash(out/'code')
        protocol={'schema':1,'kind':'exact generated bridge-removal native negative','tools':tools,'source':str(source),'source_hashes':hashes,'script_sha256':script_hash,'audit_helper_sha256':helper_hash,'positive_evidence_sha256':positive_inventory,'base_evidence_sha256':base_inventory,'positive_candidate_sha256':a.GOOD_HASH,'expected_candidate_sha256':a.BASE_HASH,'removed_uuid':a.UID,'removed_node':matches[0],'expected_native':positive['baseline_native'],'wall_budget_seconds':BUDGET,'cpu_budget_seconds':BUDGET,'routing_accepted':False,'cost_scope':summary['cost_scope'],'current_code_vs_positive':positive['postrun_code_changes']}
        p.save_json(out/'protocol.json',protocol);summary['protocol_sha256']=p.sha(out/'protocol.json')
        def stable():
            require(p.tree_hash(source.parent)==hashes==p.tree_hash(out/'snapshot'),'original source/snapshot changed')
            require(p.tree_hash(a.POSITIVE)==positive_inventory and p.tree_hash(a.BASE)==base_inventory,'positive or base evidence changed')
            require(p.tool_manifest()==tools and p.sha(__file__)==script_hash and p.sha(HERE/'audit.py')==helper_hash,'tool/code/helper freeze changed')
            require(p.tree_hash(out/'code')==frozen_code and p.sha(out/'control.py')==script_hash and p.sha(out/'positive_audit.py')==helper_hash,'retained frozen implementation changed')
            require(p.sha(out/'protocol.json')==summary['protocol_sha256'],'control protocol changed')
            summary['original_inputs_unchanged']=True
        ready=True
        stable()
        final,native=p.validate_candidate(job,original,candidate,hashes,protected)
        require(final==a.BASE_HASH and sx.read(candidate)==negative,'native refill changed exact counterfactual')
        p.verify_candidate_files(candidate,hashes,final)
        errors=[f for f in native['findings'] if f['severity']=='error']
        expected=(native==positive['baseline_native'] and native['opens']==native['warnings']==native['exclusions']==0 and native['blocking']==1 and len(errors)==1 and errors[0]['type']=='starved_thermal' and {i['uuid'] for i in errors[0]['items']}=={a.PAD,a.ZONE})
        require(all(s['cleanup_complete'] and not s['log_truncated'] and s['status'] in ('success','nonzero_exit') for s in job.steps),'native cleanup or completion failed')
        summary.update(status='expected_native_rejection' if expected else 'unexpected_native_outcome',control_passed=expected,candidate=str(candidate),candidate_sha256=final,native=native,native_report_sha256=p.sha(job.out/'final-drc.json'),native_class_map_sha256=p.sha(job.out/'final-netclasses.json'))
        stable()
    except KeyboardInterrupt:summary.update(status='cancelled',control_passed=False)
    except Exception as exc:summary.update(status='control_error',control_passed=False,reason=type(exc).__name__+': '+str(exc))
    def final_check():
        if not ready:return
        stable()
        if not summary['control_passed']:return
        p.verify_candidate_files(candidate,hashes,a.BASE_HASH)
        require(p.sha(job.out/'final-drc.json')==summary['native_report_sha256'] and p.parse_report(job.out/'final-drc.json',source.name)==summary['native'],'negative report changed')
        require(p.sha(job.out/'final-netclasses.json')==summary['native_class_map_sha256'],'negative class map changed')
        p.audit_candidate_netclasses(candidate,protected,a.read(job.out/'final-netclasses.json'))
        binding=a.read(job.out/'final-drc-binding.json');expected=dict(hashes);expected[source.name]=a.BASE_HASH
        require(binding['before']==expected and binding['source']==str(candidate) and binding['input']==str(job.out/'final-drc-input'/source.name) and binding['saved'] is False,'negative final native binding differs')
        require(p.tree_hash(job.out/'final-drc-input')==binding['after'] and all(binding['after'].get(k)==h for k,h in expected.items()),'negative final native inputs changed')
    summary['native_executed']=bool(job and job.steps)
    publish(summary,out,totals,final_check,p.save_json)
    print(json.dumps({'status':summary['status'],'control_passed':summary['control_passed'],'native_executed':summary['native_executed'],'routing_accepted':False,'output':str(out)}))
    return 0 if summary['control_passed'] else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--run-native',action='store_true');args=parser.parse_args()
    if not args.run_native:parser.error('lead-scheduled --run-native is required')
    def interrupted(signum,frame):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    lock=local(ROOT/'.runs/quality-experiment.lock')
    with lock.open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raise SystemExit(main(args.output))
