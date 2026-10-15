"""Unexecuted fresh IR connectivity baseline; never a normal routing receipt."""
import time, resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,json,math,shutil,signal,sys,copy,hashlib
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,board_floor as g,sexpr as sx
from autorouter import native_connected as nc,preferences as pref,placement_clearance as pc,handoff as h,local_settings as ls
from experiments.native_connected_v1 import driver as classifier
from scripts import experiment_quality as q
from scripts.fetch_led_demo import capture_native_source
from autorouter import schematic_field_evidence as fields
SECONDS=95;BOOT=1;FINAL=20;MIN_CHILD=45
def need(ok,why):
 if not ok:raise p.Rejected(why)
def warn(n):return sorted(f.canonical(x) for x in n['findings'] if x['severity']=='warning')
def original_baseline(spec):
 # Compose the already qualified missing-field proof without parsing/mutating
 # the correctly retained failed original001 sidecar or rerunning Native.
 gate=f.read_json(ROOT/'.runs/ir-obstacle-original-field-gate-003/result.json')
 prior_path=ROOT/'.runs/ir-obstacle-original-native-001/result.json';prior=f.read_json(prior_path)
 raw=ROOT/spec['original_report'];_,files=capture_native_source('ir-obstacle',root=ROOT)
 need(all(gate.get(k) is True for k in ('passed','source_current','original_unchanged')),'qualified retained field gate required')
 need(gate['native_report_sha256']==p.sha(raw)==spec['pins'][spec['original_report']] and gate['prior_original_receipt_sha256']==p.sha(prior_path),'field gate original/report binding differs')
 need(gate['source_hashes']==prior['original_hashes']=={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},'field gate complete source packet differs')
 for name in ('autorouter/schematic_field_evidence.py','autorouter/schematic_fields.py'):
  need(gate['tools']['implementation_sha256'][name]==p.sha(ROOT/name)==spec['pins'][name],'qualified field helper lineage changed')
 proof=fields.derive(raw.parent,'original-final',f.read_json(raw))
 baseline=copy.deepcopy(prior['parity_native']);baseline['field_parity']=proof
 need(proof==gate['field_proof'] and baseline==gate['qualified_native'],'retained field composition differs')
 need(p.native_accepted(baseline) and (baseline['warnings'],len(baseline['ignored_checks']))==(42,7),'qualified original42-warning/seven-ignored baseline required')
 return baseline
