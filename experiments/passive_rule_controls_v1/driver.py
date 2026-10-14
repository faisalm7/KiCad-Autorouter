"""One new owned backdrill diagnostic, using existing native control helpers.

No routing or machining admission. The earlier counterbore controls are not rerun.
"""
from pathlib import Path
import argparse,copy,json,signal,sys,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,floor_route as f,handoff as h,placement_clearance as io
from experiments.modern_semantics_controls_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
SECONDS=60;LIMIT=20*1024**2

def experiment(output,*,run_native=False):
 if run_native is not True:raise p.Rejected('explicit --run-native required')
 started=time.monotonic();cpu0=h.cpu_seconds();remaining=lambda:min(SECONDS-time.monotonic()+started,SECONDS-h.cpu_seconds()+cpu0)
 out=h.real_path(output,existing=False)
 if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('fresh direct checkout output required')
 job=shared.ControlJob(out,SECONDS,remaining);owner={};h.capture_destination(owner,out)
 record={'schema':1,'kind':'passive-rule-backdrill-native-control','accepted':False,'controls_passed':False,'status':'incomplete','budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'routing_executed':False,'machining_support':False}
 source_before=shared.inventory(shared.PIC.parent);tools=p.tool_manifest();code=None;source=None
 def owned():h.owned_destination(owner)
 def size():return shared.size(out)
 def account():
  record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=h.cpu_seconds()-cpu0,output_bytes=size(),steps=job.steps)
  record['within_budget']=remaining()>0 and record['output_bytes']<=LIMIT
  if not record['within_budget'] or record['status']!='controls_passed':record['controls_passed']=False
  if not record['within_budget']:record['status']='budget_exceeded'
 def stable():
  owned()
  if p.tool_manifest()!=tools or shared.inventory(shared.PIC.parent)!=source_before:raise p.Rejected('pinned runtime/original changed')
  if code is not None and any(p.sha(ROOT/n)!=v for n,v in code.items()):raise p.Rejected('control source changed')
  if source is not None and p.tree_hash(source)!=record['source_hashes']:raise p.Rejected('owned control source changed')
  if record['controls_passed']:
   native=f.check_drc_stage(out,{'steps':job.steps},'backdrill-drc',source/'owned.kicad_pcb',out/'backdrill-drc-input/owned.kicad_pcb',False,record['source_hashes'])
   if native!=record['native'] or p.sha(out/'backdrill-drc.json')!=record['native_report_sha256']:raise p.Rejected('final native control changed')
 try:
  if source_before!=f.read_json(Path(__file__).with_name('PROTOCOL.json'))['original_pic_inventory']:raise p.Rejected('prospective original fixture source differs')
  extras=[Path(__file__),Path(__file__).with_name('PROTOCOL.json'),Path(shared.__file__),Path(shared.fixture.__file__),Path(shared.checks.__file__)]
  freeze=io.capture_freeze({**tools,'implementation_sha256':{**tools['implementation_sha256'],**{str(n.relative_to(ROOT)):p.sha(n) for n in extras}}});code=freeze['files_sha256']
  copy_bytes({n:io.read_bytes(ROOT/n) for n in code},out/'code')
  record.update(tools=tools,code_sha256=code,original_project_inventory=source_before)
  raw,project,scene=shared.fixture.prepare(sx.read(shared.PIC),f.read_json(shared.PIC.with_suffix('.kicad_pro')),'positive')
  board=sx.parse(raw.decode());pad=sx.children(sx.children(board,'footprint')[2],'pad')[0]
  pad.append(['backdrill',['size','1.2'],['layers','"F.Cu"','"B.Cu"']])
  source=out/'original';copy_bytes({'owned.kicad_pcb':(sx.dump(board)+'\n').encode(),'owned.kicad_pro':(json.dumps(project,indent=2)+'\n').encode()},source)
  record['source_hashes']=p.tree_hash(source);record['scene']=scene
  try:p.preflight(source/'owned.kicad_pcb')
  except p.Rejected as exc:
   if 'backdrilled/post-machined pads or vias not qualified' not in str(exc):raise
   record['production_preflight_rejected']=str(exc)
  else:raise p.Rejected('machining source admitted to routing')
  native=job.drc('backdrill-drc',source/'owned.kicad_pcb')
  actual=f.check_drc_stage(out,{'steps':job.steps},'backdrill-drc',source/'owned.kicad_pcb',out/'backdrill-drc-input/owned.kicad_pcb',False,record['source_hashes'])
  if actual!=native:raise p.Rejected('actual report/binding differs')
  hits=[r for r in native['findings'] if r['type']=='track_on_post_machined_layer']
  wanted={scene['tracks'][1]['uuid'],scene['pads'][2]['uuid']}
  matched=len(hits)==1 and hits[0]['severity']=='error' and {i['uuid'] for i in hits[0]['items']}==wanted
  record.update(native=native,native_report_sha256=p.sha(out/'backdrill-drc.json'),final_candidate_sha256=p.sha(source/'owned.kicad_pcb'),expected_items=sorted(wanted),native_detection_passed=matched)
  if not matched or p.native_accepted(native):raise p.Rejected('declared removed-copper native finding not detected/rejected')
  record.update(status='controls_passed',controls_passed=True)
 except (Exception,KeyboardInterrupt) as exc:record.update(status='failed',error=type(exc).__name__+': '+str(exc))
 finally:
  f.publish(out,record,stable,account,remaining,owned=owned)
  try:
   stable();account()
   if record['controls_passed'] and remaining()<=0:raise p.Rejected('control final publication cap')
  except (Exception,KeyboardInterrupt) as exc:
   record.update(status='failed',controls_passed=False,error=type(exc).__name__+': '+str(exc));f.publish(out,record,lambda:(_ for _ in ()).throw(p.Rejected(record['error'])),account,remaining,owned=owned)
 return record

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',required=True);args=parser.parse_args()
 handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
 def interrupted(*_):raise KeyboardInterrupt
 try:
  for sig in handlers:signal.signal(sig,interrupted)
  record=experiment(args.output,run_native=args.run_native)
 finally:
  for sig,handler in handlers.items():signal.signal(sig,handler)
 print(json.dumps({k:record.get(k) for k in ('status','error','controls_passed','wall_seconds','total_cpu_seconds')}));return 0 if record['controls_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
