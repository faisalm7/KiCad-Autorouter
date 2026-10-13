from pathlib import Path
import datetime,json,sys,time,resource
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as pc,placement_strategy as ps
source=root/'.runs/placement-paired-001/run/C_feedback';out=root/'.runs/validated-readback-performance-001';out.mkdir()
before=pc.inventory(source,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2,with_directories=True)
rows=[]
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN);return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
for mode in ('uncached','scoped'):
    start=time.monotonic();begin=cpu();answers=[]
    if mode=='scoped':
        with p.validation_readback_session():
            for i in range(2):answers.append(p.check_result(source/'result.json'))
    else:
        for i in range(2):answers.append(p.check_result(source/'result.json'))
    assert answers[0]==answers[1]
    rows.append({'mode':mode,'readbacks':2,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':cpu()-begin,'answer':answers[0]})
assert pc.inventory(source,max_bytes=ps.LIMIT,max_files=ps.MAX_FILES,max_entries=ps.MAX_FILES*2,with_directories=True)==before
p.save_json(out/'result.json',{'schema':1,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'implementation_sha256':p.tool_manifest()['implementation_sha256'],'wrapper_sha256':p.sha(Path(__file__)),'rows':rows,'source_unchanged':True,'native_executed':False,'scope':'Repeated consistency readback cost only, on old inner accepted candidate. Does not change rejected120CPU delivery or establish route gain.'})
print(json.dumps(rows))
