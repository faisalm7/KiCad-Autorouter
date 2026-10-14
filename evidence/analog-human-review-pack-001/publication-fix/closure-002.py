"""Pure retained-workflow closure: no subprocess, native, export, plot or solver."""
from pathlib import Path
import time,resource,sys,json
START=time.monotonic()
def cpu():
 a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN);return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu();ROOT=Path(__file__).absolute().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import floor_route as f,pipeline as p,handoff as h,placement_clearance as io,review_export as ex
from experiments.licensed_acquisition_v1 import fetch as shared
HERE=Path(__file__).absolute().parent;PIN='3c9054cf71c2fce48aeac27038e575789319377763bbfb7d37976e291b4ed5ee';BASE=ROOT/'.runs/analog-human-review-pack-001'
BOOTSTRAP='import sys;sys.path.insert(0,sys.argv.pop(1));from autorouter.__main__ import main;raise SystemExit(main())'
def main():
 protocol=f.read_json(HERE/'CLOSURE-PROTOCOL.json')
 if p.sha(HERE/'CLOSURE-PROTOCOL.json')!=PIN:raise ValueError('closure protocol changed')
 out=h.real_path(ROOT/'.runs/analog-human-review-pack-closure-002',existing=False);out.mkdir();owner={};h.capture_destination(owner,out)
 record={'schema':1,'accepted':False,'pack_ready':False,'status':'incomplete','human_review_observed':False,'human_pcb_approval_observed':False,'physical_electrical_validation':False,'new_native_execution':False,'new_export_execution':False,'new_plot_execution':False,'source_pack':str(BASE),'protocol_sha256':PIN,'preserved_failure':protocol['error_preserved']}
 failed_path=ROOT/'.runs/analog-human-review-pack-closure-001/result.json';failed=f.read_json(failed_path);failed_pin=p.sha(failed_path)
 if failed.get('first_failure')!='ValueError: eight fourCu before/after plots missing' or failed['pack_ready'] is not False:raise ValueError('retained prior closure differs')
 record['retained_failed_closure_sha256']=failed_pin;record['closure_schema_correction']='Eight raw native SVGs and eight sanitized displays represent eight stages; initial verifier incorrectly required total eight SVGfiles.'
 before=io.inventory(BASE,max_bytes=1024**3,max_files=24000,max_entries=48000,with_directories=True)
 def remaining():return min(60-(time.monotonic()-START),60-(cpu()-CPU0))
 def stable():
  h.owned_destination(owner)
  if remaining()<=0:raise ValueError('closure budget exhausted')
  if p.sha(failed_path)!=failed_pin:raise ValueError('failed closure changed')
  if p.sha(HERE/'CLOSURE-PROTOCOL.json')!=PIN or any(p.sha(ROOT/n)!=v for n,v in protocol['pins'].items()):raise ValueError('frozen closure inputs changed')
  if io.inventory(BASE,max_bytes=1024**3,max_files=24000,max_entries=48000,with_directories=True)!=before:raise ValueError('original failed pack/evidence changed')
 def account():
  wall=time.monotonic()-START;used=cpu()-CPU0;record.update(closure_wall_seconds=wall,closure_full_cpu_seconds=used,total_charged_wall_seconds=protocol['original_observed_wall_seconds']+3+failed['closure_wall_seconds']+wall,total_charged_full_cpu_seconds=protocol['original_observed_full_cpu_seconds']+3+failed['closure_full_cpu_seconds']+used,original_budget_seconds=900,closure_budget_seconds=60,within_budget=wall<=60 and used<=60)
  if record.get('status')!='readback_closed' or not record['within_budget'] or max(record['total_charged_wall_seconds'],record['total_charged_full_cpu_seconds'])>900:record['pack_ready']=False
 try:
  stable();mapping=f.read_json(BASE/'custodian/mapping.json');source=f.read_json(BASE/'custodian/protocol.json');old=f.read_json(BASE/'result.json')
  if old.get('status')!='invalidated' or old.get('pack_ready') is not False or len(old.get('steps',[]))!=12 or len(mapping['cases'])!=3 or mapping['human_review'] is not None:raise ValueError('recorded failed state differs')
  proofs={};allsteps=[]
  for id in mapping['order']:
   row=mapping['cases'][id];folder=BASE/'custodian'/id;case=BASE/'reviewer-pack/cases'/id;inputrow=row['input']
   if inputrow!=next(r for r in source['cases'] if r['arm']==row['arm']):raise ValueError('case source mapping differs')
   check=ex.check_export(folder/'export/export.json');export=f.read_json(folder/'export/export.json')
   if check.get('current') is not True or check.get('export_accepted') is not True or export['native']!=inputrow['expected_native'] or export['metrics']['copper_layers']!=4 or export['source_hashes']!=inputrow['source_hashes']:raise ValueError('fresh native proof differs')
   actual=io.inventory(case/'project');expected=io.inventory(Path(export['candidate']).parent)
   if actual!=expected or actual!=row['delivered_project_hashes'] or actual['analog_filter_module.kicad_pcb']!=export['candidate_sha256']:raise ValueError('delivered project differs from native-validated bytes')
   form=f.read_json(BASE/'reviewer-pack/forms'/(id+'.json'))
   if form.get('case_id')!=id or any(v is not None for k,v in form.items() if k!='case_id'):raise ValueError('human form not blank')
   args={'copy':['review-copy',row['routing_receipt'],'--output',str(folder/'review'),*(['--render'] if row['arm']=='C_feedback' else [])],'intent':['review-choice',str(folder/'review/review.json'),'--choice','accept','--output',str(folder/'intent')],'export':['review-export',str(folder/'intent/choice.json'),'--output',str(folder/'export'),'--seconds','120'],'check':['review-export-check',str(folder/'export/export.json')]}
   for stage,tail in args.items():
    step=f.read_json(BASE/'custodian'/(id+'-'+stage+'-process.json'));expectedargv=[str(ROOT/'.venv/bin/python'),'-B','-c',BOOTSTRAP,str(ROOT),*tail]
    if step['argv']!=expectedargv or step['cwd']!=str(BASE/'custodian') or step['status']!='success' or step['exit_code']!=0 or step.get('cleanup_complete') is not True:raise ValueError('completed process grammar/state differs')
    if step!=next({k:v for k,v in x.items() if k!='name'} for x in old['steps'] if x['name']==id+'-'+stage):raise ValueError('outer process journal differs')
    allsteps.append(id+'-'+stage)
   view=f.read_json(case/'native-findings.json');native=f.read_json(folder/'export/validation/final-drc.json')
   for key in ('$schema','kicad_version','coordinate_units','included_severities','ignored_checks','violations','unconnected_items','schematic_parity'):
    if key in native and view.get(key)!=native[key]:raise ValueError('display omits or changes native findings')
   if view['native_summary']!=export['native']:raise ValueError('display summary differs')
   review=f.read_json(folder/'review/review.json');plots=review.get('preview')
   if row['arm']=='C_feedback':
    if plots['layers']!=['F.Cu','In1.Cu','In2.Cu','B.Cu'] or len(plots['steps'])!=8 or {n for n in plots['files'] if n.endswith('.svg')}!={f'plot-work/{kind}/{phase}-{layer}.svg' for kind in ('native-plots','plots') for phase in ('before','after') for layer in plots['layers']}:raise ValueError('eight fourCu before/after plots missing')
    # ex.check_export -> bind already validates every preview file hash and original reference tree.
    if any(s.get('status')!='success' or s.get('exit_code')!=0 or s.get('cleanup_complete') is not True for s in plots['steps']):raise ValueError('plot process failed')
   elif plots is not None:raise ValueError('unexpected blind-case plotting')
   proofs[id]={'delivered_hashes':actual,'export_receipt_sha256':p.sha(folder/'export/export.json'),'native_report_sha256':export['native_report_sha256'],'native_summary':{k:export['native'][k] for k in ('opens','blocking','warnings','exclusions')},'opaque_id':id}
   stable()
  if len(allsteps)!=12:raise ValueError('twelve workflow commands not uniquely closed')
  record.update(status='readback_closed',pack_ready=True,authoritative_local_index=True,delivered_cases=proofs,process_journal_count=12,custodian_plot_count=8,original_failed_pack_witness={'files':before[0],'directories':list(before[1])},human_forms_blank=True,all_six_leads_retained=source['all_source_leads_retained'],selection_exposure=mapping['selection_exposure'],all_C_exploration_compute=mapping['all_C_exploration_compute'],distribution_authorized=False)
 except (Exception,KeyboardInterrupt) as exc:record.update(status='rejected',pack_ready=False,first_failure=type(exc).__name__+': '+str(exc))
 f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner))
 try:
  stable();current=f.read_json(out/'result.json');account();stable()
  if current.get('pack_ready') is True and (record.get('pack_ready') is not True or remaining()<=0):raise ValueError('final closure cap invalidated index')
 except (Exception,KeyboardInterrupt) as exc:
  record.update(status='rejected',pack_ready=False,final_failure=type(exc).__name__+': '+str(exc));f.publish(out,record,lambda:(_ for _ in ()).throw(ValueError(record['final_failure'])),account,remaining,owned=lambda:h.owned_destination(owner))
 return record
if __name__=='__main__':
 with shared.cancellation(),shared.alarm(60):result=main()
 print(json.dumps({k:result.get(k) for k in ('status','accepted','pack_ready','closure_wall_seconds','closure_full_cpu_seconds','total_charged_wall_seconds','total_charged_full_cpu_seconds')},indent=2));raise SystemExit(0 if result.get('pack_ready') is True and result.get('status')=='readback_closed' else 2)
