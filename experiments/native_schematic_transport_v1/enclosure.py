"""Fixed one-shot, sequential, bounded owned1007 transport invocation.

SPDX-License-Identifier: GPL-3.0-or-later
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import fcntl,json,os,stat,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.native_schematic_transport_v1.driver import reference
prior_root,previous=reference()
out=ROOT/'.runs/native-schematic-transport-execution-002';out.mkdir();owner={};h.capture_destination(owner,out)
proof=ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json'
if p.sha(proof)!='26564ecd90268e463760270902d302445d9b0e6859105d3ed06e5976a8989c73':raise p.Rejected('fixed signed toolchain proof changed')
nt=p.ExperimentalNativeToolchain.from_record(f.read_json(proof)['experimental_native_toolchain'])
tools=p.tool_manifest(native_toolchain=nt);code={str(n):p.sha(n) for n in Path(__file__).resolve().parent.glob('*.py')}
lockpath=ROOT/'.runs/quality-experiment.lock';fd=os.open(lockpath,os.O_RDWR|os.O_NOFOLLOW)
with os.fdopen(fd,'r+') as lock:
    info=os.fstat(lock.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lock required')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    process=run([str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).with_name('driver.py')),'--output',str(out/'native')],cwd=out,log=out/'command.log',timeout=max(.001,176-previous['wall_seconds']-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
    childpath=out/'native/result.json';child=f.read_json(childpath) if childpath.is_file() else None
    material=p.tree_hash(out/'native') if (out/'native').is_dir() else None
    current=p.tool_manifest(native_toolchain=nt)==tools
    passed=(child is not None and child.get('passed') is True and child.get('status')=='completed'
        and child.get('accepted') is False and child.get('production_admitted') is False and child.get('tools')==tools
        and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']
        and not process['log_truncated'] and current)
    record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'failed',production_admitted=False,
                tools=tools,process=process,controller_sha256=p.sha(Path(__file__)),code_sha256=code,
                child_receipt_sha256=p.sha(childpath) if child else None,child_material_sha256=material,
                log_sha256=p.sha(out/'command.log'),whole_wall_full_cpu_cap_seconds=180,prior_charged_enclosure_costs=previous,
                scope='One new owned explicit1007 ordinary native transport. All child source/export/JAR/SES/import/refill/class/fullSCH/field/metrics/readback costs included; previously completed area/field workers are prerequisites only, never rerun. No comparative quality or production/default/GUI/installation support claim.')
    def remaining():return min(178-previous['wall_seconds']-(time.monotonic()-START),178-previous['full_cpu_seconds']-(cpu()-CPU0))
    def stable():
        h.owned_destination(owner)
        reference()
        if p.tool_manifest(native_toolchain=nt)!=tools or any(p.sha(Path(n))!=pin for n,pin in code.items()):raise p.Rejected('frozen transport enclosure source changed')
        if p.sha(out/'command.log')!=record['log_sha256']:raise p.Rejected('transport enclosure log changed')
        if child is None or p.sha(childpath)!=record['child_receipt_sha256'] or f.canonical(f.read_json(childpath))!=f.canonical(child):raise p.Rejected('child transport receipt changed')
        if p.tree_hash(out/'native')!=material:raise p.Rejected('transport child completed evidence changed')
        if record['passed']:
            route=f.read_json(out/'native/route/result.json')
            p.check_experimental_local_settings(out/'native/route',route,nt)
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
        if remaining()<=0:record.update(passed=False,status='budget_exceeded')
    f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    print(json.dumps({k:record[k] for k in ('passed','status','wall_seconds','full_cpu_seconds')}))
    raise SystemExit(0 if record['passed'] else 2)
