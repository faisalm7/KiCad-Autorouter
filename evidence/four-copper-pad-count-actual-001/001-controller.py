"""Two sequential, observer-only Native pad-count controls using existing helpers.
SPDX-License-Identifier: GPL-3.0-or-later
No DRC, routing, embedded-pad manufacture or source-board admission claim.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import fcntl,hashlib,json,os,signal,stat,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,local_settings as ls,netclass,sexpr as sx,config as c
from experiments.hfe_original_native_v1 import driver as original
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.four_copper_class_transport_v1 import fixture
HEAD=sys.argv[1];original.clean(HEAD)
proof=f.read_json(original.PROOF)
if p.sha(original.PROOF)!=original.PROOF_PIN:raise p.Rejected('signed bundle proof changed')
nt7=p.ExperimentalNativeToolchain.from_record(proof['experimental_native_toolchain'])
tools={name:p.tool_manifest(native_toolchain=nt) for name,nt in [('1000',None),('1007',nt7)]}
worker=ROOT/'.runs/four-cu-inner-count-worker-001.py';code={str(x):p.sha(x) for x in [worker,Path(__file__),ROOT/'experiments/four_copper_class_transport_v1/fixture.py']}
packet=fixture.files();tree=sx.parse(packet[fixture.STEM+'.kicad_pcb'].decode())
for fp in sx.children(tree,'footprint'):
 ref=next(sx.unquote(x[2]) for x in sx.children(fp,'property') if sx.unquote(x[1])=='Reference')
 pad=sx.one(fp,'pad')
 if ref=='J1':sx.one(pad,'layers')[:]=['layers','"In1.Cu"']
 if ref=='J2':
  pad[2]='thru_hole';pad.append(['drill','0.8']);sx.one(pad,'layers')[:]=['layers','"*.Cu"','"*.Mask"']
packet[fixture.STEM+'.kicad_pcb']=(sx.dump(tree)+'\n').encode()
expected_pads={}
for fp in sx.children(tree,'footprint'):
 ref=next(sx.unquote(x[2]) for x in sx.children(fp,'property') if sx.unquote(x[1])=='Reference')
 for pad in sx.children(fp,'pad'):
  uid=sx.unquote(sx.one(pad,'uuid')[1]);names=[sx.unquote(x) for x in sx.one(pad,'layers')[1:]]
  expected_pads[uid]=dict(reference=ref,number=sx.unquote(pad[1]),net=sx.unquote(sx.one(pad,'net')[1]),layers=[x for x in netclass.FOUR_COPPER_NAMES if '*.Cu' in names or x in names])
pins={n:hashlib.sha256(raw).hexdigest() for n,raw in packet.items()}
OUT=ROOT/'.runs/four-cu-inner-count-001';OUT.mkdir();owner={};h.capture_destination(owner,OUT)
plan=dict(schema=1,git_head=HEAD,tools=tools,code_sha256=code,source_files_sha256=pins,scope='Newly authored observer-only source: one ROUTE pad In1-only and one PTH all4. Old outer census must count ROUTE1; new Native class census ROUTE2. No DRC/routing/manufacturing qualification.',limits=dict(whole_wall_full_cpu_seconds=90,publication_allowance_seconds=2))
p.save_json(OUT/'plan.json',plan);planpin=p.sha(OUT/'plan.json')
def remaining():return min(88-(time.monotonic()-START),88-(cpu()-CPU0))
record=dict(schema=1,accepted=False,passed=False,status='failed',production_support_qualified=False,git_head=HEAD,tools=tools,plan_sha256=planpin,cases=[],scope=plan['scope'])
def cancel(*_):raise KeyboardInterrupt
for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,cancel)
fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
with os.fdopen(fd,'r+') as lock:
 info=os.fstat(lock.fileno())
 if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary quality lane required')
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  for name,nt in [('1000',None),('1007',nt7)]:
   job=original.BoundJob(OUT/name,30,remaining,native_toolchain=nt,protect_local_settings=True)
   copy_bytes(packet,job.out/'input');board=job.out/'input'/(fixture.STEM+'.kicad_pcb');before=p.tree_hash(board.parent)
   output=job.out/'api.json';argv=[str(nt.python if nt else c.PYTHON),str(worker),json.dumps(nt.record() if nt else None,sort_keys=True),str(output),str(board)]
   step='four-cu-inner-count';ls.protected_step(job,step,argv);api_pin=p.sha(output);data=f.read_json(output)
   if p.sha(output)!=api_pin:raise p.Rejected('API snapshot changed while reading')
   pads=data['pads'];mapping=data['netclasses'];expected_version=nt.expected_version if nt else '10.0.0'
   if (data.get('kind')!='actual-native-four-cu-api-class-census' or data.get('native_version')!=expected_version or data.get('source')!=str(board) or data.get('board_saved') is not False or data.get('routing_accepted') is not False
       or mapping.get('source')!=str(board) or mapping.get('board_sha256')!=before[board.name] or mapping.get('project_sha256')!=before[board.with_suffix('.kicad_pro').name] or mapping.get('board_saved') is not False
       or any(type(row.get('netcode')) is not int or row['netcode']<=0 for row in pads)
       or {row['uuid']:{key:row[key] for key in ('reference','number','net','layers')} for row in pads}!=expected_pads):raise p.Rejected('API/source exact pad/header identity differs')
   counts={n['name']:n['copper_pad_count'] for n in data['netclasses']['nets']}
   if (p.tree_hash(board.parent)!=pins or data['source_files_sha256']!=pins or len(pads)!=6 or len({r['uuid'] for r in pads})!=6
       or counts!={'ROUTE':2,'KEEP':2,'GND':2} or data['legacy_outer_counts']!={'ROUTE':1,'KEEP':2,'GND':2}
       or sum(r['net']=='ROUTE' and r['layers']==['In1.Cu'] for r in pads)!=1
       or sum(r['net']=='ROUTE' and r['layers']==list(netclass.FOUR_COPPER_NAMES) for r in pads)!=1):raise p.Rejected('actual inner-only/PTH census prediction differs')
   audit=netclass.audit_native(data['netclasses'],json.loads(board.with_suffix('.kicad_pro').read_text()),parent_policy=True,native_toolchain=nt)
   if p.sha(output)!=api_pin or f.canonical(f.read_json(output))!=f.canonical(data):raise p.Rejected('validated API snapshot changed before adoption')
   record['cases'].append(dict(api_literal=f.canonical(data),version=name,job=str(job.out),steps=job.steps,argv=argv,api_sha256=api_pin,source_files_sha256=before,legacy_outer_counts=data['legacy_outer_counts'],counts=counts,audit=audit))
  record.update(passed=True,status='completed')
 except (Exception,KeyboardInterrupt) as exc:record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or any(step.get('status')=='cancelled' for step in (job.steps if 'job' in globals() else [])) else 'failed',error=type(exc).__name__+': '+str(exc))
 for case in record['cases']:
  if p.sha(Path(case['job'])/'api.json')!=case['api_sha256'] or f.canonical(f.read_json(Path(case['job'])/'api.json'))!=case['api_literal']:raise p.Rejected('API changed before final material snapshot')
 material=original.material(OUT);record['completed_evidence']=material
 def stable():
  h.owned_destination(owner);original.clean(HEAD)
  if p.sha(OUT/'plan.json')!=planpin or original.material(OUT)!=material or any(p.sha(Path(n))!=v for n,v in code.items()):raise p.Rejected('frozen observer material changed')
  for name,nt in [('1000',None),('1007',nt7)]:
   if p.tool_manifest(native_toolchain=nt)!=tools[name]:raise p.Rejected('observer tools/HEAD changed')
  for case in record['cases']:
   job=Path(case['job']);board=job/'input'/(fixture.STEM+'.kicad_pcb')
   if p.tree_hash(board.parent)!=pins or p.sha(job/'api.json')!=case['api_sha256'] or f.canonical(f.read_json(job/'api.json'))!=case['api_literal']:raise p.Rejected('observer source/report changed')
   proc=f.process_check(job,case,'four-cu-inner-count',[*f.SANDBOX,*case['argv']]);ls.check_preserved(board.with_suffix('.kicad_prl'),pins,proc['local_settings_protection'])
  if remaining()<=0:raise p.Rejected('observer whole budget exhausted')
 def account():
  record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
  if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
  if record['status']!='completed':record['passed']=False
 f.publish(OUT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 row=f.read_json(OUT/'result.json');print(f.canonical({k:row.get(k) for k in ['passed','status','error','wall_seconds','full_cpu_seconds']}));raise SystemExit(0 if row.get('passed') and row.get('status')=='completed' else 2)
