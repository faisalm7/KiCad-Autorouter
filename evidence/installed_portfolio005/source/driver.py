"""Compose the unchanged installed portfolio and production review/export helpers."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,json,sys,signal
ap=argparse.ArgumentParser();ap.add_argument('--project',choices=['push-button-led','nus-usb-led'],required=True);ap.add_argument('--work',required=True);a=ap.parse_args()
ROOT=Path('/Users/faisal/Projects/KiCad-Autorouter-local');CLONE=ROOT/'.runs/installation-050/checkout';sys.path.insert(0,str(CLONE));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h,review_export as ex
from scripts import experiment_quality as q,experiment_portfolio as portfolio,experiment_paired as paired
protocol=ROOT/'.runs/competent-portfolio005-preparation/protocol.json';assert p.sha(protocol)=='c4af7cfbd4f77eacb33bd2b531c715f152fb0b98740d535e685aaa60285a6c0b';plan=f.read_json(protocol)
assert c.ROOT==CLONE and Path(sys.executable)==CLONE/'.venv/bin/python' and Path(sys.prefix).resolve()==CLONE/'.venv'
work=Path(a.work);assert CLONE/'.runs' in work.parents;child=work/'child';child.mkdir();owner={};h.capture_destination(owner,child);selfpin=p.sha(Path(__file__));case=plan['cases'][a.project];board=Path(case['source']);record=dict(schema=1,accepted=False,workflow_delivered=False,status='failed',project=a.project,protocol_sha256=p.sha(protocol),driver_sha256=selfpin,source=str(board),source_hashes=case['source_hashes'],method_budget_seconds=120,whole_budget_seconds=240,software_test_intent_only=True)
def fresh():
 assert p.sha(protocol)==record['protocol_sha256'] and p.sha(Path(__file__))==selfpin and p.tool_manifest()==plan['tools'] and p.tree_hash(board.parent)==case['source_hashes'] and h.owned_destination(owner)==child
def interrupted(*_):raise KeyboardInterrupt
for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
try:
 fresh();frozen=portfolio.freeze(board)
 result=portfolio.experiment(child/'portfolio',a.project,budget=120,allocation='remaining',outer_ceiling=120)
 selected=paired.verify_portfolio(child/'portfolio',result,board,frozen);record['portfolio']=selected
 if selected['accepted'] is not True:raise p.Rejected('fixed portfolio did not deliver an eligible selected route: '+str(selected['status']))
 receipt=Path(selected['selected']['result']);p.check_result(receipt);h.review_copy(receipt,child/'review',render=True);h.review_choice(child/'review/review.json',child/'choice','accept')
 left=min(120,210-(time.monotonic()-START),210-(cpu()-CPU0));assert left>=30,'insufficient fresh export reserve'
 export=ex.export(child/'choice/choice.json',child/'export',left);ex.check_export(child/'export/export.json');assert export['export_accepted'] is True
 record.update(workflow_delivered=True,status='completed',selected_route_receipt=str(receipt),selected_route_sha256=p.sha(receipt),candidate_sha256=export['candidate_sha256'],native=export['native'],metrics=export['metrics'])
except (Exception,KeyboardInterrupt) as exc:record.update(workflow_delivered=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
fresh();record.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2,external_complete_exit_required=True)
if max(record['sampled_wall_seconds'],record['sampled_full_cpu_seconds'])+2>240:record.update(workflow_delivered=False,status='budget_exceeded')
p.save_json(child/'result.json',record);fresh()
raise SystemExit(130 if record['status']=='cancelled' else 0 if record['workflow_delivered'] and record['status']=='completed' else 2)
