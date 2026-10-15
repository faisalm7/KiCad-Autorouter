"""One sequential bounded fullSCH/fields diagnostic via existing shared runner."""
import time,resource
START=time.monotonic()
def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime
CPU0=cpu()
from pathlib import Path
import fcntl,json,os,stat,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.runs/native-schematic-toolchain-execution-001';out.mkdir();tools=p.tool_manifest()
lockpath=ROOT/'.runs/quality-experiment.lock'
if any(x.is_symlink() for x in (lockpath,*lockpath.parents)):raise p.Rejected('shared lock alias')
fd=os.open(lockpath,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'r+') as lock:
    info=os.fstat(lock.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary exclusive shared lock required')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'experiments/native_schematic_toolchain_v1/driver.py'),'--run-native','--toolchain-proof',str(ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json'),'--output',str(out/'native')],cwd=out,log=out/'command.log',timeout=max(.001,188-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
    current=p.tool_manifest()==tools
    wall=time.monotonic()-START;full=cpu()-CPU0
    passed=process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] and current and max(wall,full)+2<=190
    record=dict(schema=1,accepted=False,status='completed' if passed else 'failed',passed=passed,source_current=current,process=process,tools=tools,git_head=tools['git_head'],controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'command.log'),wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,whole_wall_full_cpu_cap_seconds=190,scope='One sequential owned fullSCH/hidden later field paired diagnostic on production1000 and explicit1007. Existing shared Native/refill/original-shell/PRL/process readers. No engine/GUI/production admission or routing improvement claim.')
    def remaining():return max(0,min(188-(time.monotonic()-START),188-(cpu()-CPU0)))
    def stable():
        if p.tool_manifest()!=tools or p.sha(Path(__file__))!=record['controller_sha256']:raise p.Rejected('frozen enclosure source changed')
        if p.sha(out/'command.log')!=record['log_sha256']:raise p.Rejected('Native enclosure log changed')
        if remaining()<=0:raise p.Rejected('whole enclosure budget exhausted')
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
        record['passed']=bool(passed and record['status']=='completed' and remaining()>0)
    record['cost_scope']='Samples before shared guarded publication; all final callbacks and literal readbacks remain under188s wall/fullCPU with2s final allowance within190s. No comparative routing budget or speedup claim.'
    f.publish(out,record,stable,account,remaining,final_check=stable)
    print(json.dumps({k:record[k] for k in ('passed','source_current','status','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
