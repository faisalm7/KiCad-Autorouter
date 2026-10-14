"""Clock-only fixed offline plan/cache acquisition; no network fallback."""
import argparse,fcntl,json,re,sys,time
from pathlib import Path
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as shared
from experiments.licensed_acquisition_v6.cache_transport import Cache

def execute(args,started,root=ROOT,here=HERE):
    root=Path(root);here=Path(here);selected=shared.profile('v6');plan,baseline,rows=shared.load(here,'v6')
    shared.inventory(root/'.data',baseline);cache=Cache(root,plan,rows)
    if not args.reuse_cache:
        return {'action':'plan_only','network_requests':0,'planned_files':len(rows),'planned_bytes':741742,
            'current_data_files':baseline['file_count'],'current_data_bytes':baseline['bytes'],
            'post_acquisition_data_files':baseline['file_count']+10,'post_acquisition_data_bytes':baseline['bytes']+741742,
            'cache_lineage_verified':True,'native_qualified':False,'models_downloaded':0}
    runtime=shared.committed(root,here,'v6');name=shared.safe(args.output)
    if len(name.parts)!=2 or name.parts[0]!='.runs' or not re.fullmatch(re.escape(selected['output_prefix'])+'[0-9]{3}',name.parts[1]):raise ValueError('fixed fresh clock output required')
    out=shared.contained(root,root/name);lock=shared.contained(root,root/'.runs/licensed-acquisition.lock')
    with lock.open('a+b') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=shared.acquire(root,here,out,plan,baseline,rows,runtime,started,cache.transport,'v6')
        acquired={r['destination']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in rows}
        def remaining():
            left=300-(time.monotonic()-started)
            if left<=0:raise TimeoutError('cached acquisition finalization deadline')
            return left
        def stable():
            remaining();cache.verify();shared.material(root,here,runtime,'v6')
            shared.inventory(root/'.data',shared.extend(baseline,acquired,destination_root='expansion009'));cache.verify();remaining()
        result.update(acquisition_transport=plan['cache_reuse']['transport'],new_network_requests=0,new_network_bytes=0,
            cached_source_lineage_sha256={n:v['sha256'] for n,v in plan['cache_reuse']['metadata'].items()},
            processed_cached_payload_bytes=result['received_bytes'],source_research_cost_retained=plan['cache_reuse']['past_source_research_cost'])
        shared.publish(out,result,stable,remaining)
        return result

def main():
    start=time.monotonic();parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-cache',action='store_true');parser.add_argument('--output',default='')
    args=parser.parse_args()
    with shared.cancellation():result=execute(args,start)
    print(json.dumps({k:result[k] for k in result if k in ('action','status','planned_files','planned_bytes','acquired_files','acquired_bytes','new_network_requests','network_requests','cache_lineage_verified')}))
if __name__=='__main__':main()
