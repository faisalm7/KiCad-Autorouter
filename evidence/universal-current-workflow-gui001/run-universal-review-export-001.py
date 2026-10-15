import time,resource
START=time.monotonic()
def cpu():
 return sum(v.ru_utime+v.ru_stime for v in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.runs/universal-review-export-execution-001';out.mkdir();tools=p.tool_manifest();controller=ROOT/'scripts/qualify_review_export.py';pin=p.sha(controller)
assert tools['git_head']=='e78f5343ec401ee7df82957eaced84fc96f2b9f3'
qualified=f.read_json(ROOT/'.runs/universal-preparation950-001/execution.json')
assert qualified['passed'] is True and qualified['source_current'] is True and next(x for x in qualified['final_charged_results'] if x['id']=='C_feedback')['accepted'] is True
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(controller),'--receipt',str(ROOT/'.runs/universal-preparation950-001/C_feedback/result.json'),'--render','--output',str(ROOT/'.runs/review-export-native-universal-C-001'),'--run-native'],cwd=out,log=out/'command.log',timeout=max(.001,618-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
current=p.tool_manifest()==tools and p.sha(controller)==pin
record=dict(schema=1,process=process,tools=tools,source_current=current,controller_sha256=pin,wrapper_sha256=p.sha(Path(__file__)),wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2,scope='One retained actual normal Universal-C: existing review/render/testaccept/reject/freshNativeexport helpers only, no rerouting. Testintent is nothumanPCBapproval; original rules/geometry/PRL/source/warnings/proofs stay mandatory. Oldworkflow/GUI/cancellation controls not repeated; all81originalwarnings/fiveignored retained. Requires qualified cumulative750 comparison before separate product check.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('source_current','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if current and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] else 2)
