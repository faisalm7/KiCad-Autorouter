"""Unexecuted short-only005: reuse exact004 positive; fresh cross-net pad bridge."""
import time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
from types import SimpleNamespace
import argparse,copy,json,math,signal,sys,uuid
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,board_floor as g,placement_clearance as pc,handoff as h,routing_scope as rs,local_settings,thermal_geometry as geom
from experiments.native_connected_pair_v1 import driver as pair
from experiments.native_contact_continuation_v1.actor import inventory,need
from experiments.placement_handoff_native_v1.driver import copy_bytes
FOUR=ROOT/'.runs/nus-selected-proposal-native120-004';OUTER4=ROOT/'.runs/nus-selected-proposal-native120-004-execution';LEAD4=ROOT/'.runs/nus-selected-proposal-native120-004-lead-execution'
THREE=ROOT/'.runs/nus-native-feedback-engine120-003';TWO=ROOT/'.runs/nus-native-connected-contact120-002';AUDIT=ROOT/'.runs/selected-proposal004-native-review-preserved-001'
POLICY='selected-proposal-physical-short-only-v1';IMPORT_POLICY='selected-proposals-exact-source-v1';PIPELINE='6906c41030c4629d8cc2e7c01f3c8ef1f520f0e4c04ad7b8eaf0add7d8ff5f56';BOOT=1;LIMIT=64*1024**2
PAD1='119b2026-aa38-440c-a63f-25f6c8d5cc5a';PAD2='49eb34da-07bc-445a-94b9-294a59288a75';POINTS=[[157875000,90170000],[159625000,90170000]]

def netmap(tree):
    _,resolve=g.source_net_identity(tree);result={}
    for route in p.routes(tree):
        identity=sx.unquote(sx.one(route,'uuid')[1]);need(identity not in result,'duplicate retained route UUID');result[identity]=resolve(sx.one(route,'net'))
    return result

def control_id(candidate_sha):return str(uuid.uuid5(uuid.NAMESPACE_URL,'selected-proposal005-cross-net-pad-short/'+candidate_sha))

def fault_bindings(native,identity):
    result=[]
    for finding in native['findings']:
        if finding['severity']!='error' or finding['type'] not in {'shorting_items','clearance','tracks_crossing'}:continue
        identities=sorted({item['uuid'] for item in finding.get('items',[]) if isinstance(item,dict) and isinstance(item.get('uuid'),str) and item['uuid']})
        if identities and not {identity,PAD2}.intersection(identities):continue
        result.append({'type':finding['type'],'binding':'report_uuid' if identities else 'exact_geometric_bridge_report_has_no_uuids','item_uuids':identities})
    return result

def invalid(native,baseline,identity):
    return native['opens']+native['blocking']>0 and native['exclusions']==0 and set(pair.warnings(baseline))<=set(pair.warnings(native)) and bool(fault_bindings(native,identity))

def check_outer_witness(out,data,spec,protocol_sha):
    identity={'schema':1,'kind':POLICY,'status':'completed','accepted':False,'production_admitted':False,'method_qualified':True,'budget_seconds':120,'cpu_budget_seconds':120,'bootstrap_allowance_seconds':BOOT,'protocol_sha256':protocol_sha}
    need(all(type(data.get(k)) is type(v) and data[k]==v for k,v in identity.items()),'short-only identity differs')
    need(f.canonical(data['prior_costs'])==f.canonical(spec['prior_costs']) and data['within_budget'] is True and data['short_control']['qualified'] is True,'short-only prior/control differs')
    for key,charged,prior in [('new_wall_seconds','charged_wall_seconds','wall_seconds'),('new_full_cpu_seconds','charged_full_cpu_seconds','full_cpu_seconds')]:
        value=data[key];need(type(value) in (int,float) and math.isfinite(value) and value>=0 and data[charged]==spec['prior_costs'][prior]+BOOT+value and data[charged]<120,'short-only cumulative algebra differs')
    need(p.native_accepted(data['native']) and invalid(data['short_control']['native'],data['original_native'],control_id(spec['positive_candidate_sha256'])) and data['short_control']['native_fault_bindings']==fault_bindings(data['short_control']['native'],control_id(spec['positive_candidate_sha256'])) and data['candidate_sha256']==spec['positive_candidate_sha256'],'positive/short Native result differs')
    need(f.evidence_inventory(out)==data['completed_material'] and p.tool_manifest()==data['tools'] and p.tree_hash(Path(spec['source']).parent)==spec['source_hashes'],'completed/current short-only material differs')
    for group in ('code_sha256','retained_files'):
        for name,pin in spec[group].items():need(p.sha(ROOT/name)==pin,'frozen file changed: '+name)
    for name,pin in spec['prefixes'].items():need(inventory(ROOT/name)==pin,'retained prefix changed: '+name)

