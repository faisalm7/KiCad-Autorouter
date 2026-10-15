"""Fresh current-source distribution installation043; lead-only heavy execution."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
HEAD=sys.argv[1]
outer=ROOT/'.runs/installation-043-execution';outer.mkdir();owner={};h.capture_destination(owner,outer)
tools=p.tool_manifest()
if tools['git_head']!=HEAD:raise p.Rejected('freeze installation043 against the intended clean source checkpoint')
argv=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/install_smoke.py'),
      '--output',str(ROOT/'.runs/installation-043'),'--guidance','native','--source-mode','distribution']
process=run(argv,cwd=outer,log=outer/'command.log',timeout=max(.001,598-(time.monotonic()-START)),
    max_log_bytes=128*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=4*1024**3)
current=p.tool_manifest()==tools
wall=time.monotonic()-START;full=cpu()-CPU0
passed=bool(current and max(wall,full)+2<=600 and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
base=ROOT/'.runs/installation-043';child=f.read_json(base/'result.json');child_pin=p.sha(base/'result.json');child_literal=f.canonical(child)
record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'failed',process=process,tools=tools,git_head=HEAD,source_current=current,
    wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,
    whole_delivery_within_budget=max(wall,full)+2<=600,wrapper_sha256=p.sha(Path(__file__)),
    log_sha256=p.sha(outer/'command.log'),
    scope='Current verified committed source distribution, independent venv and cached engine copy; existing fixed22offline commands and actual Native60mm default smoke. Separate current angle/provenance targeted controls and owned-v2 fullSCH tuned-free-angle installed execution remain required. Same Mac/apps/cache, offline; no freshOS/full installed suite/GUI/human/comparative qualification.')
record['child_receipt_sha256']=child_pin
record['completed_evidence']=f.evidence_inventory(outer)
def remaining():return min(598-(time.monotonic()-START),598-(cpu()-CPU0))
def stable():
 h.owned_destination(owner)
 if (p.tool_manifest()!=tools or p.sha(base/'result.json')!=child_pin or f.canonical(f.read_json(base/'result.json'))!=child_literal
     or f.evidence_inventory(outer)!=record['completed_evidence']):raise p.Rejected('base installation/source/material changed')
 if remaining()<=0:raise p.Rejected('base installation whole budget exhausted')
def account():
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,whole_delivery_within_budget=remaining()>0)
 record['passed']=bool(passed and record['status']=='completed' and remaining()>0)
 if record['status']!='completed':record['source_current']=False
f.publish(outer,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
stored=f.read_json(outer/'result.json')
print(json.dumps({key:stored[key] for key in ('passed','status','source_current','wall_seconds','full_cpu_seconds','whole_delivery_within_budget')}))
raise SystemExit(0 if stored.get('passed') is True and stored.get('status')=='completed' else 2)
