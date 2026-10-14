"""Lead-only real three-class transport controls; no production admission.

Reuses shared native jobs, import/dimension checks, DRC binding, bounded
inventory, owned copier, committed freeze and publication. No wildcard matcher.
"""
from pathlib import Path
import argparse,copy,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,sexpr as sx,netclass as n,placement_clearance as io,handoff as h
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.original_project_native_v1.driver import completed_evidence
from experiments.licensed_acquisition_v1.fetch import cancellation
from experiments.netclass_parent_transport_v1 import fixture
from autorouter.strategy import _warning_signatures
SECONDS=180;LIMIT=20*1024**2
HERE=Path(__file__).resolve().parent

def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=2048,max_entries=4096)
def size(path):return sum(len(x) for x in io.inventory(path,contents=True,max_bytes=LIMIT,max_files=2048,max_entries=4096).values())
def observed(path,board,hashes):
 record=f.read_json(path)
 if (record.get('source')!=str(board) or record.get('board_sha256')!=hashes[board.name]
     or record.get('project_sha256')!=hashes[board.with_suffix('.kicad_pro').name] or record.get('board_saved') is not False):
  raise p.Rejected('native class map source/project binding differs')
 return record

def geometry(original,candidate,hashes,protected):
 tree=sx.read(candidate)
 if p.immutable(tree)!=p.immutable(original) or any(route not in p.routes(tree) for route in protected):
  raise p.Rejected('immutable or protected geometry changed')
 p.verify_candidate_files(candidate,hashes)
 return {'passed':True,'candidate_sha256':p.sha(candidate),'protected_records':len(protected)}

def native_binding(job,name,board,before,*,saved=False):
 return f.check_drc_stage(job.out,{'steps':job.steps},name,board,board if saved else job.out/(name+'-input')/board.name,saved,before)

