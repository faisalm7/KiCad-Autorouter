"""Bounded installed GUI workflow without wx; software intent, not GUI/human proof."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
import argparse,json,sys,signal
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--project',choices=['push-button-led','nus-usb-led'],required=True);ap.add_argument('--method',choices=['route','improve'],required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
ROOT=Path('/Users/faisal/Projects/KiCad-Autorouter-local');BASE=ROOT/'.runs/installation-050';CLONE=BASE/'checkout';sys.path.insert(0,str(CLONE));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,gui,handoff as h,floor_route as f
from scripts import install_smoke as install
assert c.ROOT==CLONE and Path(sys.executable)==CLONE/'.venv/bin/python' and Path(sys.prefix).resolve()==CLONE/'.venv'
planpath=CLONE/'.runs/installed-comparison-003/protocol.json';assert p.sha(planpath)=='561f1326e88b3ce8f5144d063c1970b16d5537f800081f748e81ad1612dc6ebd';plan=f.read_json(planpath)
source=Path(plan['cases'][a.project]['source']);original=plan['cases'][a.project]['files'];preset=planpath.parent/'presets'/a.project/('route.json' if a.method=='route' else 'improve.json');settings=preset.read_bytes();selfpin=p.sha(Path(__file__));out=Path(a.output);assert out.resolve()==out and not out.exists();out.mkdir();owner={};h.capture_destination(owner,out)
base=f.read_json(BASE/'result.json');selected=install.distribution_listing((BASE/'03-source-files.log').read_text());inventory=f.read_json(BASE/'source-tracked.json')
def fresh():
 assert p.sha(Path(__file__))==selfpin and p.tree_hash(source.parent)==original
 assert p.tool_manifest()==base['native']['tools']
 assert install.tracked_inventory(CLONE,selected)=={name:inventory[name] for name in selected.split('\0') if name}
 assert install.git_identity(CLONE,plan['git_head'])==base['git_identity_witnesses'][str(CLONE)]
 assert preset.read_bytes()==settings and h.owned_destination(owner)==out
fresh();flow=gui.Request(str(source),str(out),settings.decode(),True,a.method).prepare();processes=[]
report=dict(schema=1,accepted=False,workflow_delivered=False,status='failed',scope='Installed production GUI Request/Workflow/CliJob without window; explicit SOFTWARE TEST accept intent. Not an actual GUI interaction, human review or a repaired full comparison.',project=a.project,method=a.method,installed_head=plan['git_head'],source=str(source),source_hashes=original,settings=json.loads(settings),workspace=str(flow.workspace),driver_sha256=selfpin,processes=processes)
def interrupted(*_):raise KeyboardInterrupt
for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
try:
 for stage in ('preview','route','review','choice','export','verify_export'):
  fresh();left=min(210-(time.monotonic()-START),210-(cpu()-CPU0));assert left>1,'whole diagnostic delivery reserve exhausted'
  choice='accept' if stage=='choice' else None;job=gui.CliJob();log=out/(stage+'.log');argv=flow.command(stage,choice=choice)
  process=job.run(argv,log,timeout=min(flow.timeout(stage),left));processes.append(dict(stage=stage,process=process,log_sha256=p.sha(log)))
  job.adopt(flow,stage,process,log,choice=choice)
 report.update(workflow_delivered=True,status='completed')
except (Exception,KeyboardInterrupt) as exc:
 report.update(workflow_delivered=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
fresh();report.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_cpu_seconds=cpu()-CPU0,whole_budget_seconds=240,publication_allowance_seconds=2,external_exit_required=True)
raw=flow.workspace/'route/result.json'
if raw.is_file():
 data=f.read_json(raw);report.update(route_receipt_sha256=p.sha(raw),route_status=data.get('status'),native=data.get('native'),metrics=data.get('metrics'))
if max(report['sampled_wall_seconds'],report['sampled_full_cpu_seconds'])+2>240:report.update(workflow_delivered=False,status='budget_exceeded')
p.save_json(out/'result.json',report);fresh()
raise SystemExit(0 if report['workflow_delivered'] and report['status']=='completed' else 130 if report['status']=='cancelled' else 2)
