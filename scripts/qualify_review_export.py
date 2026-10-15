#!/usr/bin/env python3
"""Sequential native qualification of existing review/export APIs; no routing repeats.

Requires retained accepted receipts. Uses shared copy, choice, validation, proof,
process and publication helpers. This controller never grants PCB approval.
"""
from pathlib import Path
import argparse,fcntl,hashlib,signal,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h,review_export as e
SECONDS=600
CASES=(('native_partial_layers','.runs/layers-native-partial-front-001/result.json',1,False),
       ('placement','.runs/default-tuning-native-001/result.json',3,False),
       ('search','.runs/placement-paired-003/run/B1/result.json',4,False),
       ('pruning','.runs/placement-paired-003/run/C_feedback/result.json',5,True),
       ('pruning_owned','.runs/placement-pruning-controls-004/run/C/result.json',5,False))

def selected_cases(receipt=None,*,render=False):
    """Choose the unchanged default population or one explicit retained result."""
    if type(render) is not bool:raise p.Rejected('render must be an explicit boolean')
    if receipt is None:
        if render:raise p.Rejected('--render requires one explicit --receipt')
        return CASES
    try:
        path=Path(receipt)
        path=h.real_path(path if path.is_absolute() else c.ROOT/path)
        runs=c.ROOT/'.runs'
        if path.name!='result.json' or runs not in path.parents or path.parent==runs or not path.is_file():
            raise p.Rejected('explicit receipt must be an existing project .runs case result.json')
        data=f.read_json(path)
    except (OSError,ValueError,TypeError) as exc:
        raise p.Rejected('invalid explicit retained receipt: '+str(exc)) from exc
    if not isinstance(data,dict) or type(data.get('schema')) is not int or data['schema'] not in (1,3,4,5):
        raise p.Rejected('explicit retained receipt requires supported schema 1, 3, 4 or 5')
    return (('retained',str(path),data['schema'],render),)

def cancelled(exc):
    for _ in range(8):
        if isinstance(exc,KeyboardInterrupt):return True
        exc=exc.__cause__ if exc is not None else None
        if exc is None:break
    return False

