"""UNEXECUTED missing-stage continuation; retained classifier/child, cumulative120."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import argparse,hashlib,json,math,signal,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,handoff as h,sexpr as sx,board_floor as g,native_connected as nc,preferences as pref
from experiments.native_connected_pair_v1 import driver as pair
from experiments.placement_handoff_native_v1.driver import copy_bytes
OLD=ROOT/'.runs/nus-native-connected-contact120-001'
PROBE=ROOT/'.runs/nus-native-connected-contact120-001-classifier'
OLD_OUTER=ROOT/'.runs/nus-native-connected-contact120-001-execution'
OLD_LEAD=ROOT/'.runs/nus-native-connected-contact120-001-lead-execution'
READER=ROOT/'.runs/contact001-corrected-child-readback-001'
OLD_PROTOCOL=ROOT/'experiments/native_connected_pair_v1/protocol-contact-v2.json'
OLD_HEAD='7aeaac72f3f79e70cb0226275daadb326419ebdb'
SECONDS=120;BOOT=1;LIMIT=64*1024**2

def need(ok,message):
    if not ok:raise p.Rejected(message)
def inventory(path):
    files,dirs=pc.inventory(path,max_bytes=128*1024**2,max_files=6000,max_entries=12000,with_directories=True)
    return dict(files=files,directories=list(dirs))
def check_outer_witness(out,data,spec,protocol_sha):
    """Existing pair's byte-continuity seam adapted for retained sibling paths."""
    identity={'schema':1,'kind':'NUS-contact-missing-stage-continuation','method':'native-connected-contact','status':'completed','method_qualified':True,'accepted':False,'production_admitted':False,'budget_seconds':120,'cpu_budget_seconds':120,'bootstrap_allowance_seconds':1,'protocol_sha256':protocol_sha}
    need(all(type(data.get(k)) is type(v) and data[k]==v for k,v in identity.items()),'continuation identity/caps differ')
    need(f.canonical(data['prior_costs'])==f.canonical(spec['prior_costs']),'continuation prior charge differs')
    for label,charged,prior in (('new_wall_seconds','charged_wall_seconds','wall_seconds'),('new_full_cpu_seconds','charged_full_cpu_seconds','full_cpu_seconds')):
        need(type(data[label]) in (int,float) and math.isfinite(data[label]) and data[label]>=0 and data[charged]==spec['prior_costs'][prior]+BOOT+data[label],'continuation exact charged accounting differs')
    need(data['within_budget'] is True and max(data['charged_wall_seconds'],data['charged_full_cpu_seconds'])<120,'continuation cumulative cap differs')
    need(f.evidence_inventory(out)==data['completed_material'],'completed continuation material changed')
    need(data['source']==spec['source'] and data['source_hashes']==spec['source_hashes'] and p.tool_manifest()==data['tools'] and p.tree_hash(Path(data['source']).parent)==data['source_hashes'],'current producer/source changed')
    for name,pin in spec['code_sha256'].items():need(p.sha(ROOT/name)==pin,'current code changed: '+name)
    for name,pin in spec['prefixes'].items():need(inventory(ROOT/name)==pin,'retained prefix changed: '+name)
    for name,pin in spec['retained_files'].items():need(p.sha(ROOT/name)==pin,'retained producer changed: '+name)

