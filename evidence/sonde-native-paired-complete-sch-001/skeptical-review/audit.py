"""Read-only actual Sonde consistency audit; no subprocess/native/Git calls."""
import copy,hashlib,json,signal,subprocess,sys,time
from pathlib import Path
from collections import Counter
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,strategy as s
from scripts import experiment_paired as paired,experiment_portfolio as portfolio
RUN=ROOT/'.runs/sonde-native-paired-complete-sch-001/run';OUTER=RUN.parent
start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('60-second read-only ceiling')));signal.alarm(60)
def read(path):return f.read_json(path)
def inventory(path):return pc.inventory(path,max_bytes=512*1024**2,max_files=16000,max_entries=32000)
def require(ok,message):
    if not ok:raise ValueError(message)
def forbidden(*a,**kw):raise AssertionError('subprocess/native/Git/network prohibited')
protocol=read(RUN/'protocol.json');prospective=read(ROOT/'.runs/sonde-native-paired-complete-sch-001-protocol.json');summary=read(RUN/'paired-summary.json');outer=read(OUTER/'execution.json');freeze=protocol['freeze'];tools=freeze['tools'];source=Path(protocol['source']);original=p.preflight(source);hashes=pc.inventory(source.parent);raw_before=inventory(RUN)
require(hashes==freeze['source_hashes']==prospective['original_source_sha256'],'source differs from both prospective freezes')
require(protocol['arm_order']==[r['id'] for r in summary['results']]==['B0','B1','B2_portfolio','C_feedback'],'four-arm population differs')
require(protocol['paired_system']=='native-all' and protocol['guidance_policy'] is None,'unexpected guidance/adapter comparison')
require(protocol['wall_budget_per_arm_seconds']==protocol['cpu_budget_per_arm_seconds']==120,'unequal declared budgets')
require(outer['git_head']==tools['git_head']==prospective['git_head'],'stored code identity differs')
require(summary['protocol_sha256']==p.sha(RUN/'protocol.json') and outer['prospective_protocol_sha256']==p.sha(ROOT/'.runs/sonde-native-paired-complete-sch-001-protocol.json'),'protocol bytes changed')
require(outer['wrapper_sha256']==prospective['wrapper_sha256']==p.sha(ROOT/'.runs/run-sonde-native-paired-complete-sch-001.py') and outer['log_sha256']==p.sha(OUTER/'command.log'),'outer code/log binding differs')
for n,v in freeze['files_sha256'].items():require(p.sha(ROOT/n)==p.sha(RUN/'frozen-code'/n)==v,'current/frozen implementation mismatch: '+n)
for n,v in tools['files'].items():require(p.sha(Path(n))==v,'actual pinned binary changed: '+n)
require(outer['process']['argv']==[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/experiment_paired.py'),'--project','sonde','--system','native-all','--output',str(RUN)],'outer dispatch differs')
require(outer['process']['status']=='success' and outer['process']['exit_code']==0 and outer['process']['cleanup_complete'] is True and outer['process']['log_truncated'] is False,'outer process incomplete/truncated')
require(prospective['audit_charge_seconds']==5,'missing prospectively charged final audit allowance')
rows=summary['results'];by={r['id']:r for r in rows};checks={};records={};native_rows=[]
with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
    checks['B1']=p.check_result(RUN/'B1/result.json');checks['C']=p.check_result(RUN/'C_feedback/result.json');checks['C_own_incumbent']=p.check_result(RUN/'C_feedback/incumbent/result.json')
    psum=read(RUN/'B2_portfolio/portfolio-summary.json');checks['B2']=paired.verify_portfolio(RUN/'B2_portfolio',psum,source,freeze)
    require([r['id'] for r in psum['trials']]==list(portfolio.VARIANTS) and all(r['eligible'] for r in psum['trials']),'portfolio omitted or suppressed an attempted variant')
    require(summary['status']=='completed' and summary['comparisons']==paired.comparisons(rows),'paired comparisons differ')
    for rel in ['B0','B1','B2_portfolio/01-via_default','B2_portfolio/02-via_low','B2_portfolio/03-via_high','C_feedback/incumbent','C_feedback']:
        folder=RUN/rel;data=read(folder/'result.json');records[rel]=data;candidate=Path(data['candidate'])
        require(data['source']==str(source) and data['source_hashes']==hashes and data['tools']==tools and pc.inventory(folder/'snapshot')==hashes,'receipt source/code/rule snapshot differs')
        pc.verify_candidate(candidate,hashes,data['candidate_sha256']);require(p.immutable(sx.read(candidate))==p.immutable(original),'original design changed')
        native=p.parse_report(folder/'final-drc.json',source.name);require(native==data['native'] and p.sha(folder/'final-drc.json')==data['native_report_sha256'],'final native report differs')
        require(data['schematic_parity']=='checked by final native DRC' and data['whole_project_drc_clean'] is False,'parity/warning disclosure differs')
        before={**hashes,source.name:data['candidate_sha256']};require(f.check_drc_stage(folder,data,'final-drc',candidate,folder/'final-drc-input'/source.name,False,before,schematic_parity=True,sandboxed=False)==native,'final parity/process/rules binding differs')
        p.check_resource_accounting(data);require(read(folder/'metrics.json')==data['metrics'],'native metrics differ')
        for step in data['steps']:
            process=read(Path(step['cwd'])/(step['name']+'-process.json'));require(all(step.get(k)==v for k,v in process.items()),'process/step differ')
            require(step['cleanup_complete'] is True and step['log_truncated'] is False and Path(step['log']).stat().st_size==step['log_bytes'],'native log/cleanup invalid')
        if rel!='C_feedback':
            task=f.g.task_from_source(original);imported=sx.read(folder/'imported.kicad_pcb');before_refill=p.transplant_routes(task,imported)
            source_native=f.check_drc_stage(folder,data,'source-drc',folder/'snapshot'/source.name,folder/'source-drc-input'/source.name,False,hashes,sandboxed=False)
            require(source_native==data['source_drc'],'original native source report differs')
            refill=folder/'refill'/source.name;before_refill_hash=hashlib.sha256((sx.dump(before_refill)+'\n').encode()).hexdigest()
            f.check_drc_stage(folder,data,'refill-drc',refill,refill,True,{**hashes,source.name:before_refill_hash},sandboxed=False)
            require((sx.dump(p.transplant_fill(before_refill,sx.read(refill)))+'\n').encode()==pc.read_bytes(candidate),'candidate task/import/refill reconstruction differs')
            if rel!='B0':p.check_minimum_width_record(data,folder)
        native_rows.append({'run':rel,'candidate_sha256':data['candidate_sha256'],'native_report_sha256':data['native_report_sha256'],'native_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'metrics':data['metrics'],'complete_native_parity':True,'finding_types':dict(Counter(x['type'] for x in native['findings']))})
    try:p.check_result(RUN/'B0/result.json')
    except p.Rejected as exc:checks['B0_expected_rejection']=str(exc)
    else:raise ValueError('invalid B0 admitted')
    cdata=records['C_feedback'];inc=records['C_feedback/incumbent'];best=Path(inc['candidate']);best_native=inc['native'];best_metrics=inc['metrics'];nets=s.zone_net_ids(original);trials=[];base_queue=[];base_mode=None
    require(cdata['incumbent']['receipt']==str(RUN/'C_feedback/incumbent/result.json') and cdata['incumbent_metrics']==best_metrics,'C does not bind own incumbent')
    require(cdata['zone_net_ids']==sorted(nets)==['13'] and inc['engine_profile']=='tuned' and inc['adapter']=='both' and inc['scoring_variant'] is None,'C engine/zone contract differs')
    for row in cdata['trials']:
        folder=RUN/'C_feedback/trials'/row['id'];trial=read(folder/'result.json');candidate=folder/'candidate'/source.name;prop=trial['proposal']
        require(trial['id']==row['id'] and trial['status']==row['status'] and trial['accepted']==row['accepted'] and trial['base_candidate_sha256']==p.sha(best),'trial/selected-parent binding differs')
        if prop['kind']=='native_warning_cleanup':
            parent=trials[-1];decision=s.feedback_proposal(sx.read(Path(parent['candidate'])),parent['proposal'],parent['native'],best_native,nets,[])
            decision.update(parent_trial=parent['id'],failed_candidate_sha256=parent['candidate_sha256'],native_report_sha256=parent['native_report_sha256'],base_candidate_sha256=parent['base_candidate_sha256'])
            if decision['proposed']:decision['proposal']['parent_trial']=parent['id']
            require(decision==read(Path(parent['candidate']).parent.parent/'feedback-decision.json') and prop==decision['proposal'],'feedback is not derived from actual rejected native warnings')
        else:
            mode=prop['kind']=='whole_zone_net'
            if base_mode!=mode:base_queue=s.proposals(sx.read(best),nets,[],mode);base_mode=mode
            available={s.route_id(x) for x in s.eligible_routes(sx.read(best),nets,[])}
            while base_queue and not set(base_queue[0]['route_ids'])<=available:base_queue.pop(0)
            require(base_queue and prop==base_queue.pop(0),'deterministic native-only proposal order differs')
        deleted=s.delete_routes(sx.read(best),prop['route_ids'],nets,[]);before={**hashes,source.name:hashlib.sha256((sx.dump(deleted)+'\n').encode()).hexdigest()};refill=folder/'refill'/source.name
        f.check_drc_stage(folder,trial,'refill-drc',refill,refill,True,before,sandboxed=False)
        rebuilt=p.transplant_fill(deleted,sx.read(refill));require((sx.dump(rebuilt)+'\n').encode()==pc.read_bytes(candidate),'trial differs from exact deletion+freshfill')
        pc.verify_candidate(candidate,hashes,trial['candidate_sha256']);before={**hashes,source.name:trial['candidate_sha256']}
        native=f.check_drc_stage(folder,trial,'final-drc',candidate,folder/'final-drc-input'/source.name,False,before,schematic_parity=True,sandboxed=False)
        require(native==trial['native'] and p.sha(folder/'final-drc.json')==trial['native_report_sha256'],'trial native/report differs')
        if trial['accepted']:
            require(trial['status']=='improvement_validated' and s._valid(native) and s._improves(trial['metrics'],best_metrics,native,best_native),'native rejected/quality-regressed trial admitted')
            require(read(folder/'metrics.json')==trial['metrics'],'trial metrics differ');best,best_native,best_metrics=candidate,native,trial['metrics']
        elif trial['status']=='quality_rejected':require(s._valid(native) and not s._improves(trial['metrics'],best_metrics,native,best_native),'quality rejection differs')
        else:require(trial['status']=='drc_rejected' and not s._valid(native),'unexplained trial failure')
        trials.append({**trial,'candidate':str(candidate)})
    require(len(trials)==9 and sum(t['accepted'] for t in trials)==cdata['improvements']==7,'C trial/improvement population differs')
    require(p.sha(best)==cdata['candidate_sha256'] and best_metrics==cdata['metrics'] and best_native==cdata['native'],'final candidate differs from last accepted validated parent')
    for n in cdata['checkpoints']:
        cp=read(RUN/'C_feedback'/n);candidate=Path(cp['candidate']);require(p.sha(candidate)==cp['candidate_sha256'] and all(cp[k]<=protocol['inner_allowance_seconds'] for k in ('elapsed_seconds','observed_cpu_seconds')),'stale/overbudget checkpoint')
    require(all(records[rel]['native']==records['B1']['native'] for rel in ['B2_portfolio/01-via_default','B2_portfolio/02-via_low','B2_portfolio/03-via_high','C_feedback/incumbent','C_feedback']),'warnings/native finding populations differ across valid arms')
# Complete enclosing invocation overhead is charged to each arm; ROOT owns
# the actual subsequent 5-second readback qualification, not this audit.
amendment_path=ROOT/'.runs/sonde-native-paired-complete-sch-002-qualification-protocol.json';amendment=read(amendment_path)
failedq=ROOT/'.runs/sonde-native-paired-complete-sch-001-qualification';newq=ROOT/'.runs/sonde-native-paired-complete-sch-002-qualification';failedq_result=read(failedq/'result.json');failedq_exec=read(failedq/'execution.json');newq_result=read(newq/'result.json');newq_exec=read(newq/'execution.json')
require(failedq_result['status']=='failed' and newq_result['status']=='completed' and newq_result['comparison_eligible'] is True,'failed/corrective qualification disposition differs')
require(amendment['native_rerun'] is False and amendment['prior_failed_audit_result_sha256']==p.sha(failedq/'result.json') and amendment['prior_failed_audit_execution_sha256']==p.sha(failedq/'execution.json'),'amendment omits/bypasses failed qualification')
require(newq_result['qualification_amendment_sha256']==p.sha(amendment_path) and newq_result['paired_summary_sha256']==p.sha(RUN/'paired-summary.json') and newq_result['outer_execution_sha256']==p.sha(OUTER/'execution.json'),'corrective result input binds differ')
for directory,execution in [(failedq,failedq_exec),(newq,newq_exec)]:
    require(execution['within_charged_allowance'] is True and max(execution['wall_seconds'],execution['full_cpu_seconds'])<=5 and execution['result_sha256']==p.sha(directory/'result.json'),'failed/corrective audit exceeds fixed charge')
qualification_charge=amendment['failed_prior_audit_fixed_charge_to_every_arm_wall_full_cpu_seconds']+amendment['new_audit_fixed_charge_to_every_arm_wall_full_cpu_seconds'];require(qualification_charge==10 and amendment['equal_wall_full_cpu_caps_unchanged']==120,'qualification changes acceptance cap')
full_shared_wall=outer['wall_seconds']-sum(r['invocation_wall_seconds'] for r in rows);full_shared_cpu=outer['full_cpu_seconds']-sum(r['invocation_cpu_seconds'] for r in rows)
require(full_shared_wall>=summary['shared_overhead_wall_seconds'] and full_shared_cpu>=summary['shared_overhead_cpu_seconds'],'outer accounting drops measured shared costs')
costs=[]
for row in rows:
    require(abs(row['charged_wall_seconds']-(row['invocation_wall_seconds']+summary['shared_overhead_wall_seconds']))<1e-6 and abs(row['charged_cpu_seconds']-(row['invocation_cpu_seconds']+summary['shared_overhead_cpu_seconds']))<1e-6,'paired inner charge algebra differs')
    costs.append({'id':row['id'],'invocation_wall_seconds':row['invocation_wall_seconds'],'invocation_cpu_seconds':row['invocation_cpu_seconds'],'full_outer_and_10_wall_seconds':row['invocation_wall_seconds']+full_shared_wall+qualification_charge,'full_outer_and_10_cpu_seconds':row['invocation_cpu_seconds']+full_shared_cpu+qualification_charge,'within120':max(row['invocation_wall_seconds']+full_shared_wall+qualification_charge,row['invocation_cpu_seconds']+full_shared_cpu+qualification_charge)<=120})
require(all(x['within120'] for x in costs),'full outer/prospective audit charge rejects an arm')
require(inventory(RUN)==raw_before and pc.inventory(source.parent)==hashes,'raw evidence/original changed during audit')
for n,v in freeze['files_sha256'].items():require(p.sha(ROOT/n)==v,'current helper changed during review')
report={'schema':1,'status':'passed_scoped_readonly_consistency','native_executions':0,'git_subprocesses':0,'network_requests':0,'review_seconds':time.monotonic()-start,'frozen_head':tools['git_head'],'run_files':len(raw_before),'run_bytes':sum((RUN/n).stat().st_size for n in raw_before),'run_inventory_sha256':hashlib.sha256(f.canonical(raw_before).encode()).hexdigest(),'source_sha256':hashes,'checks':checks,'native_final_candidates':native_rows,'C_trial_summary':{'trials':9,'improvements':7,'rejected_whole_zone_net_opens':4,'warning_regression_rejected':28,'warning_cleanup_retains26':True},'C_trial_evidence':[{'id':t['id'],'status':t['status'],'accepted':t['accepted'],'kind':t['proposal']['kind'],'deleted_routes':len(t['proposal']['route_ids']),'parent_sha256':t['base_candidate_sha256'],'candidate_sha256':t['candidate_sha256'],'native_report_sha256':t['native_report_sha256'],'native_counts':{k:t['native'][k] for k in ('opens','blocking','warnings','exclusions')},'metrics':t.get('metrics')} for t in trials],'full_outer':{'wall_seconds':outer['wall_seconds'],'full_cpu_seconds':outer['full_cpu_seconds'],'entire_shared_wall_seconds':full_shared_wall,'entire_shared_cpu_seconds':full_shared_cpu},'per_arm_full_outer_plus_failed5_corrective5_charge':costs,'comparisons':summary['comparisons'],'actual_acceptance_or_comparison_defects_found':[],'quality_gain_mm':{'beyond_B1':by['B1']['length_mm']-by['C_feedback']['length_mm'],'beyond_selected_B2':by['B2_portfolio']['selected']['length_mm']-by['C_feedback']['length_mm']},'root_qualification':{'failed_receipt_sha256':p.sha(failedq/'result.json'),'failed_execution':failedq_exec,'amendment_sha256':p.sha(amendment_path),'corrective_receipt_sha256':p.sha(newq/'result.json'),'corrective_execution':newq_exec,'conservative_fixed_wall_full_cpu_charge_to_every_arm':10},'remaining_gate':'No missing native/equal-budget gate found. This separately measured read-only skeptical review is not new solver/native work and is distinct from the already charged failed/corrective ROOT qualification.','limits':['No fresh native run or authenticity/human physical review.','All valid outputs retain26raw warnings:25footprint-symbol FPID differences and1J2library mismatch; no whole-project-clean or fully matching schematic claim.','No first-field exception used: native has only footprint_symbol_mismatch rather than footprint_symbol_field_mismatch; all original fields/FPIDs retained exact.','Exposed Sonde one-circuit result; independent pedigree/holdout/general superiority not established.','C costs more than B1/B2; no speedup claim.']}
p.save_json(HERE/'audit.json',report);print(f.canonical({'status':report['status'],'review_seconds':report['review_seconds'],'quality_gain_mm':report['quality_gain_mm'],'per_arm':costs}));signal.alarm(0)
