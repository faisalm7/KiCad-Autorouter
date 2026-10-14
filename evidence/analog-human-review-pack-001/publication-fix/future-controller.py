"""Prospective local pack preparation. No reviewer contact, solver or approval."""
from pathlib import Path
import argparse,json,secrets,sys,time,resource
START=time.monotonic()
def cpu():
    a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU_START=cpu()
ROOT=Path(__file__).absolute().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,review_export as ex
from autorouter.runner import run
from experiments.licensed_acquisition_v1 import fetch as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
HERE=ROOT/'.runs/analog-human-review-pack-draft-001';PROTOCOL_SHA='3c6ffb34650e3da7efa0eb26fa9e5fff910e0b76bc87056c9ebf6baf73b5f66f';SECONDS=900;LIMIT=1024**3

def main(output,prepare=False):
    raw=io.read_bytes(HERE/'PROTOCOL.json');protocol=json.loads(raw)
    if h.digest(raw)!=PROTOCOL_SHA:raise ValueError('frozen pack protocol changed')
    if prepare is not True:return {'status':'prospective_only','native_run':False,'human_review':False,'cases':3,'commands':protocol['commands_per_case']}
    closure=f.read_json(ROOT/'.runs/analog-high-cumulative-audit-closure-001/result.json')
    if closure.get('comparison_eligible') is not True or closure.get('cumulative_audit_closure_passed') is not True or protocol.get('source_identity_equal') is not True or protocol.get('same_scope') is not True:raise ValueError('matched group/whole-cost closure not qualified')
    started=START;cpu0=CPU_START;out=h.real_path(output,existing=False)
    if out.parent!=ROOT/'.runs' or not out.name.startswith('analog-human-review-pack-') or out.exists():raise ValueError('fresh checkout .runs pack required')
    out.mkdir();owner={};h.capture_destination(owner,out);steps=[];finished=[];captured={};complete=None
    record={'schema':1,'accepted':False,'status':'incomplete','pack_ready':False,'human_review_observed':False,'human_pcb_approval_observed':False,'physical_electrical_validation':False,'sharing_performed':False,'solver_jobs':0,'protocol_sha256':PROTOCOL_SHA,'steps':steps,'prepared_cases':finished,'limits':protocol['limits']}
    def remaining():return min(SECONDS-(time.monotonic()-started),SECONDS-(h.cpu_seconds()-cpu0))
    def witness():return io.inventory(out,max_bytes=LIMIT,max_files=24000,max_entries=48000,with_directories=True)
    def stable():
        h.owned_destination(owner)
        if remaining()<=0:raise ValueError('whole pack wall/fullCPU budget exhausted')
        if p.sha(HERE/'PROTOCOL.json')!=PROTOCOL_SHA or any(p.sha(ROOT/n)!=v for n,v in protocol['runtime_sha256'].items()):raise ValueError('pack runtime/protocol changed')
        if any(p.sha(ROOT/n)!=v for n,v in protocol['evidence_index'].items()):raise ValueError('custodian evidence changed')
        for row in protocol['cases']:
            if p.sha(ROOT/row['receipt'])!=row['receipt_sha256']:raise ValueError('routing receipt changed')
        for path,hashes in captured.items():
            if io.inventory(path)!=hashes:raise ValueError('delivered project changed')
        if complete is not None:
            files,dirs=witness();files={n:v for n,v in files.items() if n not in {'result.json','result.json.partial'} and not n.startswith(('invalidated-result-','interrupted-result-'))}
            if (files,dirs)!=complete:raise ValueError('completed pack evidence changed')
    def account():
        wall=time.monotonic()-started;cpu=h.cpu_seconds()-cpu0
        record.update(wall_seconds=wall,total_cpu_seconds=cpu,output_bytes=sum((out/n).stat().st_size for n in witness()[0]),within_budget=wall<=SECONDS and cpu<=SECONDS,retained_publication_artifacts={n:v for n,v in witness()[0].items() if n.startswith(('invalidated-result-','interrupted-result-'))})
        if record.get('status')!='local_pack_prepared':record['pack_ready']=False
        if not record['within_budget']:record.update(status='rejected',pack_ready=False)
    def save(path,value):p.save_json(path,value)
    def command(name,args,seconds):
        bootstrap='import sys;sys.path.insert(0,sys.argv.pop(1));from autorouter.__main__ import main;raise SystemExit(main())'
        stable();step=run([str(ROOT/'.venv/bin/python'),'-B','-c',bootstrap,str(ROOT),*map(str,args)],cwd=custodian,log=custodian/(name+'.log'),timeout=min(seconds,remaining()),max_log_bytes=262144,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        steps.append({'name':name,**step});save(custodian/(name+'-process.json'),step)
        if step['status']!='success' or step['exit_code']!=0 or step.get('cleanup_complete') is not True:raise ValueError('pack command failed: '+name)
        stable()
    custodian=out/'custodian';custodian.mkdir();pack=out/'reviewer-pack';pack.mkdir();cases=pack/'cases';cases.mkdir();forms=pack/'forms';forms.mkdir()
    ids=[secrets.token_hex(8) for _ in protocol['cases']]
    if len(set(ids))!=3:raise ValueError('opaque case collision')
    draw=list(zip(ids,protocol['cases']));secrets.SystemRandom().shuffle(draw)
    mapping={'order':[id for id,_ in draw],'draw_source':'secrets.token_hex + SystemRandom shuffle','source_protocol_sha256':PROTOCOL_SHA,'cases':{},'human_review':None,'selection_exposure':protocol['selection_exposure'],'all_C_exploration_compute':protocol['exploration_cost'],'primary_group':protocol['primary_group']}
    try:
        save(custodian/'protocol.json',protocol)
        save(custodian/'full-evidence-index.json',{'pinned':protocol['evidence_index'],'source_cohort_size':6,'all_source_leads_retained':True,'diagnostic_roots':['.runs/analog-high-incumbent-pruning-001','.runs/analog-high-incumbent-pruning-002/run/trials','.runs/analog-filter-native-paired-complete-sch-001/run'], 'meaning':'Rejected thermal/extra-warning/timeout trials, B0 and failed audits remain outside primary cases; original evidence untouched.'})
        for index,(id,row) in enumerate(draw):
            base=custodian/id;base.mkdir();receipt=ROOT/row['receipt'];report=f.read_json(receipt)
            if report['candidate_sha256']!=row['candidate_sha256'] or report['native_report_sha256']!=row['native_report_sha256'] or report['source_hashes']!=row['source_hashes'] or report['scope']!=row['scope']:raise ValueError('selected case lineage changed')
            command(id+'-copy',['review-copy',receipt,'--output',base/'review',*(['--render'] if row['arm']=='C_feedback' else [])],30)
            command(id+'-intent',['review-choice',base/'review/review.json','--choice','accept','--output',base/'intent'],30)
            command(id+'-export',['review-export',base/'intent/choice.json','--output',base/'export','--seconds','120'],120)
            command(id+'-check',['review-export-check',base/'export/export.json'],120)
            checked=ex.check_export(base/'export/export.json');export=f.read_json(base/'export/export.json')
            if checked.get('current') is not True or export['native']!=row['expected_native'] or export['metrics']['copper_layers']!=4 or export['source_hashes']!=row['source_hashes']:raise ValueError('fresh export differs from declared native constraints/findings')
            project=Path(export['candidate']).parent;content=io.inventory(project,contents=True);hashes=io.inventory(project)
            case=cases/id;case.mkdir();case_owner={};h.capture_destination(case_owner,case)
            delivered=case/'project';copy_bytes(content,delivered,expected_parent_owner=case_owner)
            if io.inventory(delivered)!=hashes or p.sha(delivered/'analog_filter_module.kicad_pcb')!=export['candidate_sha256']:raise ValueError('delivered bytes differ from freshly validated export')
            captured[str(delivered)]=hashes
            native=f.read_json(base/'export/validation/final-drc.json')
            view={k:native[k] for k in ('$schema','kicad_version','coordinate_units','included_severities','ignored_checks','violations','unconnected_items','schematic_parity') if k in native}
            view.update(source='analog_filter_module.kicad_pcb',native_summary=export['native'],status='native routing accepted with 14 inherited library warnings; whole project not clean')
            save(case/'native-findings.json',view)
            (case/'constraints.md').write_text('Matched four-copper-layer project; original placement, pads, nets, stackup, outline, zones/protected copper/rules and all severity settings preserved. Complete schematic parity checked on these delivered bytes. All14 library warnings and ignored checks remain visible. Electrical/model requirements and physical adequacy unqualified. Review/cleanup findings and timing are not measured.\n')
            save(forms/(id+'.json'),{'case_id':id,'reviewer_id':None,'experience':None,'prior_exposure':None,'findings':None,'inspection_start_utc':None,'inspection_end_utc':None,'active_cleanup_seconds':None,'endpoint_reached':None,'censored':None,'method_guess':None,'pairwise_preference':None,'human_pcb_approval':None,'edited_output_sha256':None})
            mapping['cases'][id]={'arm':row['arm'],'routing_receipt':str(receipt),'input':row,'export_receipt':str(base/'export/export.json'),'export_receipt_sha256':p.sha(base/'export/export.json'),'fresh_native_report_sha256':export['native_report_sha256'],'delivered_project_hashes':hashes,'export_sha_changed_after_refill':export['final_sha_changed_after_refill']}
            finished.append(id);save(custodian/'mapping.json',mapping);stable()
        (pack/'instructions.md').write_text('Local development review inputs only; no human PCB approval or physical validation. Start each opaque case independently. Keep original inputs byte-exact and use a separate working copy. Preserve original rules; inspect every warning and missing electrical requirement. Forms are blank until an actual approved reviewer works. Cleanup cap30 active minutes per case, record elapsed/tool-wait/break time and censoring. No comparative human-speed claim from exposed sequential siblings. No reviewer contact/share or spending has been authorized.\n')
        save(pack/'presentation-order.json',{'order':mapping['order'],'reviewer_id':None,'actual_order_used':None})
        stable();files,dirs=witness();complete=({n:v for n,v in files.items() if n not in {'result.json','result.json.partial'} and not n.startswith(('invalidated-result-','interrupted-result-'))},dirs);record.update(status='local_pack_prepared',pack_ready=True,delivery_project_hashes=captured,blinding_audit='Custodian labels/logs/exports withheld; native geometry/metadata may still permit identity guesses. No reviewer/independence or perfect blindness claim.',native_validation_performed=True)
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'rejected',pack_ready=False,first_failure=type(exc).__name__+': '+str(exc))
    f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner))
    try:
        stable();published=f.read_json(out/'result.json');account();stable()
        if published.get('pack_ready') is True and (record.get('pack_ready') is not True or record.get('within_budget') is not True or remaining()<=0):raise ValueError('final pack budget changed after publication')
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='rejected',pack_ready=False,final_failure=type(exc).__name__+': '+str(exc))
        f.publish(out,record,lambda:(_ for _ in ()).throw(ValueError(record['final_failure'])),account,remaining,owned=lambda:h.owned_destination(owner))
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--output',default=str(ROOT/'.runs/analog-human-review-pack-001'));args=parser.parse_args()
    with shared.cancellation(),shared.alarm(900):result=main(args.output,args.prepare)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result.get('status') in {'prospective_only','local_pack_prepared'} else 2)
