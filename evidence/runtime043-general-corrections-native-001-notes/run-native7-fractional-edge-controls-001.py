"""One fresh fractional-owned Native qualification, existing shared controller."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
HEAD='6ec7ad2344ed060d5e0971965ef05bd9de68925d';tools=p.tool_manifest();assert tools['git_head']==HEAD
base=R/'.runs/installation-020/checkout/.runs/install-native-smoke/candidate/smoke.kicad_pcb';before=p.tree_hash(base.parent)
O=R/'.runs/native7-fractional-edge-controls-execution-001';O.mkdir();out=R/'.runs/native7-fractional-edge-controls-001'
command=[str(R/'.venv/bin/python'),'-B',str(R/'scripts/native_edge_controls.py'),'--valid',str(base),'--output',str(out),'--fractional-edge','--native-version','10.0.7']
pins={n:p.sha(R/n) for n in ('scripts/native_edge_controls.py','autorouter/native_edge.py','tests/test_native_edge.py')}
plan=dict(schema=1,tools=tools,git_head=HEAD,command=command,base=str(base),base_inventory=before,code_sha256=pins,controller_sha256=p.sha(Path(__file__)),whole_wall_full_cpu_seconds=180,publication_allowance_seconds=2,scope='Explicit pinned10.0.7 diagnostic fractional-owned outline/export/obstacle/shared edge replay plus actual positive/edge/rule-tamper Native controls. No schematic supplied by shared controller, not final product or IR completion. Previous10.0.0 controls and original failed042 cohort unchanged.')
p.save_json(O/'protocol.json',plan);planpin=p.sha(O/'protocol.json')
process=run(command,cwd=O,log=O/'command.log',timeout=max(.001,178-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
current=p.tool_manifest()==tools and p.tree_hash(base.parent)==before and all(p.sha(R/n)==pin for n,pin in pins.items()) and p.sha(O/'protocol.json')==planpin
actor=f.read_json(out/'result.json') if (out/'result.json').exists() else None
wall=time.monotonic()-START;full=cpu()-CPU0;passed=bool(current and actor and actor['all_passed'] and actor['transport']['passed'] and max(wall,full)+2<=180 and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True)
r=dict(schema=1,passed=passed,source_current=current,tools=tools,process=process,wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,controller_sha256=p.sha(Path(__file__)),protocol_sha256=planpin,actor_result_sha256=p.sha(out/'result.json') if actor else None,log_sha256=p.sha(O/'command.log'),scope=plan['scope'])
p.save_json(O/'execution.json',r);print(json.dumps({k:r[k] for k in ('passed','source_current','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if passed else 2)
