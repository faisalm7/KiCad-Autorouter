#!/usr/bin/env python3
"""Generate <=4 fixed GND bridge probes; --validate explicitly runs native checks.

Diagnostic repair-only costs exclude acquiring the failed incumbent. No result is
an accepted routing receipt or a fair end-to-end system comparison. Originals
are immutable; no engine or original reference-route selection is used.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, sexpr as sx
import argparse,copy,datetime,fcntl,json,math,resource,shutil,signal,time,uuid
BASE=ROOT/'.runs/interf-native-003'
BASE_HASH='922c6ce93556732940b5bccc06794c84b35fd164f86abd0ac3f6faf5b76e3f41'
PAD='387e8928-4a73-4b3a-ae74-249440996e94'
ZONE='00000000-0000-0000-0000-00004cdec22b'
BUDGET=60.0

def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime

def inside(point,poly):
    x,y=point;v=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:v=not v
    return v

def diagnostic_uuid_index(base):
    owners={}
    def visit(node):
        if not isinstance(node,list) or not node:return
        for child in node[1:]:
            if isinstance(child,list) and child and child[0]=='uuid':
                if len(child)!=2 or not isinstance(child[1],str):raise p.Rejected('malformed candidate UUID')
                owners.setdefault(sx.unquote(child[1]),[]).append(node)
            visit(child)
    visit(base)
    for uid,kind in ((PAD,'pad'),(ZONE,'zone')):
        matches=owners.get(uid,[])
        if len(matches)!=1 or matches[0][0]!=kind:raise p.Rejected('ambiguous or incorrectly typed diagnostic target UUID')
    return owners

def main(out,validate):
    started,started_cpu=time.monotonic(),cpu()
    out=out.resolve()
    if ROOT/'.runs' not in out.parents:raise p.Rejected('output outside project .runs')
    out.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((BASE/'result.json').read_text());candidate=Path(receipt['candidate']);source=Path(receipt['source']);hashes=receipt['source_hashes'];tools=p.tool_manifest()
    if ROOT/'.data/boards' not in source.resolve().parents or candidate!=BASE/'candidate'/source.name:
        raise p.Rejected('base receipt paths escape the explicit local task')
    def stable():
        if p.tree_hash(source.parent)!=hashes or p.tree_hash(BASE/'snapshot')!=hashes:raise p.Rejected('source or snapshot stale')
        if p.sha(candidate)!=BASE_HASH or p.tool_manifest()!=tools:raise p.Rejected('candidate/code/tool freeze changed')
    stable();p.check_storage();p.verify_candidate_files(candidate,hashes,BASE_HASH)
    original=sx.read(source);base=sx.read(candidate)
    if p.immutable(base)!=p.immutable(original):raise p.Rejected('base immutable mismatch')
    protected=[r for r in p.routes(original) if p.locked(r)]
    binding=json.loads((BASE/'final-drc-binding.json').read_text());expected=dict(hashes);expected[source.name]=BASE_HASH
    if binding['before']!=expected or p.tree_hash(BASE/'final-drc-input')!=binding['after'] or any(binding['after'].get(k)!=v for k,v in expected.items()):raise p.Rejected('base native input binding stale')
    baseline=p.parse_report(BASE/'final-drc.json',source.name)
    if baseline!=receipt['native'] or p.sha(BASE/'final-drc.json')!=receipt['native_report_sha256']:raise p.Rejected('base native report binding stale')
    errors=[f for f in baseline['findings'] if f['severity']=='error']
    if baseline['opens'] or baseline['exclusions'] or len(errors)!=1 or errors[0]['type']!='starved_thermal' or {i['uuid'] for i in errors[0]['items']}!={PAD,ZONE}:raise p.Rejected('unexpected baseline failure')
    uuids=diagnostic_uuid_index(base)
    zone=uuids[ZONE][0]
    if sx.one(zone,'net')!=['net','100'] or sx.one(zone,'layer')!=['layer','"B.Cu"']:raise p.Rejected('zone identity changed')
    polys=[[list(map(float,v[1:3])) for v in sx.one(poly,'pts')[1:]] for poly in sx.children(zone,'filled_polygon')]
    proposals=[]
    for index,x in enumerate([149.96,150.00,150.04,150.08]):
        a=[x,71.7];b=[x,73.8]
        a_polys=[i for i,poly in enumerate(polys) if inside(a,poly)];b_polys=[i for i,poly in enumerate(polys) if inside(b,poly)]
        if a_polys!=[20] or b_polys!=[17]:raise p.Rejected('bridge does not join the two predeclared filled regions')
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'kicad-autorouter:interf-003-thermal-bridge:'+BASE_HASH+':'+str(index)))
        if uid in uuids:raise p.Rejected('generated UUID collision')
        node=['segment',['start',f'{x:.2f}','71.7'],['end',f'{x:.2f}','73.8'],['width','0.5'],['layer','"B.Cu"'],['net','100'],['uuid','"'+uid+'"']]
        proposals.append({'id':f'bridge-{index+1:02d}','node':node,'uuid':uid,'net':'GND','width_mm':.5,'layer':'B.Cu','start_mm':a,'end_mm':b,'length_mm':math.dist(a,b),'start_saved_fill_polygon':20,'end_saved_fill_polygon':17})
    protocol={'schema':1,'kind':'bounded diagnostic repair, not a baseline/system score','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_receipt_sha256':p.sha(BASE/'result.json'),'base_candidate_sha256':BASE_HASH,'base_native_report_sha256':p.sha(BASE/'final-drc.json'),'source':str(source),'source_hashes':hashes,'tools':tools,'script_sha256':p.sha(__file__),'wall_budget_seconds':BUDGET,'CPU_budget_seconds':BUDGET,'cost_scope':'repair only; failed incumbent acquisition excluded; no comparative eligibility','hypothesis':'bridge isolated same-net fill to distinct saved copper body, leaving original zone/pad/rules unchanged','proposal_policy':'four fixed nearby parallel GND bridges, stop after first native pass; no reference routing','proposals':proposals}
    p.save_json(out/'protocol.json',protocol);shutil.copy2(__file__,out/'probe.py');shutil.copytree(source.parent,out/'snapshot')
    for relative,digest in tools['implementation_sha256'].items():
        copied=out/'code'/relative;copied.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,copied)
        if p.sha(copied)!=digest:raise p.Rejected('code changed during diagnostic snapshot')
    summary={'schema':1,'status':'generated_only','validation_passed':False,'comparison_eligible':False,'applied':False,'physical_electrical_validation':False,'native_validation_requested':validate,'native_executed':False,'protocol_sha256':p.sha(out/'protocol.json'),'trials':[]}
    try:
        for proposal in proposals:
            stable()
            remaining=min(BUDGET-(time.monotonic()-started),BUDGET-(cpu()-started_cpu))
            if remaining<10:summary['status']='budget_reserve_reached';break
            directory=out/proposal['id'];job=p.Job(directory,max(.001,remaining-2));shutil.copytree(candidate.parent,directory/'candidate');board=directory/'candidate'/source.name
            new=copy.deepcopy(base);new.append(proposal['node']);sx.write(board,new)
            if p.immutable(new)!=p.immutable(original) or p.routes(new)!=p.routes(base)+[proposal['node']]:raise p.Rejected('proposal modifies more than one generated track')
            trial={'id':proposal['id'],'validation_passed':False,'candidate':str(board),'proposed_candidate_sha256':p.sha(board),'status':'generated_only','steps':job.steps}
            summary['trials'].append(trial)
            if validate:
                try:
                    final,native=p.validate_candidate(job,original,board,hashes,protected)
                    job.native('metrics','metrics',board,directory/'metrics.json');metrics=json.loads((directory/'metrics.json').read_text())
                    p.verify_candidate_files(board,hashes,final)
                    if p.routes(sx.read(board))!=p.routes(new):raise p.Rejected('validation changed proposed routing')
                    stable()
                    baseline_warning={(f['type'],tuple(sorted(i['uuid'] for i in f['items']))) for f in baseline['findings'] if f['severity']=='warning'}
                    warnings={(f['type'],tuple(sorted(i['uuid'] for i in f['items']))) for f in native['findings'] if f['severity']=='warning'}
                    valid=p.native_accepted(native) and warnings<=baseline_warning
                    trial['native_rejection_reasons']=p.native_rejection_reasons(native)
                    trial.update(status='native_pass' if valid else 'native_rejected',validation_passed=valid,candidate_sha256=final,native=native,native_report_sha256=p.sha(directory/'final-drc.json'),metrics=metrics)
                except p.Rejected as exc:trial.update(status='validation_error',reason=str(exc))
            trial.update(steps=job.steps,finished_elapsed_seconds=time.monotonic()-started,finished_observed_CPU_seconds=cpu()-started_cpu)
            p.save_json(directory/'diagnostic-result.json',trial)
            if any(s.get('status')=='cancelled' for s in job.steps):raise KeyboardInterrupt
            if trial['validation_passed']:
                summary.update(status='diagnostic_native_pass',validation_passed=True,selected=proposal['id']);break
        if validate and summary['status']=='generated_only':summary['status']='no_native_pass'
        stable()
        if p.tree_hash(out/'snapshot')!=hashes:raise p.Rejected('diagnostic snapshot stale')
    except KeyboardInterrupt:summary.update(status='cancelled',validation_passed=False)
    except Exception as exc:summary.update(status='invalidated',validation_passed=False,reason=type(exc).__name__+': '+str(exc))
    def account():
        summary['native_executed']=any(trial.get('steps') for trial in summary['trials'])
        summary.update(wall_seconds=time.monotonic()-started,total_CPU_seconds=cpu()-started_cpu)
        if summary['wall_seconds']>BUDGET or summary['total_CPU_seconds']>BUDGET:summary.update(status='budget_exceeded',validation_passed=False)
    try:
        account();p.save_json(out/'diagnostic-summary.json',summary)
        if time.monotonic()-started>BUDGET or cpu()-started_cpu>BUDGET:account();p.save_json(out/'diagnostic-summary.json',summary)
    except KeyboardInterrupt:
        summary.update(status='cancelled',validation_passed=False)
        partial=out/'diagnostic-summary.json.partial'
        if partial.exists():partial.rename(out/'cancelled-summary.partial')
        account();p.save_json(out/'diagnostic-summary.json',summary)
    print(json.dumps({'status':summary['status'],'validation_passed':summary['validation_passed'],'comparison_eligible':False,'output':str(out)}))
    return 0 if (summary['validation_passed'] if validate else summary['status']=='generated_only') else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--validate',action='store_true',help='Runs native tools; only use in lead-assigned quiet slot')
    args=parser.parse_args()
    def interrupt(sig,frame):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupt)
    lock=ROOT/'.runs/quality-experiment.lock'
    if lock.is_symlink():raise p.Rejected('lock symlink')
    with lock.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raise SystemExit(main(args.output,args.validate))
