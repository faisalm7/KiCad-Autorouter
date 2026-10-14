"""Unexecuted missing Native stages for exact retained003 selected proposals; cumulative120."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import argparse,copy,json,math,signal,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,board_floor as g,placement_clearance as pc,handoff as h,routing_scope as rs,local_settings
from experiments.native_connected_pair_v1 import driver as pair
from experiments.native_contact_continuation_v1.actor import inventory,need
from experiments.placement_handoff_native_v1.driver import copy_bytes
THREE=ROOT/'.runs/nus-native-feedback-engine120-003';GROUND=THREE/'ground-route';TWO=ROOT/'.runs/nus-native-connected-contact120-002'
OUTER=ROOT/'.runs/nus-native-feedback-engine120-003-execution';LEAD=ROOT/'.runs/nus-native-feedback-engine120-003-lead-execution'
AUDIT=ROOT/'.runs/native-feedback-engine003-review-preserved-001'
POLICY='selected-proposal-missing-native-stages-v1';IMPORT_POLICY='selected-proposals-exact-source-v1';BOOT=1;LIMIT=64*1024**2
OLD_PIPELINE='74023e683ab3fef1d0e6365b9c3c1b758c7e1f447c0ce6f7d66efb51b9fd34b5'

def check_outer_witness(out,data,spec,protocol_sha):
    identity={'schema':1,'kind':POLICY,'status':'completed','method_qualified':True,'accepted':False,'production_admitted':False,'budget_seconds':120,'cpu_budget_seconds':120,'bootstrap_allowance_seconds':1,'protocol_sha256':protocol_sha,'import_policy':IMPORT_POLICY}
    need(all(type(data.get(k)) is type(v) and data[k]==v for k,v in identity.items()),'selected proposal continuation identity differs')
    need(f.canonical(data['prior_costs'])==f.canonical(spec['prior_costs']),'prior charges differ')
    for new,charged,prior in [('new_wall_seconds','charged_wall_seconds','wall_seconds'),('new_full_cpu_seconds','charged_full_cpu_seconds','full_cpu_seconds')]:
        a=data[new];need(type(a) in (int,float) and math.isfinite(a) and a>=0 and data[charged]==spec['prior_costs'][prior]+BOOT+a,'cumulative algebra differs')
    need(data['within_budget'] is True and max(data['charged_wall_seconds'],data['charged_full_cpu_seconds'])<120 and data['wrong_net_control']['qualified'] is True,'cumulative cap/control differs')
    need(f.evidence_inventory(out)==data['completed_material'] and p.tool_manifest()==data['tools'] and p.tree_hash(Path(spec['source']).parent)==spec['source_hashes'],'completed/current material differs')
    for group in ('code_sha256','retained_files'):
        for name,pin in spec[group].items():need(p.sha(ROOT/name)==pin,'frozen file changed: '+name)
    for name,pin in spec['prefixes'].items():need(inventory(ROOT/name)==pin,'retained prefix changed: '+name)

def experiment(out,protocol,protocol_sha):
    need(Path(__file__).parent==ROOT/'experiments/selected_proposal_continuation_v1','promote/review/checkpoint before Native')
    need(out.parent==ROOT/'.runs' and not out.exists() and not out.is_symlink(),'fresh direct output required')
    need(p.sha(protocol)==protocol_sha,'prospective protocol differs');spec=f.read_json(protocol)
    need(spec['status']=='prospectively_frozen' and spec['policy']==POLICY and spec['import_policy']==IMPORT_POLICY==p.SELECTED_PROPOSAL_IMPORT_POLICY and spec['actor_sha256']==p.sha(__file__) and spec['cumulative_wall_full_cpu_seconds']==120 and spec['bootstrap_allowance_seconds']==BOOT,'unfrozen exact selected proposal policy')
    need(all(not Path(n).is_absolute() and '..' not in Path(n).parts for group in ('code_sha256','retained_files','prefixes') for n in spec[group]),'project-relative frozen paths required')
    old=f.read_json(THREE/'result.json');ground=f.read_json(GROUND/'result.json');two=f.read_json(TWO/'result.json');outer=f.read_json(OUTER/'result.json');lead=f.read_json(LEAD/'execution.json');previous=f.read_json(THREE/'prospective-pins.json')
    audit=f.read_json(AUDIT/'result-corrected.json');execution=f.read_json(AUDIT/'execution-corrected.json');first_execution=f.read_json(AUDIT/'execution.json');prior=spec['prior_costs'];charged=[prior['wall_seconds'],prior['full_cpu_seconds']]
    costs=execution['both_actual_reader_costs'];minimum=[max(old['charged_wall_seconds'],outer['charged_wall_seconds'],lead['charged_wall_seconds'])+costs['wall_seconds']+4,max(old['charged_full_cpu_seconds'],outer['charged_full_cpu_seconds'],lead['charged_full_cpu_seconds'])+costs['full_cpu_seconds']+4]
    need(all(type(v) in (int,float) and math.isfinite(v) and bound<=v<119 for v,bound in zip(charged,minimum)) and execution['both_startup_allowances_seconds']==4,'omitted failed001002003/bothreader costs')
    need(audit['passed'] is True and audit['native_route_acceptance_performed'] is False and audit['source_result_sha256']==p.sha(THREE/'result.json') and execution['result_sha256']==p.sha(AUDIT/'result-corrected.json') and execution['previous_reader_execution_sha256']==p.sha(AUDIT/'execution.json'),'corrected and failed reader continuity differs')
    need(all(abs(costs[k]-execution['whole_reader_execution_cost'][k]-first_execution['whole_reader_execution_cost'][k])<1e-12 for k in ('wall_seconds','full_cpu_seconds')),'both actual reader costs differ')
    for row in (outer,lead):need(row['process']['status']=='nonzero_exit' and type(row['process']['exit_code']) is int and row['process']['exit_code']==2 and row['process']['cleanup_complete'] is True,'retained003 outer did not cleanly reject')
    left=lambda:min(120-charged[0]-BOOT-(time.monotonic()-START),120-charged[1]-BOOT-(cpu()-CPU0))
    source=Path(spec['source']);hashes=spec['source_hashes'];original=p.preflight(source);tools=p.tool_manifest();old_tools=old['tools'];classification=f.read_json(ROOT/'.runs/nus-native-connected-contact120-001/result.json')['classification']
    need(classification['inactive_names']==['GND'] and len(classification['active_names'])==5,'fixed prior classifier active/inactive names differ')
    def normalized(value):
        result=copy.deepcopy(value);result.pop('git_head');result['implementation_sha256'].pop('autorouter/pipeline.py');return result
    need(old_tools==ground['tools'] and old_tools['implementation_sha256']['autorouter/pipeline.py']==OLD_PIPELINE==spec['old_pipeline_sha256'] and normalized(old_tools)==normalized(tools),'only explicitly audited pipeline/HEAD producer difference allowed')
    need(tools['implementation_sha256']['autorouter/pipeline.py']==spec['new_pipeline_sha256'] and p.sha(GROUND/'code/pipeline.py')==OLD_PIPELINE,'new/old captured pipeline source differs')
    need(old['source']==str(source) and old['source_hashes']==hashes and len(hashes)==8 and old['accepted'] is False and old['method_qualified'] is False and old['reason']=='Rejected: selected-GND fallback rejected' and ground['accepted'] is False and ground['reason']=='Rejected: protected route missing, changed or ambiguous after import','preserved003 source/import failure differs')
    required=set(previous['prefixes'])|{str(x.relative_to(ROOT)) for x in (THREE,OUTER,LEAD,AUDIT)}
    need(required<=set(spec['prefixes']) and set(previous['code_sha256'])|set(tools['implementation_sha256'])|{'experiments/selected_proposal_continuation_v1/actor.py','experiments/selected_proposal_continuation_v1/run.py'}<=set(spec['code_sha256']),'complete prior/current closure missing')
    need([step['name'] for step in ground['steps']]==['source-drc','export','obstacles','engine','import'] and not (GROUND/'refill').exists() and not (GROUND/'final-drc.json').exists(),'only actually missing Native stages permitted')
    warm=THREE/'warm-source'/source.name;warm_tree=sx.read(warm);task=rs.task(warm_tree,['GND']);protected=rs.protected_routes(warm_tree,['GND'])
    need(ground['source']==str(warm) and p.tree_hash(warm.parent)==old['warm_source_hashes']==ground['source_hashes'] and p.sha(GROUND/'result.json')==old['ground_receipt_sha256'] and inventory(GROUND)==old['ground_inventory'],'exact own003 warm source/child differs')
    need(p.immutable(warm_tree)==p.immutable(original) and len(protected)==22 and len(p.routes(task))==22 and audit['geometry']['selected_imported_segments']==18 and audit['raw_ses_sha256']==p.sha(GROUND/'routes.ses') and audit['imported_board_sha256']==p.sha(GROUND/'imported.kicad_pcb'),'fixed exact22 signals/18 selected proposal lineage differs')
    out.mkdir();owner={};h.capture_destination(owner,out);copy_bytes(pc.inventory(source.parent,contents=True),out/'original',expected_parent_owner=owner)
    copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},out/'code',expected_parent_owner=owner)
    copy_bytes({n:pc.read_bytes(ROOT/n) for n in spec['code_sha256'] if n not in tools['implementation_sha256']},out/'helper-code',expected_parent_owner=owner)
    with (out/'imported.kicad_pcb').open('xb') as stream:stream.write(pc.read_bytes(GROUND/'imported.kicad_pcb'))
    p.save_json(out/'prospective-pins.json',spec);jobs=[];phases={};prepared=None;completed=None
    record=dict(schema=1,kind=POLICY,status='incomplete',method_qualified=False,accepted=False,production_admitted=False,budget_seconds=120,cpu_budget_seconds=120,bootstrap_allowance_seconds=BOOT,protocol_sha256=protocol_sha,import_policy=IMPORT_POLICY,prior_costs=prior,source=str(source),source_hashes=hashes,tools=tools,retained_stage_tools=old_tools,allowed_core_change={'autorouter/pipeline.py':{'old':OLD_PIPELINE,'new':spec['new_pipeline_sha256']}},prior_minimum_wall_seconds=minimum[0],prior_minimum_full_cpu_seconds=minimum[1],steps=[],original_native_reused_from=str(TWO/'whole-validation/pristine-original.json'),wrong_net_control={'status':'not_run','qualified':False,'reason':'positive Native not yet accepted'},scope='Only missing whole Native/metrics/conditional wrong-net after failed003; no classifier/engine/export/import/baseline/geometry repeat. All own001002003+bothreader costs retained under same120; no normalrouting/production/novelty/independence claim.')
    def stable():
        h.owned_destination(owner);need(left()>0,'cumulative120 exhausted')
        need(p.sha(protocol)==protocol_sha and p.tool_manifest()==tools and p.tree_hash(source.parent)==hashes and p.tree_hash(out/'original')==hashes,'current source/protocol/runtime changed')
        need(p.tree_hash(out/'code')=={Path(n).name:pin for n,pin in tools['implementation_sha256'].items()} and p.tree_hash(out/'helper-code')=={n:pin for n,pin in spec['code_sha256'].items() if n not in tools['implementation_sha256']},'captured current source differs')
        for group in ('code_sha256','retained_files'):
            for name,pin in spec[group].items():need(p.sha(ROOT/name)==pin,'frozen file changed: '+name)
        for name,pin in spec['prefixes'].items():need(inventory(ROOT/name)==pin,'retained prefix changed: '+name)
        need(p.sha(out/'imported.kicad_pcb')==audit['imported_board_sha256'],'owned exact imported copy changed')
        pc.inventory(out,max_bytes=LIMIT,max_files=6000,max_entries=12000)
        if completed is not None:need(f.evidence_inventory(out)==completed,'completed material changed')
    def baseline():
        directory=TWO/'whole-validation';native=f.check_drc_stage(directory,{'steps':two['steps']},'pristine-original',directory/'snapshot'/source.name,directory/'pristine-original-input'/source.name,False,hashes,schematic_parity=True)
        need(native==two['original_native'] and p.native_accepted(native) and native['warnings']==10 and p.sha(directory/'pristine-original.json')==two['original_native_report_sha256'],'retained original baseline differs');return native
    def proof():
        if prepared is None:return
        need(p.sha(prepared)==record['prepared_sha256'] and record['import_policy']==IMPORT_POLICY==p.SELECTED_PROPOSAL_IMPORT_POLICY and f.read_json(out/'selected-proposals.json')==record['protected_route_import'],'mandatory selected proposal proof missing/changed')
        p.check_protected_import(out,{'scope':'selected_nets','protected_route_import':record['protected_route_import']},task,prepared,protected,expected_policy=IMPORT_POLICY,selected_names=['GND'])
        need(rs.audit(warm_tree,sx.read(prepared),['GND'])==record['protected_signal_audit'],'prepared original signals changed')
    def validate(name,tree):
        value=f.FloorJob(out/name,left(),left,protect_local_settings=True);jobs.append(value);copy_bytes(pc.inventory(source.parent,contents=True),value.out/'snapshot');copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},value.out/'code')
        files=pc.inventory(source.parent,contents=True);files[source.name]=(sx.dump(tree)+'\n').encode();copy_bytes(files,value.out/'candidate');candidate=value.out/'candidate'/source.name;(value.out/'pre-refill.kicad_pcb').write_bytes(files[source.name]);entry={'job':value,'candidate':str(candidate)};phases[name]=entry
        digest,native=p.validate_candidate(value,original,candidate,hashes,protected,schematic_parity=True)
        saved=f.check_drc_stage(value.out,{'steps':value.steps},'refill-drc',value.out/'refill'/source.name,value.out/'refill'/source.name,True,{**hashes,source.name:p.sha(value.out/'pre-refill.kicad_pcb')})
        entry.update(candidate_sha256=digest,native=native,saved_native=saved,report_sha256=p.sha(value.out/'final-drc.json'));pair._contact_phase_readback(entry,original,hashes);return entry
    def wrong_net(tree):
        bad=copy.deepcopy(tree);_,resolve=g.source_net_identity(bad);protected_ids={sx.unquote(sx.one(n,'uuid')[1]) for n in protected}
        choices=sorted((sx.unquote(sx.one(n,'uuid')[1]),n) for n in p.routes(bad) if n[0]=='segment' and sx.unquote(sx.one(n,'uuid')[1]) not in protected_ids and resolve(sx.one(n,'net'))=='GND');need(choices,'new GND segment required for control')
        target_uuid,target=choices[0];wrong_name=sorted(classification['active_names'])[0];declarations=[n for n in sx.children(original,'net') if sx.unquote(n[2])==wrong_name];need(len(declarations)==1,'exact fixed numbered active-net declaration required')
        before=copy.deepcopy(bad);net=sx.one(target,'net');need(len(net) in (2,3),'ordinary route net field required');net[1]=declarations[0][1]
        if len(net)==3:net[2]=declarations[0][2]
        difference=[(a,b) for a,b in zip(p.routes(before),p.routes(bad)) if a!=b];need(len(difference)==1 and p.immutable(bad)==p.immutable(original) and all(n in p.routes(bad) for n in protected),'wrong-net control changed extra source/protected geometry')
        return bad,{'segment_uuid':target_uuid,'from_net':'GND','to_net':wrong_name}
    def replay():
        stable();native_original=baseline();proof()
        for name,entry in phases.items():
            if 'candidate_sha256' not in entry:continue
            pair._contact_phase_readback(entry,original,hashes);local_settings.check_normal_policy(entry['job'].out,{'tools':tools,'source_hashes':hashes,'steps':entry['job'].steps})
            if name=='positive':
                need(p.routes(sx.read(Path(entry['candidate'])))==p.routes(sx.read(prepared)),'positive proposal routes changed')
                rs.audit(warm_tree,sx.read(Path(entry['candidate'])),['GND'])
        if 'metrics_sha256' in record:
            e=phases['positive'];j=e['job'];f.process_check(j.out,{'steps':j.steps},'metrics',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',e['candidate'],str(j.out/'metrics.json')]);need(f.read_json(j.out/'metrics.json')==record['metrics'] and p.sha(j.out/'metrics.json')==record['metrics_sha256'],'positive actual metrics differ')
        if 'wrong-net' in phases and 'candidate_sha256' in phases['wrong-net']:
            expected_bad,control=wrong_net(sx.read(Path(phases['positive']['candidate'])));e=phases['wrong-net'];need(p.routes(expected_bad)==p.routes(sx.read(Path(e['candidate']))) and all(record['wrong_net_control'][k]==v for k,v in control.items()) and record['wrong_net_control']['candidate_sha256']==e['candidate_sha256'] and record['wrong_net_control']['native']==e['native'] and record['wrong_net_control']['report_sha256']==e['report_sha256'],'wrong-net control exact replay differs')
        if record['method_qualified']:
            positive=phases['positive'];negative=phases['wrong-net'];need(p.native_accepted(positive['native']) and pair.warnings(positive['native'])==pair.warnings(native_original) and record['candidate_sha256']==positive['candidate_sha256'] and record['native']==positive['native'] and record['wrong_net_control']['qualified'] is True and not p.native_accepted(negative['native']) and negative['native']['opens']+negative['native']['blocking']>0 and negative['native']['exclusions']==0 and set(pair.warnings(native_original))<=set(pair.warnings(negative['native'])),'positive/negative Native acceptance differs')
    def account():
        wall,full=time.monotonic()-START,cpu()-CPU0;record.update(new_wall_seconds=wall,new_full_cpu_seconds=full,charged_wall_seconds=charged[0]+BOOT+wall,charged_full_cpu_seconds=charged[1]+BOOT+full,within_budget=left()>0,steps=[step for job in jobs for step in job.steps]);record.update(cumulative_active002_reader_and_selected_proposals_wall_seconds=27.294584+record['charged_wall_seconds'],cumulative_active002_reader_and_selected_proposals_full_cpu_seconds=22.430367+record['charged_full_cpu_seconds'])
        if record['status']!='completed' or not record['within_budget']:record['method_qualified']=False
    try:
        stable();native_original=baseline();import_audit={'imported_sha256':p.sha(out/'imported.kicad_pcb')}
        combined=p.transplant_routes(task,sx.read(out/'imported.kicad_pcb'),protected=protected,audit=import_audit,policy=IMPORT_POLICY,selected_names=['GND']);tree=g.task_from_source(original);tree.extend(copy.deepcopy(p.routes(combined)))
        need(p.immutable(tree)==p.immutable(original) and p.routes(tree)==p.routes(combined),'original unrouted shell/proposal reconstruction differs')
        prepared=out/'prepared.kicad_pcb';sx.write(prepared,tree);record.update(protected_route_import=import_audit,protected_signal_audit=rs.audit(warm_tree,tree,['GND']),prepared_sha256=p.sha(prepared));p.save_json(out/'selected-proposals.json',import_audit);proof();stable()
        positive=validate('positive',tree);record.update(candidate=positive['candidate'],candidate_sha256=positive['candidate_sha256'],native=positive['native'],native_report_sha256=positive['report_sha256'],original_native=native_original,original_native_report_sha256=p.sha(TWO/'whole-validation/pristine-original.json'))
        j=positive['job'];j.native('metrics','metrics',Path(positive['candidate']),j.out/'metrics.json');metrics=f.read_json(j.out/'metrics.json');need(metrics['version']=='10.0.0' and type(metrics['vias']) is int and metrics['vias']>=0 and type(metrics['track_length_mm']) in (int,float) and math.isfinite(metrics['track_length_mm']) and metrics['track_length_mm']>=0,'actual positive metrics invalid');record.update(metrics=metrics,metrics_sha256=p.sha(j.out/'metrics.json'))
        need(p.native_accepted(positive['native']) and pair.warnings(positive['native'])==pair.warnings(native_original),'fresh positive Native failed; wrong-net control unexecuted')
        need(left()>=6,'conditional wrong-net control reserve unavailable')
        bad,control=wrong_net(sx.read(Path(positive['candidate'])));record['wrong_net_control']={'status':'running','qualified':False,**control};negative=validate('wrong-net',bad);record['wrong_net_control'].update(status='native_rejected' if not p.native_accepted(negative['native']) else 'unexpected_native_pass',candidate_sha256=negative['candidate_sha256'],native=negative['native'],report_sha256=negative['report_sha256'])
        need(not p.native_accepted(negative['native']) and negative['native']['opens']+negative['native']['blocking']>0 and negative['native']['exclusions']==0 and set(pair.warnings(native_original))<=set(pair.warnings(negative['native'])),'wrong-net Native control failed')
        record['wrong_net_control']['qualified']=True;record.update(status='completed',method_qualified=True);replay();completed=f.evidence_inventory(out);record['completed_material']=completed
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',method_qualified=False,initial_failure=type(exc).__name__+': '+str(exc),reason=type(exc).__name__+': '+str(exc))
    if completed is None:
        pc.inventory(out,max_bytes=LIMIT,max_files=6000,max_entries=12000);completed=f.evidence_inventory(out);record['completed_material']=completed
    return f.publish(out,record,stable,account,left,owned=lambda:h.owned_destination(owner),final_check=replay)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
    if not a.run_native:ap.error('explicit Native opt-in required')
    def stop(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
    d=experiment(a.output,a.protocol,a.protocol_sha256);print(json.dumps({k:d[k] for k in ('status','method_qualified','charged_wall_seconds','charged_full_cpu_seconds')}));raise SystemExit(0 if d['method_qualified'] else 2)