def experiment(output,*,run_native=False):
 if run_native is not True:raise p.Rejected('explicit --run-native required; lead owns native lane')
 start=time.monotonic();cpu0=h.cpu_seconds();out=h.real_path(output,existing=False)
 if out.exists() or not out.is_relative_to(ROOT/'.runs'):raise p.Rejected('fresh checkout-owned output required')
 out.mkdir();owner={};h.capture_destination(owner,out)
 remaining=lambda:max(0,min(SECONDS-time.monotonic()+start,SECONDS-h.cpu_seconds()+cpu0))
 record={'schema':1,'kind':'netclass-parent-transport-v1','accepted':False,'whole_project_drc_clean':False,
  'status':'incomplete','controls_passed':False,'production_support_changed':False,'schematic_parity':'unavailable; owned diagnostic fixture has no schematic',
  'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_ceiling_bytes':LIMIT,'cases':[],
  'accounting_point':'SELF+waited-child CPU and wall through publisher; outer supervisor records complete lifetime costs plus startup allowance. Polling bounds may overshoot.'}
 tools=runtime=witness=None;jobs=[];sources={};checks=[]
 def owned():h.owned_destination(owner)
 def account():
  record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=h.cpu_seconds()-cpu0,steps=[s for job in jobs for s in job.steps],within_budget=remaining()>0 and size(out)<=LIMIT)
  if not record['within_budget'] or record['status'] in ('failed','invalidated','cancelled'):record['controls_passed']=False
 def bound():
  for job,name,board,before,saved,expected in checks:
   if native_binding(job,name,board,before,saved=saved)!=expected:raise p.Rejected('final native evidence changed')
  for row in record['cases']:
   if 'final_candidate' not in row:continue
   case=out/row['case'];board=Path(row['final_candidate']);source=case/'original'/board.name;project=f.read_json(source.with_suffix('.kicad_pro'))
   original=sx.read(source);protected=p.routes(original);hashes=sources[row['case']]
   if geometry(original,board,hashes,protected)!=row['geometry']:raise p.Rejected('final geometry binding changed')
   native=observed(case/'job/final-netclasses.json',board,p.tree_hash(board.parent));n.audit_native(native,project,parent_policy=True)
   if p.audit_route_dimensions(sx.read(board),protected,native)!=row['route_dimensions']:raise p.Rejected('final exact class target audit changed')
   exported=observed(case/'job/native-netclasses.json',source,hashes)
   if n.audit_dsn(case/'job/task.dsn',exported,project,parent_policy=True)!=row['dsn_audit']:raise p.Rejected('original native/DSN class evidence changed')
 def stable():
  owned()
  if tools is not None and p.tool_manifest()!=tools:raise p.Rejected('tool or committed implementation freeze changed')
  if runtime is not None and inventory(out/'code')!=runtime:raise p.Rejected('captured implementation changed')
  for case,hashes in sources.items():
   if p.tree_hash(out/case/'original')!=hashes:raise p.Rejected('immutable fixture source changed')
  if witness is not None:
   bound()
   if completed_evidence(out)!=witness:raise p.Rejected('finished evidence tree changed')
  if record['accepted'] is not False or record['production_support_changed'] is not False:raise p.Rejected('experimental scope changed')
 try:
  tools=p.tool_manifest();code={name:io.read_bytes(ROOT/name) for name in tools['implementation_sha256']}
  extra=['experiments/netclass_parent_transport_v1/driver.py','experiments/netclass_parent_transport_v1/fixture.py','experiments/netclass_parent_transport_v1/PROTOCOL.json','experiments/placement_handoff_native_v1/driver.py','experiments/original_project_native_v1/driver.py']
  for path in extra:code[path]=io.read_bytes(ROOT/path)
  for name,raw in code.items():
   committed=subprocess.run(['git','show',tools['git_head']+':'+name],cwd=ROOT,capture_output=True,check=True,timeout=min(3,remaining())).stdout
   if raw!=committed:raise p.Rejected('commit exact implementation before real native transport')
  copy_bytes(code,out/'code');runtime=inventory(out/'code');record.update(tools=tools,runtime_source_sha256=runtime,protocol_sha256=p.sha(HERE/'PROTOCOL.json'))
  for case,protected_variant in [('whole_unprotected',False),('partial_protected',True)]:
   stable();caseout=out/case;caseout.mkdir();files,recipe=fixture.prepare(protected=protected_variant)
   copy_bytes(files,caseout/'original');hashes=p.tree_hash(caseout/'original');sources[case]=hashes
   source=caseout/'original/fixture.kicad_pcb';original=sx.read(source);project=f.read_json(source.with_suffix('.kicad_pro'));protected=p.routes(original)
   row={'case':case,'status':'incomplete','control_passed':False,'recipe':recipe,'source_hashes':hashes};record['cases'].append(row)
   # Sequential jobs share the one whole wall/CPU clock; no fresh budget per stage.
   job=f.FloorJob(caseout/'job',SECONDS,remaining);jobs.append(job)
   src_native=job.drc('source-drc',source);checks.append((job,'source-drc',source,hashes,False,src_native))
   row['source_native']=src_native
   if src_native['blocking'] or src_native['exclusions'] or src_native['opens']!=3:raise p.Rejected('owned source expected exactly three unresolved pairs')
   job.native('export','export',source,job.out/'native.dsn',job.out/'native-netclasses.json')
   mapping=observed(job.out/'native-netclasses.json',source,hashes);native_classes=n.audit_native(mapping,project,parent_policy=True)
   # Engine helper expects task.dsn beside its process records. Exact bytes only.
   with (job.out/'task.dsn').open('xb') as stream:stream.write(io.read_bytes(job.out/'native.dsn'))
   row['dsn_audit']=n.audit_dsn(job.out/'task.dsn',mapping,project,parent_policy=True)
   if {x['class'] for x in native_classes['nets']}!={'Default','POWER,Default','SIGNAL,Default'}:raise p.Rejected('actual native composite identities differ from intended control')
   settings=p.engine_profile_settings('completion-only',remaining(),strict_class_targets=True);row['engine_settings']=settings
   job.step('engine',p.engine_argv(job.out,settings['argv']),already_sandboxed=True)
   f.process_check(job.out,{'steps':job.steps},'engine',p.engine_argv(job.out,settings['argv']))
   if not (job.out/'routes.ses').is_file() or not 0<(job.out/'routes.ses').stat().st_size<=sx.MAX_BYTES:raise p.Rejected('missing bounded real SES')
   job.native('import','import',source,job.out/'imported.kicad_pcb',job.out/'routes.ses')
   audit={};candidate_tree=p.transplant_routes(original,sx.read(job.out/'imported.kicad_pcb'),protected=protected,audit=audit,policy='exact_non_uuid_lock_position_v2')
   copy_bytes(files,caseout/'candidate');candidate=caseout/'candidate'/source.name;sx.write(candidate,candidate_tree)
   geometry(original,candidate,hashes,protected);p.audit_route_dimensions(candidate_tree,protected,mapping)
   # Shared original-shell native refill, preserving every non-route field.
   copy_bytes(io.inventory(candidate.parent,contents=True,max_bytes=LIMIT,max_files=2048,max_entries=4096),job.out/'refill');refill=job.out/'refill'/source.name;before=p.tree_hash(refill.parent)
   refill_native=job.drc('refill-drc',refill,save=True);checks.append((job,'refill-drc',refill,before,True,refill_native))
   sx.write(candidate,p.transplant_fill(sx.read(candidate),sx.read(refill)));finalhashes=p.tree_hash(candidate.parent)
   job.native('final-netclasses','netclasses',candidate,job.out/'final-netclasses.json')
   finalmap=observed(job.out/'final-netclasses.json',candidate,finalhashes);n.audit_native(finalmap,project,parent_policy=True)
   if [{k:v for k,v in x.items() if k!='netcode'} for x in finalmap['nets']]!=[{k:v for k,v in x.items() if k!='netcode'} for x in mapping['nets']]:raise p.Rejected('native class membership/targets changed after import/refill')
   dims=p.audit_route_dimensions(sx.read(candidate),protected,finalmap)
   final=job.drc('final-drc',candidate);checks.append((job,'final-drc',candidate,finalhashes,False,final))
   if not p.native_accepted(final) or _warning_signatures(final)!=_warning_signatures(src_native):
    raise p.Rejected('generated positive native failure/warning regression')
   if dims['checked']['vias']<1 or dims['checked']['segments']<3 or dims['checked']['protected']!=int(protected_variant):raise p.Rejected('positive failed to exercise generated widths/via/protection')
   row.update(final_candidate=str(candidate),candidate_sha256=p.sha(candidate),geometry=geometry(original,candidate,hashes,protected),route_dimensions=dims,native=final,protected_import=audit,schematic_parity='unavailable')
   # Legal minimum-width copper is still wrong when its exact source target differs.
   copy_bytes(io.inventory(candidate.parent,contents=True,max_bytes=LIMIT,max_files=2048,max_entries=4096),caseout/'wrong-width');wrong=caseout/'wrong-width'/source.name;tree=sx.read(wrong)
   names={x[1]:sx.unquote(x[2]) for x in sx.children(tree,'net')}
   target=next(x for x in p.routes(tree) if x[0]=='segment' and x not in protected and names.get(sx.one(x,'net')[1],sx.unquote(sx.one(x,'net')[1]))=='/PWR_PAIR')
   sx.one(target,'width')[1]='0.4';sx.write(wrong,tree)
   try:p.audit_route_dimensions(tree,protected,finalmap)
   except p.Rejected as exc:reason=str(exc)
   else:raise p.Rejected('wrong source class target not rejected')
   if reason!='generated track differs from native netclass target: /PWR_PAIR':raise p.Rejected('unexpected wrong-width refusal')
   wronghash=p.tree_hash(wrong.parent);wrongnative=job.drc('wrong-width-drc',wrong);checks.append((job,'wrong-width-drc',wrong,wronghash,False,wrongnative))
   row['wrong_width']={'class_audit_rejected':True,'reason':reason,'candidate_sha256':p.sha(wrong),'native':wrongnative,'native_minimums_accepted':p.native_accepted(wrongnative),'source_floor_preserved':project['board']['design_settings']['rules']['min_track_width']}
   if protected_variant:
    copy_bytes(io.inventory(candidate.parent,contents=True,max_bytes=LIMIT,max_files=2048,max_entries=4096),caseout/'removed-protected');missing=caseout/'removed-protected'/source.name;tree=sx.read(missing);tree.remove(protected[0]);sx.write(missing,tree)
    class NeverNative:
     calls=0
     def drc(self,*args,**kwargs):self.calls+=1;raise AssertionError('lost protection reached validator native')
    never=NeverNative()
    try:p.validate_candidate(never,original,missing,hashes,protected)
    except p.Rejected as exc:reason=str(exc)
    else:raise p.Rejected('lost protection not rejected')
    if reason!='protected route changed' or never.calls:raise p.Rejected('unexpected protection refusal')
    missinghash=p.tree_hash(missing.parent);missingnative=job.drc('removed-protected-drc',missing);checks.append((job,'removed-protected-drc',missing,missinghash,False,missingnative))
    if missingnative['opens']<1 or p.native_accepted(missingnative):raise p.Rejected('protected removal did not create native invalid control')
    row['removed_protected']={'pre_native_rejected':True,'reason':reason,'validator_native_calls':never.calls,'candidate_sha256':p.sha(missing),'native':missingnative}
   row.update(status='passed',control_passed=True)
  bound();witness=completed_evidence(out);stable();record.update(status='controls_passed',controls_passed=True);account()
 except (Exception,KeyboardInterrupt) as exc:
  record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
 f.publish(out,record,stable,account,remaining,owned=owned);owned()
 if remaining()<=0 or size(out)>LIMIT:
  record.update(status='budget_exceeded',controls_passed=False);f.publish(out,record,stable,account,remaining,owned=owned)
 return record

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--run-native',action='store_true');args=parser.parse_args()
 with cancellation():result=experiment(args.output,run_native=args.run_native)
 print(json.dumps({k:result[k] for k in ('status','controls_passed','accepted')}));raise SystemExit(0 if result['controls_passed'] else 2)
