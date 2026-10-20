"""Two bounded owned Native/invariant controls using shared validators.
No custom acceptance rule: Native scope and original protection remain distinct.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,shutil,copy,uuid,argparse,hashlib
from decimal import Decimal
ap=argparse.ArgumentParser();ap.add_argument('--protocol',required=True);ap.add_argument('--protocol-sha256',required=True);parsed=ap.parse_args()
protocol=Path(parsed.protocol);raw=protocol.read_bytes();assert hashlib.sha256(raw).hexdigest()==parsed.protocol_sha256
plan=json.loads(raw);args=argparse.Namespace(**{key:plan[key] for key in ('runtime','receipt','output')})
runtime=Path(args.runtime);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,floor_route as f,sexpr as sx,strategy as s,local_settings as local,handoff as h,schematic_field_evidence as fields
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256'] and p.sha(Path(__file__))==plan['controller_sha256']
receipt=Path(args.receipt);before_receipt=p.sha(receipt);data=f.read_json(receipt);assert data['single_selection_policy']==s.SINGLE_SELECTION_POLICY
assert p.check_result(receipt)['current']
source=Path(data['source']);hashes=p.tree_hash(source.parent);assert hashes==data['source_hashes'];original=sx.read(source)
protected=[r for r in p.routes(original) if p.locked(r)];assert len(protected)==1
candidate=Path(data['candidate']);positive_inventory=f.evidence_inventory(receipt.parent);tools=p.tool_manifest();selfpin=p.sha(Path(__file__))
out=h.real_path(args.output,existing=False)
assert out.parent==runtime/'.runs' and out.name.startswith('native7-comparison-control-') and not out.exists()
assert all(root!=out and root not in out.parents and out not in root.parents for root in (source.parent,receipt.parent,candidate.parent))
out.mkdir(mode=0o700);owner={};h.capture_destination(owner,out);rows=[];stages=[]
def check_native(job,name,board,before,native,*,saved=False):
 target=job.out/'refill'/board.name if saved else job.out/(name+'-input')/board.name
 assert f.check_drc_stage(job.out,{'steps':job.steps},name,board,target,saved,before,schematic_parity=not saved,sandboxed=False)==native
 stages.append((job,name,board,target,saved,before,native))
record=dict(schema=1,accepted=False,production_admitted=False,project_complete=False,actual_GUI=False,human_review=False,control_passed=False,status='failed',source=str(source),source_hashes=hashes,positive_receipt=str(receipt),positive_sha256=before_receipt,tools=tools,cases=rows,whole_wall_full_CPU_seconds=120,scope='Two owned copied-candidate Native/invariant controls after fresh installed Improve positive. No solver rerun, original edit, GUI, false-acceptance rate or electrical claim.')
try:
 for mode in ('short','protected-width'):
  assert min(115-(time.monotonic()-START),115-(cpu()-CPU0))>20
  job=p.Job(out/mode,min(40,110-(time.monotonic()-START),110-(cpu()-CPU0)),protect_local_settings=True)
  copied=job.out/'candidate'/source.name;shutil.copytree(candidate.parent,copied.parent);tree=sx.read(copied)
  row=dict(case=mode,passed=False,steps=job.steps);rows.append(row)
  if mode=='short':
   segment=['segment',['start','12','10'],['end','12','16'],['width','0.3'],['layer','"F.Cu"'],['net','"ROUTE"'],['uuid',json.dumps(str(uuid.uuid4()))]]
   tree.append(p.convert_route_nets(segment,['kicad_pcb'],tree));sx.write(copied,tree);row['pre_native_sha256']=p.sha(copied)
   digest,native=p.validate_candidate(job,original,copied,hashes,protected,default_target_policy=True)
   row.update(candidate_sha256=digest,native=native,report_sha256=p.sha(job.out/'final-drc.json'))
   assert not p.native_accepted(native) and native['blocking']>0 and any(r['type']=='shorting_items' for r in native['findings'])
   expected=dict(hashes);expected[copied.name]=digest
   check_native(job,'final-drc',copied,expected,native)
   refill_before=dict(hashes);refill_before[copied.name]=row['pre_native_sha256']
   check_native(job,'refill-drc',job.out/'refill'/copied.name,refill_before,p.parse_report(job.out/'refill-drc.json',copied.name),saved=True)
   basis=s.native7_default_target_basis(receipt.parent,data)
   p.check_final_netclass_evidence(job.out,{'steps':job.steps},copied,protected,default_target_policy=True,default_target_basis=basis)
   row['rejection']='Actual original-rule full-schematic Native short'
  else:
   chosen=next(r for r in protected if r[0]=='segment');changed=next(r for r in p.routes(tree) if r==chosen);width=sx.one(changed,'width');width[1]=format(Decimal(width[1])+Decimal('0.000001'),'f');sx.write(copied,tree)
   row['mutated_sha256']=p.sha(copied);before=dict(hashes);before[copied.name]=p.sha(copied)
   native=job.drc('diagnostic-drc',copied,schematic_parity=True);row['diagnostic_native']=native
   assert p.native_accepted(native)
   check_native(job,'diagnostic-drc',copied,before,native)
   count=len(job.steps)
   try:p.validate_candidate(job,original,copied,hashes,protected,default_target_policy=True)
   except p.Rejected as exc:assert 'protected route changed' in str(exc);row['rejection']=str(exc)
   else:raise AssertionError('protected original mutation accepted')
   assert len(job.steps)==count
  # These are diagnostic Jobs, not standalone route receipts with code snapshots.
  # Actual Native input/process/field readers above and final PRL replay below
  # are the same shared seams used by the existing owned invalid controls.
  row['passed']=True
 assert p.check_result(receipt)['current']
 assert p.sha(receipt)==before_receipt and f.evidence_inventory(receipt.parent)==positive_inventory and p.tree_hash(source.parent)==hashes
 assert p.tool_manifest()==tools and p.sha(Path(__file__))==selfpin
 assert protocol.read_bytes()==raw and p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']
 for job,name,board,target,saved,before,native in stages:
  assert f.check_drc_stage(job.out,{'steps':job.steps},name,board,target,saved,before,schematic_parity=not saved,sandboxed=False)==native
  if fields.has_fields(native.get('findings',[])):fields.check_local_settings(job.out,name,f.read_json(job.out/(name+'-binding.json')))
 assert h.owned_destination(owner)==out
 local.check_final_events([*s.native7_packets(receipt.parent,data),*((out/row['case'],{'steps':row['steps']}) for row in rows)],c.CLI)
 record.update(control_passed=True,status='completed')
except (Exception,KeyboardInterrupt) as exc:record.update(error=type(exc).__name__+': '+str(exc))
record.update(wall_seconds=time.monotonic()-START,total_cpu_seconds=cpu()-CPU0,external_exit_required=True)
if max(record['wall_seconds'],record['total_cpu_seconds'])+2>120:record.update(control_passed=False,status='budget_exceeded')
p.save_json(out/'result.json',record);print(json.dumps(dict(control_passed=record['control_passed'],status=record['status'],error=record.get('error'))));raise SystemExit(0 if record['control_passed'] else 2)