def experiment(out,protocol,protocol_sha):
    need(Path(__file__).parent==ROOT/'experiments/physical_short_continuation_v1','promote/review/checkpoint before Native')
    need(out.parent==ROOT/'.runs' and not out.exists() and not out.is_symlink(),'fresh direct output required')
    need(p.sha(protocol)==protocol_sha,'prospective protocol differs');spec=f.read_json(protocol)
    need(spec['status']=='prospectively_frozen' and spec['policy']==POLICY and spec['actor_sha256']==p.sha(__file__) and spec['bootstrap_allowance_seconds']==BOOT and spec['cumulative_wall_full_cpu_seconds']==120 and spec['pipeline_sha256']==PIPELINE==p.tool_manifest()['implementation_sha256']['autorouter/pipeline.py'],'unfrozen short-only code/policy')
    need(all(not Path(n).is_absolute() and '..' not in Path(n).parts for group in ('code_sha256','retained_files','prefixes') for n in spec[group]),'project-relative frozen paths required')
    old=f.read_json(FOUR/'result.json');outer=f.read_json(OUTER4/'result.json');lead=f.read_json(LEAD4/'execution.json');previous=f.read_json(FOUR/'prospective-pins.json');two=f.read_json(TWO/'result.json')
    audit=f.read_json(AUDIT/'result-corrected.json');execution=f.read_json(AUDIT/'execution-corrected.json');first=f.read_json(AUDIT/'execution.json');prior=spec['prior_costs'];charged=[prior['wall_seconds'],prior['full_cpu_seconds']];costs=execution['both_actual_reader_costs']
    need(audit['passed'] is True and audit['source_result_sha256']==p.sha(FOUR/'result.json') and execution['result_sha256']==p.sha(AUDIT/'result-corrected.json') and execution['previous_reader_execution_sha256']==p.sha(AUDIT/'execution.json') and execution['both_startup_allowances_seconds']==4,'actual004 corrected/failed reader lineage differs')
    need(all(type(costs[k]) in (int,float) and math.isfinite(costs[k]) and costs[k]>=0 and abs(costs[k]-execution['whole_reader_execution_cost'][k]-first['whole_reader_execution_cost'][k])<1e-12 for k in ('wall_seconds','full_cpu_seconds')),'both actual reader costs differ')
    minimum=[max(old['charged_wall_seconds'],outer['charged_wall_seconds'],lead['charged_wall_seconds'])+costs['wall_seconds']+4,max(old['charged_full_cpu_seconds'],outer['charged_full_cpu_seconds'],lead['charged_full_cpu_seconds'])+costs['full_cpu_seconds']+4]
    need(all(type(value) in (int,float) and math.isfinite(value) and bound<=value<119 for value,bound in zip(charged,minimum)),'prior omitted failed001002003004/bothreader costs')
    for row in (outer,lead):need(row['process']['status']=='nonzero_exit' and row['process']['exit_code']==2 and row['process']['cleanup_complete'] is True,'004 outer did not cleanly reject')
    need(lead['source_current'] is True and old['status']=='failed' and old['accepted'] is old['method_qualified'] is old['production_admitted'] is False and old['reason']==old['initial_failure']=='Rejected: wrong-net Native control failed' and old['wrong_net_control']['status']=='unexpected_native_pass' and old['wrong_net_control']['qualified'] is False,'actual004 failure must remain unchanged')
    source=Path(spec['source']);hashes=spec['source_hashes'];original=p.preflight(source);tools=p.tool_manifest();base=FOUR/'positive';candidate=base/'candidate'/source.name;warm=THREE/'warm-source'/source.name;warm_tree=sx.read(warm);task=rs.task(warm_tree,['GND']);protected=rs.protected_routes(warm_tree,['GND']);all_positive=p.routes(sx.read(candidate))
    need(old['source']==str(source) and old['source_hashes']==hashes and len(hashes)==8 and {k:v for k,v in old['tools'].items() if k!='git_head'}=={k:v for k,v in tools.items() if k!='git_head'} and tools['implementation_sha256']['autorouter/pipeline.py']==PIPELINE,'only current HEAD may differ from004; core/tool bytes exact')
    required=set(previous['prefixes'])|{str(x.relative_to(ROOT)) for x in (FOUR,OUTER4,LEAD4,AUDIT)}
    need(required<=set(spec['prefixes']) and set(previous['code_sha256'])|set(tools['implementation_sha256'])|{'experiments/physical_short_continuation_v1/actor.py','experiments/physical_short_continuation_v1/run.py'}<=set(spec['code_sha256']),'prior/current whole closure missing')
    need(p.sha(candidate)==old['candidate_sha256']==spec['positive_candidate_sha256'] and p.sha(base/'final-drc.json')==old['native_report_sha256']==spec['positive_report_sha256'],'fixed positive/report differs')
    out.mkdir();owner={};h.capture_destination(owner,out);copy_bytes(pc.inventory(source.parent,contents=True),out/'original',expected_parent_owner=owner)
    copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},out/'code',expected_parent_owner=owner);copy_bytes({n:pc.read_bytes(ROOT/n) for n in spec['code_sha256'] if n not in tools['implementation_sha256']},out/'helper-code',expected_parent_owner=owner)
    p.save_json(out/'prospective-pins.json',spec);job=None;entry=None;completed=None;left=lambda:min(120-charged[0]-BOOT-(time.monotonic()-START),120-charged[1]-BOOT-(cpu()-CPU0))
    record=dict(schema=1,kind=POLICY,status='incomplete',accepted=False,production_admitted=False,method_qualified=False,budget_seconds=120,cpu_budget_seconds=120,bootstrap_allowance_seconds=BOOT,protocol_sha256=protocol_sha,prior_costs=prior,source=str(source),source_hashes=hashes,tools=tools,retained_stage_tools=old['tools'],candidate=str(candidate),candidate_sha256=old['candidate_sha256'],native=old['native'],native_report_sha256=old['native_report_sha256'],metrics=old['metrics'],metrics_sha256=old['metrics_sha256'],positive_reused_from=str(FOUR/'result.json'),positive_receipt_sha256=p.sha(FOUR/'result.json'),original_native=old['original_native'],original_native_report_sha256=old['original_native_report_sha256'],prior_minimum_wall_seconds=minimum[0],prior_minimum_full_cpu_seconds=minimum[1],short_control={'qualified':False,'status':'not_run'},steps=[],scope='Only missing physical-short negative Native stages; retained004positive/fullSCH/metrics/policy and all earlier failures/costs remain exact. No classifier/engine/export/import/baseline/positive/geometry rerun, normal routing admission, independentcomparison or physical/electrical claim.')
    def stable():
        h.owned_destination(owner);need(left()>0,'cumulative120 exhausted')
        need(p.sha(protocol)==protocol_sha and p.tool_manifest()==tools and p.tree_hash(source.parent)==p.tree_hash(out/'original')==hashes,'source/protocol/runtime changed')
        need(p.tree_hash(out/'code')=={Path(n).name:pin for n,pin in tools['implementation_sha256'].items()} and p.tree_hash(out/'helper-code')=={n:pin for n,pin in spec['code_sha256'].items() if n not in tools['implementation_sha256']},'captured current code differs')
        for group in ('code_sha256','retained_files'):
            for name,pin in spec[group].items():need(p.sha(ROOT/name)==pin,'frozen file changed: '+name)
        for name,pin in spec['prefixes'].items():need(inventory(ROOT/name)==pin,'retained prefix changed: '+name)
        pc.inventory(out,max_bytes=LIMIT,max_files=6000,max_entries=12000)
        if completed is not None:need(f.evidence_inventory(out)==completed,'new short attempt material changed')
    def phase(directory,steps):
        path=directory/'candidate'/source.name;saved=f.check_drc_stage(directory,{'steps':steps},'refill-drc',directory/'refill'/source.name,directory/'refill'/source.name,True,{**hashes,source.name:p.sha(directory/'pre-refill.kicad_pcb')})
        native=f.check_drc_stage(directory,{'steps':steps},'final-drc',path,directory/'final-drc-input'/source.name,False,{**hashes,source.name:p.sha(path)},schematic_parity=True)
        value={'job':SimpleNamespace(out=directory,steps=steps),'candidate':str(path),'candidate_sha256':p.sha(path),'native':native,'saved_native':saved,'report_sha256':p.sha(directory/'final-drc.json')};pair._contact_phase_readback(value,original,hashes)
        p.check_pour_evidence(directory,{'steps':steps},original,path,source_hashes=hashes,correction=False,sandboxed=True);p.check_legacy_zone_evidence(directory,original,path,implementation=tools['implementation_sha256']);local_settings.check_normal_policy(directory,{'tools':old['tools'] if directory in (base,FOUR/'wrong-net') else tools,'source_hashes':hashes,'steps':steps});return value
    def retained():
        need(f.evidence_inventory(FOUR)==old['completed_material'] and p.tree_hash(FOUR/'original')==hashes and p.tree_hash(base/'snapshot')==hashes and p.tree_hash(FOUR/'code')=={Path(n).name:pin for n,pin in tools['implementation_sha256'].items()},'retained004 original/captured material changed')
        prepared=FOUR/'prepared.kicad_pcb';proof=f.read_json(FOUR/'selected-proposals.json');need(proof==old['protected_route_import'] and proof['policy']==IMPORT_POLICY==p.SELECTED_PROPOSAL_IMPORT_POLICY and p.sha(prepared)==old['prepared_sha256'],'mandatory retained selected proof differs')
        p.check_protected_import(FOUR,{'scope':'selected_nets','protected_route_import':proof},task,prepared,protected,expected_policy=IMPORT_POLICY,selected_names=['GND'])
        need(len(protected)==22 and len(proof['selected_proposals'])==18 and len(all_positive)==40 and rs.audit(warm_tree,sx.read(candidate),['GND'])==old['protected_signal_audit'] and p.routes(sx.read(prepared))==all_positive,'exact22 signal/18GND preservation differs')
        baseline=f.check_drc_stage(TWO/'whole-validation',{'steps':two['steps']},'pristine-original',TWO/'whole-validation/snapshot'/source.name,TWO/'whole-validation/pristine-original-input'/source.name,False,hashes,schematic_parity=True)
        positive=phase(base,[step for step in old['steps'] if step['cwd']==str(base)]);need(positive['native']==old['native'] and baseline==old['original_native'] and p.native_accepted(positive['native']) and p.native_accepted(baseline) and baseline['warnings']==10 and pair.warnings(positive['native'])==pair.warnings(baseline),'retained positive/fullSCH baseline differs')
        need(netmap(sx.read(base/'pre-refill.kicad_pcb'))==netmap(sx.read(base/'refill'/source.name))==netmap(sx.read(candidate)),'retained positive semantic route nets normalized')
        f.process_check(base,{'steps':old['steps']},'metrics',[*f.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(base/'metrics.json')]);need(f.read_json(base/'metrics.json')==old['metrics'] and p.sha(base/'metrics.json')==old['metrics_sha256'],'retained positive metrics changed')
        directory=FOUR/'wrong-net';bad=phase(directory,[step for step in old['steps'] if step['cwd']==str(directory)]);need(bad['native']==old['wrong_net_control']['native'] and p.native_accepted(bad['native']),'failed004 control actual Native pass changed')
        repair=TWO/'whole-validation/contact-repair';scene=f.read_json(repair/'geometry.json');request=f.read_json(repair/'request.json');scene_board=TWO/'whole-validation/candidate'/source.name
        need(scene['native_version']=='10.0.0' and scene['status']=='observations_complete' and scene['api_error_count']==0 and scene['source_unchanged'] is True and scene['board_saved'] is False and scene['board_sha256']==p.sha(scene_board) and p.immutable(sx.read(scene_board))==p.immutable(original) and request['candidate_files']==p.tree_hash(repair/'input'),'retained Native pad geometry/source differs')
        f.process_check(repair,{'steps':two['steps']},'thermal-geometry',[*f.SANDBOX,str(p.c.PYTHON),'-B',str(repair/'worker.py'),str(repair/'input'/source.name),str(repair/'request.json'),str(repair/'geometry.json')])
        owners=geom.uuid_index(original,sx);_,resolve=g.source_net_identity(original);rows=[]
        for identity,point,name in zip((PAD1,PAD2),POINTS,('GND','Net-(D1-A)')):
            pads=[pad for pad in scene['pads'] if pad['uuid']==identity];need(len(pads)==1 and len(owners.get(identity,[]))==1,'unique fixed D1 pad');pad=pads[0];layers=[row for row in pad['layers'] if row['canonical']=='F.Cu']
            need(resolve(sx.one(owners[identity][0],'net'))==pad['net_name']==name and pad['position_nm']==point and pad['is_pth'] is False and pad['drill_size_nm']==[0,0] and len(layers)==1 and layers[0]['on_layer'] is True and layers[0]['flash_layer'] is True and layers[0]['shape_is_roundrect'] is True and layers[0]['shape_position_nm']==point and layers[0]['offset_nm']==[0,0] and layers[0]['size_nm']==[1050000,950000],'exact fixed D1 F.Cu interior/net differs');rows.append({'uuid':identity,'net_name':name,'position_nm':point,'size_nm':layers[0]['size_nm']})
        need(resolve(['net','1'])=='GND','original numeric GND code changed');return baseline,rows
    def short_tree():
        tree=sx.read(candidate);identity=control_id(spec['positive_candidate_sha256']);need(identity not in geom.uuid_index(tree,sx),'control UUID collides')
        node=sx.parse('(segment (start 157.875 90.17) (end 159.625 90.17) (width 0.5) (layer "F.Cu") (net 1) (uuid "'+identity+'"))');tree.append(node)
        need(p.routes(tree)==all_positive+[node] and p.immutable(tree)==p.immutable(original),'short added more than the one route');return tree,node
    def replay():
        stable();baseline,pads=retained()
        if entry is not None and 'candidate_sha256' in entry:
            actual=phase(job.out,job.steps);expected,node=short_tree();need(p.routes(sx.read(Path(actual['candidate'])))==p.routes(expected) and actual['candidate_sha256']==entry['candidate_sha256'] and actual['native']==entry['native'] and actual['report_sha256']==entry['report_sha256'],'fresh short/control replay differs')
            need(record['short_control']['native']==actual['native'] and record['short_control']['report_sha256']==actual['report_sha256'] and record['short_control']['candidate_sha256']==actual['candidate_sha256'] and record['short_control']['added_route']==node and record['fixed_pad_evidence']==pads and record['short_control']['native_fault_bindings']==fault_bindings(actual['native'],control_id(spec['positive_candidate_sha256'])),'short receipt/proof differs')
            if record['method_qualified']:need(record['short_control']['qualified'] is True and invalid(actual['native'],baseline,control_id(spec['positive_candidate_sha256'])),'fresh Native short rejection missing')
    def account():
        wall,full=time.monotonic()-START,cpu()-CPU0;record.update(new_wall_seconds=wall,new_full_cpu_seconds=full,charged_wall_seconds=charged[0]+BOOT+wall,charged_full_cpu_seconds=charged[1]+BOOT+full,within_budget=left()>0,steps=[] if job is None else job.steps,cumulative_active002_reader_and_short_wall_seconds=27.294584+charged[0]+BOOT+wall,cumulative_active002_reader_and_short_full_cpu_seconds=22.430367+charged[1]+BOOT+full)
        if record['status']!='completed' or not record['within_budget']:record['method_qualified']=False
    try:
        stable();baseline,pads=retained();need(left()>=6,'insufficient remaining cumulative budget for only missing short control');tree,node=short_tree();record.update(fixed_pad_evidence=pads,short_control={'status':'running','qualified':False,'added_route':node})
        job=f.FloorJob(out/'physical-short',left(),left,protect_local_settings=True);copy_bytes(pc.inventory(source.parent,contents=True),job.out/'snapshot');copy_bytes({Path(n).name:pc.read_bytes(ROOT/n) for n in tools['implementation_sha256']},job.out/'code')
        files=pc.inventory(source.parent,contents=True);files[source.name]=(sx.dump(tree)+'\n').encode();copy_bytes(files,job.out/'candidate');path=job.out/'candidate'/source.name;(job.out/'pre-refill.kicad_pcb').write_bytes(files[source.name]);entry={'candidate':str(path)}
        digest,native=p.validate_candidate(job,original,path,hashes,all_positive,schematic_parity=True);entry.update(candidate_sha256=digest,native=native,report_sha256=p.sha(job.out/'final-drc.json'));phase(job.out,job.steps)
        record['short_control'].update(status='native_rejected' if not p.native_accepted(native) else 'unexpected_native_pass',candidate_sha256=digest,native=native,report_sha256=entry['report_sha256'],native_fault_bindings=fault_bindings(native,control_id(spec['positive_candidate_sha256'])));need(invalid(native,baseline,control_id(spec['positive_candidate_sha256'])),'physical-short control lacks a bound Native cross-net error, original warnings or zero exclusions')
        record['short_control']['qualified']=True;record.update(status='completed',method_qualified=True);replay()
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',method_qualified=False,initial_failure=type(exc).__name__+': '+str(exc),reason=type(exc).__name__+': '+str(exc))
    pc.inventory(out,max_bytes=LIMIT,max_files=6000,max_entries=12000);completed=f.evidence_inventory(out);record['completed_material']=completed
    return f.publish(out,record,stable,account,left,owned=lambda:h.owned_destination(owner),final_check=replay)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
    if not a.run_native:ap.error('explicit Native opt-in required')
    def stop(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
    d=experiment(a.output,a.protocol,a.protocol_sha256);print(json.dumps({k:d[k] for k in ('status','method_qualified','charged_wall_seconds','charged_full_cpu_seconds')}));raise SystemExit(0 if d['method_qualified'] else 2)
