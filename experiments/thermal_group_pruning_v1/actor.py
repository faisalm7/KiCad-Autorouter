"""One fused thermal-informed deletion/final Native check; no incumbent rerun."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
from types import SimpleNamespace
import sys,json,signal
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,placement_clearance as pc,routing_scope as rs,local_settings as ls,thermal,thermal_geometry as geom,handoff as h,review_export as e
from experiments.native_connected_pair_v1 import driver as pair
from experiments.native_contact_continuation_v1.actor import inventory,need
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.thermal_group_pruning_v1.proposal import derive
FOUR=ROOT/'.runs/nus-selected-proposal-native120-004';TWO=ROOT/'.runs/nus-native-connected-contact120-002'
FIVE=ROOT/'.runs/nus-physical-short-native120-005';REVIEW=ROOT/'.runs/physical-short005-native-review-preserved-001'
PROTOCOL=Path(__file__).with_name('input-pins.json')
RESERVE=4.0 # one second outer publication plus three for independent pure readback

def prior_charge():
    rows=[f.read_json(path) for path in (FIVE/'result.json',ROOT/'.runs/nus-physical-short-native120-005-execution/result.json',ROOT/'.runs/nus-physical-short-native120-005-lead-execution/execution.json')]
    audit=f.read_json(REVIEW/'execution.json');cost=audit['whole_reader_execution_cost']
    need(all(row.get('method_qualified',row.get('outer_qualified')) is True for row in rows),'005 diagnostic must remain qualified')
    values=[max(row['charged_wall_seconds'] for row in rows)+cost['wall_seconds']+audit['startup_allowance_seconds'],max(row['charged_full_cpu_seconds'] for row in rows)+cost['full_cpu_seconds']+audit['startup_allowance_seconds']]
    need(all(e.finite(x) and x<120 for x in values),'invalid cumulative actual005 charge')
    return dict(wall_seconds=values[0],full_cpu_seconds=values[1])

def phase(folder,steps,source,hashes,tools):
    candidate=folder/'candidate'/source.name
    saved=f.check_drc_stage(folder,{'steps':steps},'refill-drc',folder/'refill'/source.name,folder/'refill'/source.name,True,{**hashes,source.name:p.sha(folder/'pre-refill.kicad_pcb')})
    native=f.check_drc_stage(folder,{'steps':steps},'final-drc',candidate,folder/'final-drc-input'/source.name,False,{**hashes,source.name:p.sha(candidate)},schematic_parity=True)
    original=sx.read(source);entry=dict(job=SimpleNamespace(out=folder,steps=steps),candidate=str(candidate),candidate_sha256=p.sha(candidate),native=native,saved_native=saved,report_sha256=p.sha(folder/'final-drc.json'))
    pair._contact_phase_readback(entry,original,hashes)
    p.check_pour_evidence(folder,{'steps':steps},original,candidate,source_hashes=hashes,correction=False,sandboxed=True)
    p.check_legacy_zone_evidence(folder,original,candidate,implementation=tools['implementation_sha256'])
    ls.check_normal_policy(folder,dict(tools=tools,steps=steps,source_hashes=hashes))
    f.process_check(folder,{'steps':steps},'metrics',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(folder/'metrics.json')])
    return entry,f.read_json(folder/'metrics.json')

def retained(spec):
    old=f.read_json(FOUR/'result.json');two=f.read_json(TWO/'result.json');source=Path(spec['source']);hashes=spec['source_hashes'];original=p.preflight(source)
    current=p.tool_manifest();changes={name:dict(retained=pin,current=current['implementation_sha256'].get(name)) for name,pin in old['tools']['implementation_sha256'].items() if current['implementation_sha256'].get(name)!=pin}
    need(old['source']==str(source) and old['source_hashes']==hashes and p.tree_hash(source.parent)==hashes and current['files']==old['tools']['files'] and current['kicad']==old['tools']['kicad'] and current['freerouting']==old['tools']['freerouting'],'retained source/native binary identity differs')
    need(changes==spec['disclosed_validator_changes'] and set(changes)=={'autorouter/adapter.py','autorouter/local_settings.py','autorouter/pipeline.py'},'undisclosed retained/current validator change')
    need(old['status']=='failed' and old['method_qualified'] is False and old['wrong_net_control']['qualified'] is False,'failed004 history changed')
    base=FOUR/'positive';steps=[x for x in old['steps'] if x['cwd']==str(base)]
    entry,metrics=phase(base,steps,source,hashes,old['tools'])
    need(entry['candidate_sha256']==old['candidate_sha256']==spec['base_candidate_sha256'] and entry['native']==old['native'] and metrics==old['metrics'],'retained004 actual positive differs')
    baseline=f.check_drc_stage(TWO/'whole-validation',{'steps':two['steps']},'pristine-original',TWO/'whole-validation/snapshot'/source.name,TWO/'whole-validation/pristine-original-input'/source.name,False,hashes,schematic_parity=True)
    repair=TWO/'whole-validation/contact-repair';scene=f.read_json(repair/'geometry.json');request=f.read_json(repair/'request.json');warm=Path(spec['warm_source']);warm_tree=sx.read(warm)
    failed=f.check_drc_stage(TWO/'whole-validation',{'steps':two['steps']},'final-drc',TWO/'whole-validation/candidate'/source.name,TWO/'whole-validation/final-drc-input'/source.name,False,{**hashes,source.name:p.sha(warm)},schematic_parity=True)
    finding=thermal.sole_thermal(failed)
    need(finding is not None and finding==scene['finding'] and scene['board_sha256']==p.sha(warm) and scene['project_sha256']==hashes[source.with_suffix('.kicad_pro').name] and scene['source_unchanged'] is True and scene['board_saved'] is False and scene['api_error_count']==0 and scene['status']=='observations_complete' and scene['native_version']=='10.0.0','retained thermal geometry differs')
    need(request['final_drc_sha256']==p.sha(TWO/'whole-validation/final-drc.json') and request['candidate_files']==p.tree_hash(repair/'input'),'retained geometry request/source differs')
    f.process_check(repair,{'steps':two['steps']},'thermal-geometry',[*f.SANDBOX,str(p.c.PYTHON),'-B',str(repair/'worker.py'),str(repair/'input'/source.name),str(repair/'request.json'),str(repair/'geometry.json')])
    tree,proposal=derive(original,warm_tree,sx.read(Path(entry['candidate'])),scene,finding)
    names=[proposal['net_name']];protected=rs.protected_routes(warm_tree,names);proof=f.read_json(FOUR/'selected-proposals.json')
    p.check_protected_import(FOUR,{'scope':'selected_nets','protected_route_import':proof},rs.task(warm_tree,names),FOUR/'prepared.kicad_pcb',protected,expected_policy=p.SELECTED_PROPOSAL_IMPORT_POLICY,selected_names=names)
    need(proof==old['protected_route_import'] and p.routes(sx.read(FOUR/'prepared.kicad_pcb'))==p.routes(sx.read(Path(entry['candidate']))) and rs.audit(warm_tree,sx.read(Path(entry['candidate'])),names)==old['protected_signal_audit'],'retained selected proof differs')
    need(len(protected)==22 and len(proof['selected_proposals'])==18 and len(proposal['deleted_route_ids'])==13 and len(p.routes(tree))==27 and p.native_accepted(baseline) and p.native_accepted(entry['native']) and pair.warnings(baseline)==pair.warnings(entry['native']) and baseline['warnings']==10,'frozen proposal/Native scope differs')
    return tree,proposal,protected,baseline,metrics

def check(out,data,spec,*,final=False):
    identity=dict(schema=1,kind='thermal-group-pruning-single-final-v1',accepted=False,production_admitted=False,budget_seconds=120,cpu_budget_seconds=120,reserved_publication_and_independent_readback_seconds=RESERVE,human_pcb_approval_observed=False,physical_electrical_validation=False)
    need(all(type(data.get(k)) is type(v) and data[k]==v for k,v in identity.items()),'final diagnostic identity differs')
    need(data['protocol_sha256']==p.sha(PROTOCOL) and data['prior_costs']==prior_charge() and data['tools']==p.tool_manifest(),'receipt protocol/prior/current tools differ')
    if final:
        need(data['status']=='completed' and data['method_qualified'] is True and data['within_reserved_budget'] is True,'final diagnostic qualification differs')
        need(all(e.finite(data[k]) for k in ('new_wall_seconds','new_full_cpu_seconds')) and data['prior_costs']['wall_seconds']+data['new_wall_seconds']+RESERVE<120 and data['prior_costs']['full_cpu_seconds']+data['new_full_cpu_seconds']+RESERVE<120,'final diagnostic resource claims differ')
    source=Path(spec['source']);tree,proposal,protected,baseline,old_metrics=retained(spec)
    need(data['candidate']==str(out/'validation/candidate'/source.name) and data['original_native']==baseline and data['retained_metrics']==old_metrics,'final candidate/baseline claims differ')
    need(data['proposal']==proposal and p.sha(out/'validation/pre-refill.kicad_pcb')==h.digest((sx.dump(tree)+'\n').encode()),'deletion replay/preimage differs')
    entry,metrics=phase(out/'validation',data['steps'],source,spec['source_hashes'],data['tools'])
    need(entry['candidate_sha256']==data['candidate_sha256'] and entry['native']==data['native'] and metrics==data['metrics'] and entry['report_sha256']==data['native_report_sha256'],'new final Native proof differs')
    from autorouter import placement_strategy as ps
    need(p.native_accepted(entry['native']) and pair.warnings(entry['native'])==pair.warnings(baseline) and ps.improves(metrics,old_metrics,entry['native'],baseline),'new candidate lacks Nativevalid improvement')
    protection=rs.audit(sx.read(Path(spec['warm_source'])),sx.read(Path(entry['candidate'])),[proposal['net_name']])
    need(protection['scope_passed'] is True and protection['protected_count']==22,'source protection changed')
    return True

def final_material(out,data,spec,tools,receipt_pin,protocol_pin):
    """Final callbacks must precede the last sweep of all previously read bytes."""
    current=p.tool_manifest()
    need(p.sha(PROTOCOL)==protocol_pin and current==tools,'final source/tools changed')
    need(p.sha(out/'result.json')==receipt_pin and f.evidence_inventory(out)==data['completed_material'],'final new material changed')
    for name,expected in spec['prefixes'].items():need(inventory(ROOT/name)==expected,'final retained material changed: '+name)
    for name,expected in spec['code_sha256'].items():need(p.sha(ROOT/name)==expected,'final code changed: '+name)
    need(p.tree_hash(Path(spec['source']).parent)==spec['source_hashes'],'final original project changed')

def experiment(out):
    spec=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL);tools=p.tool_manifest();prior=prior_charge()
    need(spec['status']=='prospectively_frozen' and spec['actor_sha256']==p.sha(__file__) and spec['prior_costs']==prior,'unfrozen source/prior')
    previous=f.read_json(FIVE/'prospective-pins.json')
    required_prefixes=set(previous['prefixes'])|{str(x.relative_to(ROOT)) for x in (FOUR,TWO,FIVE,REVIEW,ROOT/'.runs/nus-physical-short-native120-005-execution',ROOT/'.runs/nus-physical-short-native120-005-lead-execution')}
    required_code=set(previous['code_sha256'])|set(tools['implementation_sha256'])|{str(Path(__file__).relative_to(ROOT)),str(Path(__file__).with_name('proposal.py').relative_to(ROOT)),str(Path(__file__).with_name('run.py').relative_to(ROOT))}
    need(required_prefixes<=set(spec['prefixes']) and required_code<=set(spec['code_sha256']),'whole retained/current source closure missing')
    need(all(not Path(n).is_absolute() and '..' not in Path(n).parts for group in ('prefixes','code_sha256') for n in spec[group]),'bounded project-relative frozen paths required')
    out.mkdir();owner={};h.capture_destination(owner,out);job=None;completed=None
    record=dict(schema=1,kind='thermal-group-pruning-single-final-v1',status='failed',accepted=False,production_admitted=False,method_qualified=False,human_pcb_approval_observed=False,physical_electrical_validation=False,tools=tools,protocol_sha256=pin,prior_costs=prior,reserved_publication_and_independent_readback_seconds=RESERVE,budget_seconds=120,cpu_budget_seconds=120,steps=[],scope='ONE fused pruning/finalvalidation of own004positive, exact22signals and sourceconstraints retained. No rerouting, classifier/export/import/positive/control repeat. Existing005physicalshort proof retained. Diagnostic singleexposedNUS, no normal-C or broad/independent superiority claim. Earlier27.294584wall22.430367CPU pilot remains separate exposedexploration.')
    def left():return min(120-prior['wall_seconds']-RESERVE-(time.monotonic()-START),120-prior['full_cpu_seconds']-RESERVE-(cpu()-CPU0))
    def stable():
        h.owned_destination(owner);need(left()>0 and p.sha(PROTOCOL)==pin and p.tool_manifest()==tools,'continuation budget/source/tools changed')
        for name,value in spec['code_sha256'].items():need(p.sha(ROOT/name)==value,'frozen source changed: '+name)
        for name,value in spec['prefixes'].items():need(inventory(ROOT/name)==value,'retained evidence changed: '+name)
        need(p.tree_hash(Path(spec['source']).parent)==spec['source_hashes'],'original project changed')
        if completed is not None:need(f.evidence_inventory(out)==completed,'new complete material changed')
    def account():
        record.update(new_wall_seconds=time.monotonic()-START,new_full_cpu_seconds=cpu()-CPU0,within_reserved_budget=left()>0,steps=[] if job is None else job.steps)
        if record['status']!='completed' or left()<=0:record['method_qualified']=False
    def replay():
        stable()
        if record.get('method_qualified'):check(out,record,spec,final=True)
        stable()
    try:
        stable();tree,proposal,protected,baseline,old_metrics=retained(spec);record.update(proposal=proposal,original_native=baseline,retained_metrics=old_metrics)
        need(left()>=6,'insufficient budget after complete retained readback')
        source=Path(spec['source']);hashes=spec['source_hashes'];job=f.FloorJob(out/'validation',left(),left,protect_local_settings=True)
        files=pc.inventory(source.parent,contents=True);copy_bytes(files,job.out/'snapshot');copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},job.out/'code')
        files[source.name]=(sx.dump(tree)+'\n').encode();copy_bytes(files,job.out/'candidate');candidate=job.out/'candidate'/source.name;(job.out/'pre-refill.kicad_pcb').write_bytes(files[source.name])
        digest,native=p.validate_candidate(job,p.preflight(source),candidate,hashes,protected,schematic_parity=True)
        job.native('metrics','metrics',candidate,job.out/'metrics.json');metrics=f.read_json(job.out/'metrics.json')
        record.update(candidate=str(candidate),candidate_sha256=digest,native=native,native_report_sha256=p.sha(job.out/'final-drc.json'),metrics=metrics,steps=job.steps)
        check(out,record,spec);record.update(status='completed',method_qualified=True)
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',reason=type(exc).__name__+': '+str(exc))
    completed=f.evidence_inventory(out);record['completed_material']=completed
    return f.publish(out,record,stable,account,left,owned=lambda:h.owned_destination(owner),final_check=replay)

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if not a.run_native or a.output.parent!=ROOT/'.runs' or a.output.exists():ap.error('explicit Nativeoptin and fresh directoutput required')
    def stop(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
    r=experiment(a.output);print(json.dumps({k:r.get(k) for k in ('status','method_qualified','reason','new_wall_seconds','new_full_cpu_seconds')}));raise SystemExit(0 if r['method_qualified'] else 2)
