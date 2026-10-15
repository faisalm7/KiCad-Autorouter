"""Fresh current-source distribution installation039; lead-only heavy execution."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
HEAD='3a5a54c3afa91b4e0526a942e4f8a2b2635016f7'
outer=ROOT/'.runs/installation-039-execution';outer.mkdir()
tools=p.tool_manifest()
if tools['git_head']!=HEAD:raise p.Rejected('freeze installation039 against the intended clean source checkpoint')
argv=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/install_smoke.py'),
      '--output',str(ROOT/'.runs/installation-039'),'--guidance','native','--source-mode','distribution']
process=run(argv,cwd=outer,log=outer/'command.log',timeout=max(.001,598-(time.monotonic()-START)),
    max_log_bytes=128*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=4*1024**3)
current=p.tool_manifest()==tools
wall=time.monotonic()-START;full=cpu()-CPU0
record=dict(schema=1,process=process,tools=tools,git_head=HEAD,source_current=current,
    wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,
    whole_delivery_within_budget=max(wall,full)+2<=600,wrapper_sha256=p.sha(Path(__file__)),
    log_sha256=p.sha(outer/'command.log'),
    scope='Current verified committed source distribution, independent venv and cached engine copy; existing fixed22offline commands and actual Native60mm smoke, followed by targeted installed chain/adaptive strategy/paired/storage/preferences-freshness controls. All implementation/source/tool/distribution inventory checks remain. SameMac/apps/cache, PCB-only; not freshOS/fullinstalledsuite/GUI/human or comparative routing qualification.')
p.save_json(outer/'execution.json',record)
print(json.dumps({key:record[key] for key in ('source_current','wall_seconds','full_cpu_seconds','whole_delivery_within_budget')}))
raise SystemExit(0 if current and record['whole_delivery_within_budget'] and process['status']=='success'
    and process['exit_code']==0 and process['cleanup_complete'] else 2)