def experiment(out,protocol,protocol_sha):
 spec=f.read_json(protocol);source,family=q.selected_source('ir-obstacle');original=p.preflight(source);hashes=p.tree_hash(source.parent)
 need(spec['status']=='frozen' and spec['actor_seconds']==SECONDS and spec['final_reserve_seconds']==FINAL and spec['cumulative_cap_seconds']==300,'freeze exact95/20/300 contract')
 need(str(source)==spec['source'] and hashes==spec['source_hashes'] and len(hashes)==5 and not any(n.endswith('.kicad_prl') for n in hashes),'exact five-file original IR packet required')
 need(out==ROOT/'.runs/ir-native-connected-baseline-001' and not out.exists() and not out.is_symlink(),'fresh fixed actor output required')
 probe=ROOT/'.runs/ir-native-connected-classifier-001';need(not probe.exists() and not probe.is_symlink(),'fresh independent direct .runs classifier required')
 tools=spec['tools'];out.mkdir();owner={};h.capture_destination(owner,out)
 shutil.copytree(source.parent,out/'source');owned=out/'source'/source.name
 for name in tools['implementation_sha256']:
  target=out/'code'/Path(name).name;target.parent.mkdir(exist_ok=True);shutil.copyfile(ROOT/name,target)
 shutil.copyfile(__file__,out/'actor.py');shutil.copyfile(protocol,out/'prospective.json')
 baseline=None
 record=dict(schema=1,kind='IR-fresh-native-connected-completion-baseline',status='incomplete',accepted=False,production_qualified=False,method_qualified=False,source=str(source),source_hashes=hashes,family=family,tools=tools,protocol_sha256=protocol_sha,budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,bootstrap_allowance_seconds=BOOT,final_reserve_seconds=FINAL,profile='completion-only',scoring_preference='via_high',scope='Fresh native activity hint plus selected completion-only/via_high; full original decides adoption. No full tuned optimizer or untouched/generalization claim.')
 completed=probe_material=None;child=None;entry=None;job=None;classification=None;settings=None;task=None;task_hashes=None
 def left():return min(SECONDS-BOOT-(time.monotonic()-START),SECONDS-BOOT-(cpu()-CPU0))
 def stable():
  need(p.tool_manifest()==tools,'current tools/source/checkpoint changed');q.verify_freeze(spec['freeze'],source)
  h.owned_destination(owner);need(left()>0,'actor95 wall/fullCPU exhausted')
  need(p.sha(protocol)==protocol_sha and p.sha(Path(__file__))==spec['actor_sha256'] and p.sha(out/'actor.py')==spec['actor_sha256'],'protocol/actor changed')
  for name,pin in spec['pins'].items():need(p.sha(ROOT/name)==pin,'frozen original/prior/helper evidence changed: '+name)
  need(p.tree_hash(source.parent)==hashes and p.tree_hash(owned.parent)==hashes,'original/owned source changed')
  need(p.tree_hash(out/'code')=={Path(n).name:v for n,v in tools['implementation_sha256'].items()},'captured implementation changed')
  if settings is not None:need(f.read_json(out/'preferences.json')==settings,'owned preset changed')
  if probe_material is not None:need(p.tree_hash(probe)==probe_material,'completed/partial classifier including receipt changed')
  if completed is not None:need(f.evidence_inventory(out)==completed,'completed/partial attempt changed')
 def replay():
  stable()
  if classification is not None:
   d=f.read_json(probe/'result.json');actual=nc.readback(probe,d,owned,task,probe/'refill'/source.name,probe/'candidate'/source.name,probe/'native.dsn')
   need(d['status']=='completed' and d['eligibility_qualified'] is True and d['tools']==tools and actual==classification and p.sha(probe/'result.json')==record['classifier_receipt_sha256'],'fresh classifier changed')
   need(pc.read_bytes(task)==(sx.dump(g.task_from_source(original))+'\n').encode() and not p.routes(sx.read(task)) and p.tree_hash(task.parent)==task_hashes,'classifier task is not exact wholly stripped original')
  if child is not None:
   need(f.read_json(out/'route/result.json')==child and p.sha(out/'route/result.json')==record['child_receipt_sha256'],'child receipt changed')
   if child['accepted'] is True:need(p.check_result(out/'route/result.json')['current'] is True,'accepted own child stale')
  if entry is not None:
   data=dict(steps=job.steps,tools=tools,source_hashes=hashes);candidate=Path(entry['candidate']);before={**hashes,source.name:p.sha(job.out/'pre-refill.kicad_pcb')}
   saved=f.check_drc_stage(job.out,data,'refill-drc',job.out/'refill'/source.name,job.out/'refill'/source.name,True,before)
   final=f.check_drc_stage(job.out,data,'final-drc',candidate,job.out/'final-drc-input'/source.name,False,{**hashes,source.name:entry['candidate_sha256']},schematic_parity=True)
   expected=p.transplant_fill(sx.read(job.out/'pre-refill.kicad_pcb'),sx.read(job.out/'refill'/source.name))
   need(saved==entry['saved_native'] and final==entry['native'] and p.sha(job.out/'final-drc.json')==entry['report_sha256'] and pc.read_bytes(candidate)==(sx.dump(expected)+'\n').encode(),'whole-original saved/final proof changed')
   need(p.immutable(sx.read(candidate))==p.immutable(original),'original geometry changed');p.verify_candidate_files(candidate,hashes,entry['candidate_sha256']);ls.check_normal_policy(job.out,data)
   if p.netclass_policy(candidate) is not None:
    mapping=job.out/'final-netclasses.json';audit=p.audit_candidate_netclasses(candidate,[],f.read_json(mapping));audit['native_map_file_sha256']=p.sha(mapping)
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
  stable();baseline=original_baseline(spec);record['original_field_gate_composed']=True
  classifier.experiment(probe,project=owned)
  probe_material=p.tree_hash(probe);d=f.read_json(probe/'result.json')
  need(d['status']=='completed' and d['eligibility_qualified'] is True and d['tools']==tools,'own classifier failed; no engine')
  task=probe/'task'/source.name;task_hashes=p.tree_hash(task.parent)
  classification=nc.readback(probe,d,owned,task,probe/'refill'/source.name,probe/'candidate'/source.name,probe/'native.dsn')
  record.update(classifier=str(probe),classifier_receipt_sha256=p.sha(probe/'result.json'),classification=classification,task_hashes=task_hashes)
  need(pc.read_bytes(task)==(sx.dump(g.task_from_source(original))+'\n').encode() and not p.routes(sx.read(task)),'fresh classifier task leaked source routing/fill')
  seconds=math.floor(left()-FINAL);record['assigned_child_seconds']=seconds
  need(seconds>=MIN_CHILD,'insufficient classifier-paid child engine reserves plus20s whole-final reserve')
  settings={**pref.DEFAULTS,'scope':'selected_nets','nets':classification['active_names'],'seconds':seconds,'adapter':'both','profile':'completion-only','guidance':'native','layers':'source_all','scoring_preference':'via_high'};pref.validate(settings);p.save_json(out/'preferences.json',settings)
  child=p.route(task,out/'route',settings_path=out/'preferences.json');record.update(child_receipt_sha256=p.sha(out/'route/result.json'),child_accepted=child['accepted'],child_status=child['status'])
  need(child['source']==str(task) and child['source_hashes']==task_hashes and pref.readback(pc.read_bytes(out/'route/routing-preferences.json'))==pref.validate(settings),'child source/preset differs')
  need(child['accepted'] is True and p.check_result(out/'route/result.json')['current'] is True,'own selected child rejected; all evidence retained')
  job=f.FloorJob(out/'whole-original',left(),left,protect_local_settings=True);shutil.copytree(out/'code',job.out/'code');shutil.copytree(source.parent,job.out/'snapshot');shutil.copytree(source.parent,job.out/'candidate')
  candidate=job.out/'candidate'/source.name;tree=p.transplant_routes(g.task_from_source(original),sx.read(Path(child['candidate'])),protected=[],policy='exact_non_uuid_lock_position_v2');sx.write(candidate,tree)
  digest,native=p.validate_candidate(job,original,candidate,hashes,[],schematic_parity=True)
  saved=f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',job.out/'refill'/source.name,job.out/'refill'/source.name,True,{**hashes,source.name:p.sha(job.out/'pre-refill.kicad_pcb')})
  entry=dict(candidate=str(candidate),candidate_sha256=digest,native=native,saved_native=saved,report_sha256=p.sha(job.out/'final-drc.json'));record['final_candidate']=entry
  need(p.native_accepted(native) and warn(native)==warn(baseline) and native['ignored_checks']==baseline['ignored_checks'],'whole-original candidate rejected, including any skipped-net opens')
  job.native('metrics','metrics',candidate,job.out/'metrics.json');metrics=f.read_json(job.out/'metrics.json')
  need(metrics['version']=='10.0.0' and type(metrics['vias']) is int and metrics['vias']>=0 and type(metrics['track_length_mm']) in (int,float) and math.isfinite(metrics['track_length_mm']) and metrics['track_length_mm']>=0,'invalid actual metrics')
  record.update(metrics=metrics,metrics_sha256=p.sha(job.out/'metrics.json'),status='completed',method_qualified=True);replay()
 except (Exception,KeyboardInterrupt) as exc:
  record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',method_qualified=False,reason=type(exc).__name__+': '+str(exc),initial_failure=type(exc).__name__+': '+str(exc))
 if probe.exists():probe_material=p.tree_hash(probe)
 completed=f.evidence_inventory(out);record.update(completed_evidence=completed,classifier_material=probe_material)
 return f.publish(out,record,stable,account,left,owned=lambda:h.owned_destination(owner),final_check=replay)
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
 if not a.run_native:ap.error('explicit --run-native required')
 def stop(*_):raise KeyboardInterrupt
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
 with p.validation_readback_session():r=experiment(a.output,a.protocol,a.protocol_sha256)
 print(f.canonical({k:r.get(k) for k in ('status','method_qualified','wall_seconds','total_cpu_seconds','initial_failure','reason')}));raise SystemExit(0 if r['method_qualified'] else 2)