def experiment(out,protocol,protocol_sha):
    need(Path(__file__).parent==ROOT/'experiments/native_contact_continuation_v1','promote/review/checkpoint before Native')
    need(out.parent==ROOT/'.runs' and not out.exists() and not out.is_symlink(),'fresh direct continuation output required')
    need(p.sha(protocol)==protocol_sha,'prospective continuation protocol differs');spec=f.read_json(protocol)
    need(spec['status']=='prospectively_frozen' and spec['actor_sha256']==p.sha(__file__) and spec['cumulative_wall_full_cpu_seconds']==120 and spec['bootstrap_allowance_seconds']==BOOT and spec['experimental_contact'] is True,'unfrozen continuation interface')
    need(all(not Path(n).is_absolute() and '..' not in Path(n).parts for group in ('code_sha256','prefixes','retained_files') for n in spec[group]),'project-relative nonescaping pins required')
    prior=spec['prior_costs'];charged=[prior['wall_seconds'],prior['full_cpu_seconds']]
    need(all(type(v) in (int,float) and math.isfinite(v) and 0<=v<119 for v in charged),'finite cumulative prior required')
    remaining=lambda:min(120-charged[0]-BOOT-(time.monotonic()-START),120-charged[1]-BOOT-(cpu()-CPU0))
    old=f.read_json(OLD/'result.json');child=OLD/'selected-route';child_data=f.read_json(child/'result.json');probe_data=f.read_json(PROBE/'result.json')
    outer=f.read_json(OLD_OUTER/'result.json');lead=f.read_json(OLD_LEAD/'execution.json');reader=f.read_json(READER/'result.json');old_spec=f.read_json(OLD_PROTOCOL)
    source=Path(old['source']);hashes=old['source_hashes'];old_tools=old['tools'];tools=p.tool_manifest()
    need(old_tools['git_head']==OLD_HEAD and {k:v for k,v in old_tools.items() if k!='git_head'}=={k:v for k,v in tools.items() if k!='git_head'},'retained core/tool identity differs; only explicit historical HEAD may differ')
    need(spec['source']==str(source) and spec['source_hashes']==hashes and len(hashes)==8 and p.tree_hash(source.parent)==hashes,'exact pristine eight-file source differs')
    required={str(x.relative_to(ROOT)) for x in (OLD,PROBE,OLD_OUTER,OLD_LEAD,READER,source.parent)}
    need(required<=set(spec['prefixes']),'whole retained actor/classifier/outer/lead/reader/source prefixes required')
    need(set(old_spec['code_sha256'])|set(tools['implementation_sha256'])|{'experiments/native_contact_continuation_v1/actor.py','experiments/native_contact_continuation_v1/run.py'}<=set(spec['code_sha256']),'complete current helper/code closure required')
    for name,pin in old_spec['code_sha256'].items():
        if name not in ('experiments/native_connected_pair_v1/driver.py','tests/test_native_connected_pair.py'):need(spec['code_sha256'][name]==pin,'unexpected old helper drift: '+name)
    need(p.sha(OLD_PROTOCOL)==old['protocol_sha256']==outer['protocol_sha256']==lead['protocol_sha256'],'actual001 protocol lineage differs')
    need(old['status']=='invalidated' and old['accepted'] is False and old['method_qualified'] is False and old['steps']==[] and old['initial_failure']=='Rejected: contact child source/import/refill/report/warnings differ' and not (OLD/'whole-validation').exists(),'preserved actual001 missing-stage failure differs')
    for row in (outer,lead):
        proc=row['process'];need(proc['status']=='nonzero_exit' and type(proc['exit_code']) is int and proc['exit_code']==2 and proc['cleanup_complete'] is True,'retained outer cleanup/status differs')
    need(lead['source_current'] is True and reader['passed'] is True and reader['actor_sha256']==p.sha(OLD/'result.json') and reader['child_sha256']==p.sha(child/'result.json') and reader['corrected_reader_sha256']==spec['code_sha256']['experiments/native_connected_pair_v1/driver.py'],'actual corrected-reader binding differs')
    base=[max(old['charged_wall_seconds'],outer['wall_seconds'],lead['charged_wall_seconds']),max(old['charged_full_cpu_seconds'],outer['total_cpu_seconds'],lead['charged_full_cpu_seconds'])]
    minimum=[base[0]+reader['wall_seconds']+2,base[1]+reader['full_cpu_seconds']+2]
    need(all(v>=bound for v,bound in zip(charged,minimum)),'continuation omits actual001 max charge or corrected reader+2')
    original=p.preflight(source);source_files=pc.inventory(source.parent,contents=True)
    out.mkdir();owner={};h.capture_destination(owner,out);copy_bytes(source_files,out/'original',expected_parent_owner=owner)
    copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},out/'code',expected_parent_owner=owner)
    copy_bytes({n:pc.read_bytes(ROOT/n) for n in spec['code_sha256'] if n not in tools['implementation_sha256']},out/'helper-code',expected_parent_owner=owner)
    p.save_json(out/'prospective-pins.json',spec);state={'spec':spec,'_remaining':remaining};completed=None
    record=dict(schema=1,kind='NUS-contact-missing-stage-continuation',status='incomplete',method='native-connected-contact',accepted=False,production_admitted=False,method_qualified=False,
        budget_seconds=120,cpu_budget_seconds=120,bootstrap_allowance_seconds=BOOT,final_reserve_seconds=20,protocol_sha256=protocol_sha,prior_costs=prior,
        source=str(source),source_hashes=hashes,tools=tools,retained_stage_tools=old_tools,retained_stage_head=OLD_HEAD,
        classifier=str(PROBE),classifier_sha256=p.sha(PROBE/'result.json'),classification=old['classification'],task_hashes=old['task_hashes'],selected_names=old['selected_names'],
        child_receipt_sha256=p.sha(child/'result.json'),child_status=child_data['status'],child_accepted=False,prior_pilot_costs=old['prior_pilot_costs'],steps=[],
        prior_cost_binding=dict(actor_sha256=p.sha(OLD/'result.json'),outer_sha256=p.sha(OLD_OUTER/'result.json'),lead_sha256=p.sha(OLD_LEAD/'execution.json'),reader_sha256=p.sha(READER/'result.json'),minimum_wall_seconds=minimum[0],minimum_full_cpu_seconds=minimum[1],reader_allowance_seconds=2),
        scope='Only missing whole-original/contact/final/control stages after actual001; classifier/engine/selected Native not repeated. Cumulative120 includes all001 costs/readback+2. Prioractive002 exploration separately disclosed; no fresh first attempt, free incumbent, confirmatory, production or electrical claim.')
    def stable():
        h.owned_destination(owner);need(remaining()>0,'cumulative120 wall/fullCPU exhausted')
        need(p.sha(protocol)==protocol_sha and p.tool_manifest()==tools and p.tree_hash(source.parent)==hashes and p.tree_hash(out/'original')==hashes,'continuation protocol/runtime/original changed')
        need(p.tree_hash(out/'code')=={Path(n).name:pin for n,pin in tools['implementation_sha256'].items()},'captured current core changed')
        need(p.tree_hash(out/'helper-code')=={n:pin for n,pin in spec['code_sha256'].items() if n not in tools['implementation_sha256']},'captured current helpers changed')
        for name,pin in spec['code_sha256'].items():need(p.sha(ROOT/name)==pin,'current code changed: '+name)
        for name,pin in spec['prefixes'].items():need(inventory(ROOT/name)==pin,'retained prefix changed: '+name)
        for name,pin in spec['retained_files'].items():need(p.sha(ROOT/name)==pin,'retained producer changed: '+name)
        pc.inventory(out,max_bytes=LIMIT,max_files=6000,max_entries=12000)
        if completed is not None:need(f.evidence_inventory(out)==completed,'completed continuation changed')
    def retained_readback():
        need(probe_data['status']=='completed' and probe_data['eligibility_qualified'] is True and probe_data['source_hashes']==hashes and probe_data['tools']==old_tools and child_data['tools']==old_tools,'retained classifier/child identity differs')
        need(f.evidence_inventory(PROBE)==probe_data['completed_evidence'] and p.sha(PROBE/'result.json')==old['classifier_sha256'] and p.sha(child/'result.json')==old['child_receipt_sha256'],'retained completed stage/receipt differs')
        task=PROBE/'task'/source.name
        classification=nc.readback(PROBE,probe_data,source,task,PROBE/'refill'/source.name,PROBE/'candidate'/source.name,PROBE/'native.dsn')
        need(f.canonical(classification)==f.canonical(old['classification']) and classification['inactive_names']==['GND'] and len(classification['active_names'])==5 and classification['active_names']==old['selected_names'],'actual22-terminal classifier/active population differs')
        need(pc.read_bytes(task)==(sx.dump(g.task_from_source(original))+'\n').encode() and not p.routes(sx.read(task)) and p.tree_hash(task.parent)==old['task_hashes'],'retained classifier task not exact zero-route original shell')
        settings=pref.validate(f.read_json(OLD/'route-preferences.json'))
        need(p.sha(OLD/'route-preferences.json')==old['preferences_sha256'] and settings['nets']==classification['active_names'] and settings['profile']=='completion-only' and settings['adapter']=='both' and settings['guidance']=='native' and settings['layers']=='source_all','retained actual selected preferences differ')
        pair._contact_child(child,child_data,task,old['task_hashes'],settings,old['selected_names'])
        need(tuple(child_data['native'][key] for key in ('opens','blocking','warnings','exclusions'))==(0,1,10,0) and child_data['accepted'] is False,'actual001 child remains sole-thermal rejected')
        return task,settings
    def account():
        wall,full=time.monotonic()-START,cpu()-CPU0
        record.update(new_wall_seconds=wall,new_full_cpu_seconds=full,charged_wall_seconds=charged[0]+BOOT+wall,charged_full_cpu_seconds=charged[1]+BOOT+full,within_budget=remaining()>0,steps=[step for job in state.get('jobs',[]) for step in job.steps])
        record.update(cumulative_active002_reader_and_continuation_wall_seconds=27.294584+record['charged_wall_seconds'],cumulative_active002_reader_and_continuation_full_cpu_seconds=22.430367+record['charged_full_cpu_seconds'])
        if record['status']!='completed' or not record['within_budget']:record['method_qualified']=False
        record.update(accepted=False,production_admitted=False)
    def replay():
        stable();retained_readback()
        pair._contact_replay(state,record,original,hashes,old_tools);stable()
    try:
        stable();task,settings=retained_readback()
        pair._contact_treatment(state,record,out,source,original,hashes,task,child,child_data,settings,old_tools,remaining_seconds=remaining)
        replay();completed=f.evidence_inventory(out);record['completed_material']=completed
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',method_qualified=False,initial_failure=type(exc).__name__+': '+str(exc),reason=type(exc).__name__+': '+str(exc))
    return f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=replay)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);args=ap.parse_args()
    if not args.run_native:ap.error('--run-native required after prospectively frozen checkpoint')
    def stop(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
    d=experiment(args.output,args.protocol,args.protocol_sha256);print(json.dumps({k:d[k] for k in ('status','method_qualified','charged_wall_seconds','charged_full_cpu_seconds')}));raise SystemExit(0 if d['method_qualified'] else 2)
