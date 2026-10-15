"""Unexecuted missing-stage IR zone-net repair; never a normal routing receipt."""
import time, resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,json,math,shutil,signal,sys,copy,hashlib
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,board_floor as g,sexpr as sx
from autorouter import native_connected as nc,preferences as pref,placement_clearance as pc,handoff as h,local_settings as ls
from experiments.ir_native_connected_baseline_v1 import actor as previous
from autorouter import routing_scope as rs
from scripts import experiment_quality as q
from scripts.fetch_led_demo import capture_native_source
from autorouter import schematic_field_evidence as fields
SECONDS=60;BOOT=1;FINAL=10;MIN_CHILD=45
def need(ok,why):
 if not ok:raise p.Rejected(why)
def warn(n):return sorted(f.canonical(x) for x in n['findings'] if x['severity']=='warning')
def experiment(out,protocol,protocol_sha):
 spec=f.read_json(protocol);source,family=q.selected_source('ir-obstacle');original=p.preflight(source);hashes=p.tree_hash(source.parent)
 need(spec['status']=='frozen' and spec['actor_seconds']==SECONDS and spec['final_reserve_seconds']==FINAL and spec['cumulative_cap_seconds']==300,'freeze exact60/10/300 contract')
 need(str(source)==spec['source'] and hashes==spec['source_hashes'] and len(hashes)==5 and not any(n.endswith('.kicad_prl') for n in hashes),'exact five-file original IR packet required')
 need(out==ROOT/'.runs/ir-native-connected-repair-001' and not out.exists() and not out.is_symlink(),'fresh fixed actor output required')
 warm=ROOT/'.runs/ir-native-connected-baseline-001/route/candidate/IR_Sensor.kicad_pcb';warmtree=sx.read(warm)
 checks=f.read_json(ROOT/'.runs/ir-native-connected-negative-child-tail-002/checks.json');oldreceipt=f.read_json(warm.parent.parent/'result.json')
 need(checks['passed'] is True and checks['accepted'] is False and checks['candidate_sha256']==p.sha(warm)==spec['repair_source_sha256'] and oldreceipt['candidate_sha256']==checks['candidate_sha256'],'qualified retained negative child required')
 need(oldreceipt['accepted'] is False and oldreceipt['status']=='drc_rejected' and checks['native']=={k:oldreceipt['native'][k] for k in ('opens','blocking','warnings','exclusions','ignored_checks')} and checks['native']['opens']==1 and checks['native']['blocking']==checks['native']['exclusions']==0,'retained rejection differs')
 p.verify_candidate_files(warm,hashes,spec['repair_source_sha256']);need(p.immutable(warmtree)==p.immutable(original),'warm source changed original constraints')
 findings=checks['unconnected_items'];need(len(findings)==1 and len(findings[0]['items'])==2 and findings[0]['type']=='unconnected_items','one exact retained zone opening required')
 ids={row['uuid'] for row in findings[0]['items']};zones=[z for z in sx.children(warmtree,'zone') if rs._uuid(sx.one(z,'uuid'))[1] in ids]
 need(len(ids)==len(zones)==1,'retained opening must identify one exact original zone');_,resolve=g.source_net_identity(warmtree);names=[resolve(sx.one(zones[0],'net'),owner=zones[0])]
 need(names==spec['selected_names']==['/GND'],'exact reported original GND target required');protected=rs.protected_routes(warmtree,names);need(bool(protected),'retained own signal copper required')
 tools=spec['tools'];out.mkdir();owner={};h.capture_destination(owner,out)
 shutil.copytree(warm.parent,out/'source');owned=out/'source'/source.name;warm_hashes={**hashes,source.name:spec['repair_source_sha256']}
 for name in tools['implementation_sha256']:
  target=out/'code'/Path(name).name;target.parent.mkdir(exist_ok=True);shutil.copyfile(ROOT/name,target)
 shutil.copyfile(__file__,out/'actor.py');shutil.copyfile(protocol,out/'prospective.json')
 baseline=None
 record=dict(schema=1,kind='IR-native-connected-own-negative-zone-repair',status='incomplete',accepted=False,production_qualified=False,method_qualified=False,source=str(source),source_hashes=hashes,family=family,tools=tools,protocol_sha256=protocol_sha,budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,bootstrap_allowance_seconds=BOOT,final_reserve_seconds=FINAL,profile='completion-only',scoring_preference='via_high',scope='Own retained negative signals plus one fresh reported-zone selected-net completion-only/via_high repair. No classifier/initial engine repeat; full original decides diagnostic adoption.')
 completed=None;child=None;entry=None;job=None;settings=None;task=owned;task_hashes=warm_hashes
 def left():return min(SECONDS-BOOT-(time.monotonic()-START),SECONDS-BOOT-(cpu()-CPU0))
 def stable():
  need(p.tool_manifest()==tools,'current tools/source/checkpoint changed');q.verify_freeze(spec['freeze'],source)
  h.owned_destination(owner);need(left()>0,'actor60 wall/fullCPU exhausted')
  need(p.sha(protocol)==protocol_sha and p.sha(Path(__file__))==spec['actor_sha256'] and p.sha(out/'actor.py')==spec['actor_sha256'],'protocol/actor changed')
  for name,pin in spec['pins'].items():need(p.sha(ROOT/name)==pin,'frozen original/prior/helper evidence changed: '+name)
  need(p.tree_hash(source.parent)==hashes and p.tree_hash(owned.parent)==warm_hashes and p.sha(warm)==spec['repair_source_sha256'],'original/owned warm source changed')
  for name,pins in spec['retained_material'].items():need(p.tree_hash(ROOT/name)==pins,'retained prior prefix changed: '+name)
  need(p.tree_hash(out/'code')=={Path(n).name:v for n,v in tools['implementation_sha256'].items()},'captured implementation changed')
  if settings is not None:need(f.read_json(out/'preferences.json')==settings,'owned preset changed')
  if completed is not None:need(f.evidence_inventory(out)==completed,'completed/partial attempt changed')
 def replay():
  stable()
  if child is not None:
   need(f.read_json(out/'route/result.json')==child and p.sha(out/'route/result.json')==record['child_receipt_sha256'],'child receipt changed')
   if child['accepted'] is True:need(p.check_result(out/'route/result.json')['current'] is True,'accepted own child stale')
  if entry is not None:
   data=dict(steps=job.steps,tools=tools,source_hashes=hashes);candidate=Path(entry['candidate']);before={**hashes,source.name:p.sha(job.out/'pre-refill.kicad_pcb')}
   saved=f.check_drc_stage(job.out,data,'refill-drc',job.out/'refill'/source.name,job.out/'refill'/source.name,True,before)
   final=f.check_drc_stage(job.out,data,'final-drc',candidate,job.out/'final-drc-input'/source.name,False,{**hashes,source.name:entry['candidate_sha256']},schematic_parity=True)
   expected=p.transplant_fill(sx.read(job.out/'pre-refill.kicad_pcb'),sx.read(job.out/'refill'/source.name))
   need(saved==entry['saved_native'] and final==entry['native'] and p.sha(job.out/'final-drc.json')==entry['report_sha256'] and pc.read_bytes(candidate)==(sx.dump(expected)+'\n').encode(),'whole-original saved/final proof changed')
   need(p.immutable(sx.read(candidate))==p.immutable(original) and rs.audit(warmtree,sx.read(candidate),names)==record['final_protected_signal_audit'],'original geometry/protected signal copper changed');p.verify_candidate_files(candidate,hashes,entry['candidate_sha256']);ls.check_normal_policy(job.out,data)
   if p.netclass_policy(candidate) is not None:
    mapping=job.out/'final-netclasses.json';audit=p.audit_candidate_netclasses(candidate,protected,f.read_json(mapping));audit['native_map_file_sha256']=p.sha(mapping)
    f.process_check(job.out,data,'final-netclasses',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(mapping)])
    need(audit==f.read_json(job.out/'final-netclass-audit.json'),'class audit differs')
   if 'metrics' in record:
    f.process_check(job.out,data,'metrics',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(job.out/'metrics.json')])
    need(f.read_json(job.out/'metrics.json')==record['metrics'] and p.sha(job.out/'metrics.json')==record['metrics_sha256'],'actual final metrics changed')
   if record['method_qualified']:need(p.native_accepted(final) and warn(final)==warn(baseline) and final['ignored_checks']==baseline['ignored_checks'],'whole-original Native/warning/rule gate failed')
  stable()
 def account():
  record.update(wall_seconds=time.monotonic()-START+BOOT,total_cpu_seconds=cpu()-CPU0+BOOT,within_budget=left()>0,steps=[] if job is None else job.steps)
  if not record['within_budget'] or record['status']!='completed':record['method_qualified']=False
 try:
  stable();baseline=previous.original_baseline(f.read_json(ROOT/spec['original_baseline_protocol']));record['original_field_gate_composed']=True
  need(warn(oldreceipt['native'])==warn(baseline) and oldreceipt['native']['ignored_checks']==baseline['ignored_checks'],'retained negative changed original warnings/rules')
  seconds=math.floor(left()-FINAL);record['assigned_child_seconds']=seconds
  need(seconds>=MIN_CHILD,'insufficient selected repair45 plus10s whole-final reserve')
  settings={**pref.DEFAULTS,'scope':'selected_nets','nets':names,'seconds':seconds,'adapter':'both','profile':'completion-only','guidance':'native','layers':'source_all','scoring_preference':'via_high'};pref.validate(settings);p.save_json(out/'preferences.json',settings)
  record.update(repair_source=str(warm),repair_source_sha256=spec['repair_source_sha256'],target_finding=findings[0],selected_names=names,protected_signal_audit=rs.audit(warmtree,warmtree,names))
  child=p.route(task,out/'route',settings_path=out/'preferences.json');record.update(child_receipt_sha256=p.sha(out/'route/result.json'),child_accepted=child['accepted'],child_status=child['status'],child_native=child.get('native'),child_candidate_sha256=child.get('candidate_sha256'),child_native_report_sha256=child.get('native_report_sha256'),child_metrics=child.get('metrics'))
  need(child['source']==str(task) and child['source_hashes']==task_hashes and pref.readback(pc.read_bytes(out/'route/routing-preferences.json'))==pref.validate(settings),'child source/preset differs')
  need(child['accepted'] is True and p.check_result(out/'route/result.json')['current'] is True,'own selected child rejected; all evidence retained')
  job=f.FloorJob(out/'whole-original',left(),left,protect_local_settings=True);shutil.copytree(out/'code',job.out/'code');shutil.copytree(source.parent,job.out/'snapshot');shutil.copytree(source.parent,job.out/'candidate')
  candidate=job.out/'candidate'/source.name;tree=p.transplant_routes(g.task_from_source(original),sx.read(Path(child['candidate'])),protected=[],policy='exact_non_uuid_lock_position_v2');sx.write(candidate,tree)
  digest,native=p.validate_candidate(job,original,candidate,hashes,protected,schematic_parity=True)
  record['final_protected_signal_audit']=rs.audit(warmtree,sx.read(candidate),names)
  saved=f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',job.out/'refill'/source.name,job.out/'refill'/source.name,True,{**hashes,source.name:p.sha(job.out/'pre-refill.kicad_pcb')})
  entry=dict(candidate=str(candidate),candidate_sha256=digest,native=native,saved_native=saved,report_sha256=p.sha(job.out/'final-drc.json'));record['final_candidate']=entry
  need(p.native_accepted(native) and warn(native)==warn(baseline) and native['ignored_checks']==baseline['ignored_checks'],'whole-original candidate rejected, including any skipped-net opens')
  job.native('metrics','metrics',candidate,job.out/'metrics.json');metrics=f.read_json(job.out/'metrics.json')
  need(metrics['version']=='10.0.0' and type(metrics['vias']) is int and metrics['vias']>=0 and type(metrics['track_length_mm']) in (int,float) and math.isfinite(metrics['track_length_mm']) and metrics['track_length_mm']>=0,'invalid actual metrics')
  record.update(metrics=metrics,metrics_sha256=p.sha(job.out/'metrics.json'),status='completed',method_qualified=True);replay()
 except (Exception,KeyboardInterrupt) as exc:
  record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',method_qualified=False,reason=type(exc).__name__+': '+str(exc),initial_failure=type(exc).__name__+': '+str(exc))
 completed=f.evidence_inventory(out);record.update(completed_evidence=completed)
 return f.publish(out,record,stable,account,left,owned=lambda:h.owned_destination(owner),final_check=replay)
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
 if not a.run_native:ap.error('explicit --run-native required')
 def stop(*_):raise KeyboardInterrupt
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
 with p.validation_readback_session():r=experiment(a.output,a.protocol,a.protocol_sha256)
 print(f.canonical({k:r.get(k) for k in ('status','method_qualified','wall_seconds','total_cpu_seconds','initial_failure','reason')}));raise SystemExit(0 if r['method_qualified'] else 2)
