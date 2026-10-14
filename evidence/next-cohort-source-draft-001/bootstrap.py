"""One fixed predeclared source read; no native, engine, models or scripts."""
import time,resource
START=time.monotonic()
def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime
CPU_START=cpu()
import argparse,hashlib,json,os,sys
from pathlib import Path
HERE=Path(__file__).absolute().parent
ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.licensed_acquisition_v1 import fetch as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
from autorouter import handoff as h,floor_route as f
from scripts.fetch_led_demo import OwnedFile
PROTOCOL_SHA='dac50fe393340fbe4ed4f78d464ef0b46eb5a4a5cfaac0e8ff44a03f347bdbaa'
MATERIAL=('experiments/licensed_acquisition_v1/fetch.py',
          'experiments/placement_handoff_native_v1/driver.py',
          'autorouter/handoff.py','autorouter/floor_route.py','scripts/fetch_led_demo.py')

def main(fetch=False):
    path=HERE/'PRE_GET_PROTOCOL.json';raw=shared.bounded(path)
    if shared.sha(raw)!=PROTOCOL_SHA:raise ValueError('pre-GET protocol changed')
    plan=shared.decode(raw);rows=plan['rows'];out=HERE/plan['output']
    cohort=ROOT/'.runs/licensed-cohort-leads-001/cohort.json'
    if shared.sha(shared.bounded(cohort))!=plan['cohort_sha256']:raise ValueError('fixed cohort changed')
    if fetch is not True:return {'status':'plan_only','new_network_requests':0,'planned_bytes':164397}
    if out.exists():raise ValueError('preserve existing fixed observation; never rerun in place')
    out.mkdir();owner={};h.capture_destination(owner,out)
    responses=out/'responses';responses.mkdir();response_owner={};h.capture_destination(response_owner,responses)
    source_owner={};requests=[];received={};completed={};source_inventory=None
    witness={name:shared.sha(shared.bounded(ROOT/name)) for name in MATERIAL}
    witness.update({'bootstrap.py':shared.sha(shared.bounded(HERE/'bootstrap.py')),'PRE_GET_PROTOCOL.json':PROTOCOL_SHA})
    record={'schema':1,'kind':'fixed_cohort_primary_source_read','status':'running','accepted':False,
        'native_accepted':False,'repository':plan['repository'],'source_commit':plan['commit'],
        'protocol_sha256':PROTOCOL_SHA,'runtime_sha256':witness,'budget_seconds':300,
        'cpu_budget_seconds':300,'max_requests':5,'network_byte_cap':164402,
        'output_byte_cap':2097152,'requests':requests,'files':[],'engine_jobs':0,'native_jobs':0,
        'new_network_requests':0,'source_files_exact':False,'cohort_changed':False,
        'warnings':['Native constraints/loading/refill/parity/electrical/physical qualification unknown.',
                    'Source read is development exposed; optional models and scripts are not fetched.']}
    fd=os.open(responses,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|getattr(os,'O_CLOEXEC',0))
    def owned():
        h.owned_destination(owner);h.owned_destination(response_owner)
        if source_owner.get('created'):h.owned_destination(source_owner)
        if fd is not None and (os.fstat(fd).st_dev,os.fstat(fd).st_ino)!=response_owner['directory_identity']:
            raise ValueError('response descriptor identity differs')
        return out
    def remaining():
        left=min(300-(time.monotonic()-START),300-(cpu()-CPU_START))
        if left<=0:raise TimeoutError('whole source read wall/CPU budget exhausted')
        return left
    def stable():
        owned();remaining()
        current={name:shared.sha(shared.bounded(ROOT/name)) for name in MATERIAL}
        current.update({'bootstrap.py':shared.sha(shared.bounded(HERE/'bootstrap.py')),
                        'PRE_GET_PROTOCOL.json':shared.sha(shared.bounded(path))})
        if current!=witness or shared.sha(shared.bounded(cohort))!=plan['cohort_sha256']:
            raise ValueError('fixed source-read implementation/protocol/cohort changed')
        actual=shared.inventory(out,cap=2097152)['files']
        for name,info in completed.items():
            if actual.get(name)!=info:raise ValueError('completed source artifact changed: '+name)
        if source_inventory is not None and shared.inventory(out/'source')!=source_inventory:
            raise ValueError('original source inventory changed')
        owned();remaining()
    def account():
        owned();actual=shared.inventory(out,cap=2097152)
        wall,used=time.monotonic()-START,cpu()-CPU_START
        record.update(wall_seconds=wall,total_cpu_seconds=used,output_bytes=actual['bytes'],
                      new_network_requests=len(requests),received_bytes=sum(x.get('received_bytes',0) for x in requests))
        record['source_files_exact']=source_inventory is not None and shared.inventory(out/'source')==source_inventory and all(actual['files'].get(n)==info for n,info in completed.items()) and len(record['files'])==5
        record['within_budget']=wall<=300 and used<=300 and actual['bytes']<=2097152 and len(requests)<=5 and record['received_bytes']<=164402
        if not record['within_budget']:record.update(status='failed',accepted=False)
    try:
        for index,row in enumerate(rows):
            stable();req={'index':index,'source_path':row['source_path'],'artifact':'responses/'+str(index+1).zfill(2)+'.payload'};requests.append(req)
            allowance=164402-sum(x.get('received_bytes',0) for x in requests)
            content=shared.fetch_one(row,req,OwnedFile(out/req['artifact'],owned,fd),allowance,remaining)
            info=shared.payload(row,content)
            if shared.bounded(out/req['artifact'])!=content:raise ValueError('response artifact differs')
            completed[req['artifact']]=info;received[row['source_path']]=content
            record['files'].append({**row,**info});stable()
        source_owner.update(copy_bytes(received,out/'source',expected_parent_owner=owner));owned()
        source_inventory=shared.inventory(out/'source')
        for name,content in received.items():completed['source/'+name]={'bytes':len(content),'sha256':shared.sha(content)}
        record.update(status='acquired_unqualified',source=str(out/'source'))
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',first_failure=type(exc).__name__+': '+str(exc))
    finally:os.close(fd);fd=None
    f.publish(out,record,stable,account,remaining,owned=owned)
    try:
        owned();remaining();stable()
        if f.read_json(out/'result.json')!=record:raise ValueError('source receipt changed after publication')
        return record
    except (Exception,KeyboardInterrupt) as exc:
        record.setdefault('first_failure',type(exc).__name__+': '+str(exc))
        record.update(status='invalidated',accepted=False,source_files_exact=False)
        f.publish(out,record,stable,account,remaining,owned=owned)
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fetch',action='store_true');args=parser.parse_args()
    with shared.cancellation(),shared.alarm(300):result=main(args.fetch)
    print(json.dumps({k:result.get(k) for k in ('status','source','new_network_requests','received_bytes','wall_seconds','total_cpu_seconds','source_files_exact','within_budget')}))
    raise SystemExit(0 if result['status'] in {'plan_only','acquired_unqualified'} else 2)