def qualify(output,*,run_native=False,receipt=None,render=False):
    if run_native is not True:raise p.Rejected('--run-native required before any native work')
    start=time.monotonic();cpu0=time.process_time()+f.child_cpu()
    cases=selected_cases(receipt,render=render)
    out=h.real_path(output,existing=False)
    direct=out.parent==c.ROOT/'.runs'
    monitored=out.name=='run' and out.parent.parent==c.ROOT/'.runs' and out.parent.name.startswith('review-export-native-')
    if out.exists() or not (direct or monitored):raise p.Rejected('new project-local direct or monitored qualification output required')
    out.mkdir();owner={};h.capture_destination(owner,out)
    record={'schema':1,'kind':'review-export-native-qualification-v1','status':'failed','accepted':False,'controls_passed':False,
        'routing_accepted':False,'human_pcb_approval_observed':False,'live_application_qualified':False,'new_routing_executed':False,
        'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'cases':[],
        'scope':f'{len(cases)} retained qualified project(s); new copy/intent/export/proof, sequential native workers, no solver rerun. Intent is a test input, no human approval.',
        'compute_scope':'Additional full workflow qualification cost, separate from original measured routing comparisons. Existing routing compute retained explicitly.'}
    remaining=lambda:max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(time.process_time()+f.child_cpu()-cpu0)))
    completed={};inputs={};tools=None;code=None
    def stable():
        h.owned_destination(owner)
        if remaining()<=0:raise p.Rejected('whole native workflow qualification budget exhausted')
        if tools is not None and p.tool_manifest()!=tools:raise p.Rejected('qualification source/tools/HEAD changed')
        if code is not None and p.sha(Path(__file__))!=code:raise p.Rejected('qualification controller changed')
        for path,expected in inputs.items():
            if e.witness(Path(path))!=expected:raise p.Rejected('original routing/source evidence changed')
        for path,expected in completed.items():
            if e.witness(Path(path))!=expected:raise p.Rejected('completed review/export evidence changed')
    def account():
        record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu0)
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
        record['controls_passed']=(record['status']=='completed' and record['within_budget'] and len(record['cases'])==len(cases) and all(x.get('passed') is True for x in record['cases']))
    try:
        p.check_storage();tools=p.tool_manifest();code=p.sha(Path(__file__));record.update(tools=tools,controller_sha256=code)
        raw=subprocess.run(['git','show',tools['git_head']+':scripts/qualify_review_export.py'],cwd=c.ROOT,capture_output=True,check=True,timeout=10).stdout
        if hashlib.sha256(raw).hexdigest()!=code:raise p.Rejected('commit exact qualification controller before native execution')
        frozen=[]
        for name,relative,schema,render in cases:
            receipt=h.real_path(c.ROOT/relative);data=f.read_json(receipt)
            if data.get('schema')!=schema:raise p.Rejected('retained case policy/schema differs')
            p.check_result(receipt)
            for path in (receipt.parent,Path(data['source']).parent):inputs[str(path)]=e.witness(path)
            frozen.append({'name':name,'receipt':str(receipt),'receipt_sha256':p.sha(receipt),'candidate_sha256':data['candidate_sha256'],'schema':schema,'render':render})
        record['protocol_cases']=frozen;record['original_inputs']=inputs;p.save_json(out/'protocol.json',record)
        for pin in frozen:
            stable();case_dir=out/pin['name'];case_dir.mkdir();entry={'name':pin['name'],'passed':False};record['cases'].append(entry)
            case_start=time.monotonic();case_cpu=time.process_time()+f.child_cpu()
            try:
                review=h.review_copy(pin['receipt'],case_dir/'review',render=pin['render'])
                intent=h.review_choice(case_dir/'review/review.json',case_dir/'intent','accept')
                result=e.export(case_dir/'intent/choice.json',case_dir/'export',min(e.SECONDS,remaining()))
                checked=e.check_export(case_dir/'export/export.json');stable()
                if not result['export_accepted'] or not checked['current']:raise p.Rejected('fresh export/proof rejected')
                entry.update(review_sha256=p.sha(case_dir/'review/review.json'),choice_sha256=p.sha(case_dir/'intent/choice.json'),
                    export_sha256=p.sha(case_dir/'export/export.json'),exported_project=result['project_file'],candidate_sha256=result['candidate_sha256'],
                    final_native_report_sha256=result['native_report_sha256'],native={k:result['native'][k] for k in ('opens','blocking','warnings','exclusions','ignored_checks')},
                    metrics=result['metrics'],native_steps=[x['name'] for x in result['steps']],
                    source_and_routing_preserved=True,preview_rendered=pin['render'],human_pcb_approval_observed=False)
                # Rejection is a persistent alternative intent and deletes nothing.
                rejected=h.review_choice(case_dir/'review/review.json',case_dir/'rejection','reject')
                if rejected['choice']!='reject' or rejected['routing_accepted'] is not False:raise p.Rejected('rejection intent inconsistent')
                entry['rejection_sha256']=p.sha(case_dir/'rejection/choice.json')
                entry['passed']=True
            except (Exception,KeyboardInterrupt) as exc:
                entry.update(passed=False,error=type(exc).__name__+': '+str(exc))
                if cancelled(exc):raise KeyboardInterrupt from exc
            finally:
                entry.update(wall_seconds=time.monotonic()-case_start,full_cpu_seconds=time.process_time()+f.child_cpu()-case_cpu)
                p.save_json(case_dir/'case.json',entry);completed[str(case_dir)]=e.witness(case_dir)
            stable()
        record['status']='completed' if all(x['passed'] for x in record['cases']) else 'failed'
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if cancelled(exc) else 'failed',reason=type(exc).__name__+': '+str(exc))
    # Existing fail-closed publisher; accepted stays False for a diagnostic
    # controller. stable() checks caps even when no PCB acceptance is granted.
    result=f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner))
    if remaining()<=0:
        h.owned_destination(owner);result.update(status='budget_exceeded',controls_passed=False);p.save_json(out/'result.json',result)
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--run-native',action='store_true')
    parser.add_argument('--receipt',type=Path,help='qualify only this retained project .runs result.json; defaults remain the original CASES')
    parser.add_argument('--render',action='store_true',help='render the one explicitly selected receipt preview')
    args=parser.parse_args(argv)
    if not args.run_native:parser.error('--run-native required')
    if args.render and args.receipt is None:parser.error('--render requires --receipt')
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def stop(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,stop)
        with (c.ROOT/'.runs/quality-experiment.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=qualify(args.output,run_native=True,receipt=args.receipt,render=args.render)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    print(f.canonical({k:result[k] for k in ('status','controls_passed','routing_accepted','new_routing_executed','wall_seconds','total_cpu_seconds')}))
    return 0 if result['controls_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
