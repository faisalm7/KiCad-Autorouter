"""Actual original-rule mechanism controls, using shared validation and publication."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,shutil,subprocess,hashlib,signal,argparse
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,sexpr as sx,floor_route as f,strategy as s,chain_proposals as cp,handoff as h
from experiments.native_components_v1.controls import OfflineJob,completed_inventory,check_completed
from experiments.chain_pruning_v1.fixture import recipe
SECONDS=90
def run(out):
 out=Path(out).absolute();assert out.parent==R/'.runs' and not out.exists();out.mkdir();owner={};h.capture_destination(owner,out)
 tools=p.tool_manifest();own={str(q.relative_to(R)):p.sha(q) for d in ('chain_pruning_v1','native_components_v1') for q in (R/'experiments'/d).glob('*.py')}
 for n,v in own.items():assert hashlib.sha256(subprocess.check_output(['git','show',tools['git_head']+':'+n],cwd=R)).hexdigest()==v
 original,redundant=recipe(sx.read(R/'fixtures/smoke/smoke.kicad_pcb'));source=out/'original';source.mkdir();board=source/'smoke.kicad_pcb';sx.write(board,original);shutil.copyfile(R/'fixtures/smoke/smoke.kicad_pro',board.with_suffix('.kicad_pro'));hashes=p.tree_hash(source)
 p.preflight(board);protected=[r for r in p.routes(original) if p.locked(r)];nets=s.zone_net_ids(original)
 batch=cp.build(original,nets,protected);wanted={s.route_id(r) for r in redundant};matches=[x for x in batch['proposals'] if set(x['route_ids'])==wanted]
 assert not batch['declined_reason'] and len(matches)==1 and len(wanted)==20
 whole=s.proposals(original,nets,protected,True)[0];one=dict(kind='owned-internal-singleton',net='"GND"',route_ids=[s.route_id(redundant[9])])
 record=dict(schema=1,kind='actual-endpoint-chain-mechanism-controls-v1',status='incomplete',passed=False,accepted=False,routing_accepted=False,production_admitted=False,tools=tools,source_sha256=hashes,extra_source_sha256=own,proposal_batch=batch,controls=[],scope='Owned constructed fixture, no engine/benchmark/gain claim. Full original immutable/protected/rules/refill/final checks. PCB-only schematic unavailable. Whole deletion must remain invalid; singleton may be Native-connected but quality-invalid.')
 completed={};material=None
 def remaining():return SECONDS-max(time.monotonic()-START,cpu()-CPU0)
 def stable():
  h.owned_destination(owner)
  assert remaining()>0 and tools==p.tool_manifest() and p.tree_hash(source)==hashes and all(p.sha(R/n)==v for n,v in own.items());check_completed(completed)
  if material is not None:assert f.evidence_inventory(out)==material
 def account():
  record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
  if remaining()<2:record.update(status='budget_exceeded',passed=False)
  if record['status']!='completed':record['passed']=False
 try:
  geometry=p.Job(out/'geometry',min(12,remaining()-4),protect_local_settings=True)
  context,context_pin=s._chain_context(geometry,board)
  record['geometry_steps']=geometry.steps
  record['geometry_receipt_sha256']=context_pin
  native_batch=cp.build(original,nets,protected,native_pads=context['pads'])
  assert p.sha(geometry.out/'floor-final-context.json')==context_pin
  assert not native_batch['declined_reason'] and len([x for x in native_batch['proposals'] if set(x['route_ids'])==wanted])==1
  record['native_proposal_batch']=native_batch;completed[geometry.out]=completed_inventory(geometry.out)
  incumbent=None
  for name,proposal in [('incumbent',None),('whole',whole),('single',one),('chain',matches[0])]:
   stable();job=OfflineJob(out/name,min(20,remaining()-4),protect_local_settings=True);candidate=job.out/'candidate'/board.name;shutil.copytree(source,candidate.parent)
   if proposal is not None:sx.write(candidate,s.delete_routes(original,proposal['route_ids'],nets,protected))
   entry=dict(case=name,proposal=proposal,passed=False);record['controls'].append(entry)
   try:
    digest,native=p.validate_candidate(job,original,candidate,hashes,protected)
    f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',job.out/'refill'/board.name,job.out/'refill'/board.name,True,{**hashes,board.name:p.sha(job.out/'pre-refill.kicad_pcb')})
    assert native==f.check_drc_stage(job.out,{'steps':job.steps},'final-drc',candidate,job.out/'final-drc-input'/board.name,False,{**hashes,board.name:digest})
    job.native('metrics','metrics',candidate,job.out/'metrics.json');metrics=f.read_json(job.out/'metrics.json')
    f.process_check(job.out,{'steps':job.steps},'metrics',[*f.SANDBOX,str(c.PYTHON),str(R/'autorouter/native.py'),'metrics',str(candidate),str(job.out/'metrics.json')])
    assert p.immutable(sx.read(candidate))==p.immutable(original) and all(r in p.routes(sx.read(candidate)) for r in protected) and p.tree_hash(source)==hashes
    if name=='incumbent':
     assert p.native_accepted(native) and native['warnings']==0;incumbent=(metrics,native)
    elif name=='whole':assert native['opens']>0 and not p.native_accepted(native)
    elif name=='single':assert native['opens']==0 and native['warnings']>0 and not s._improves(metrics,incumbent[0],native,incumbent[1])
    else:assert s._improves(metrics,incumbent[0],native,incumbent[1]) and p.native_accepted(native) and abs(incumbent[0]['track_length_mm']-metrics['track_length_mm']-13)<1e-8
    entry.update(passed=True,candidate_sha256=digest,native_report_sha256=p.sha(job.out/'final-drc.json'),native=native,metrics=metrics,protected_count=len(protected),steps=job.steps);completed[job.out]=completed_inventory(job.out)
   except BaseException:
    entry['steps']=job.steps;raise
  record.update(status='completed',passed=True)
 except BaseException as ex:record.update(status='failed',passed=False,reason=type(ex).__name__+': '+str(ex))
 account();material=f.evidence_inventory(out);record['completed_material']=material;f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 print(json.dumps({k:record.get(k) for k in ('status','passed','reason','wall_seconds','full_cpu_seconds')}));return record
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args()
 if not a.run_native:ap.error('--run-native required')
 def stop(*_):raise KeyboardInterrupt
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
 r=run(a.output);raise SystemExit(0 if r['status']=='completed' and r['passed'] is True else 2)
