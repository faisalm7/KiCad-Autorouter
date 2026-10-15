"""Pure one-shot IR-workflow001 proof check; never calls create/choice/export/render."""
from pathlib import Path
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
import sys,json
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,review_export as e,review_view as view,local_settings as ls,config as c
CAP=60.
BASE=ROOT/'.runs/review-export-native-ir-chains-001'
OUTER=ROOT/'.runs/ir-chains-review-export-execution-001'
OUTPUT=ROOT/'.runs/ir-chains-workflow001-readback-001'
RECEIPT=ROOT/'.runs/ir-chain-fivearm-001/C_chains/result.json'


def require(value,why):
    if not value:raise p.Rejected(why)


def check():
    result=f.read_json(BASE/'result.json');outer=f.read_json(OUTER/'execution.json')
    require(result['status']=='completed' and result['controls_passed'] is True and result['accepted'] is False
        and result['new_routing_executed'] is False and result['human_pcb_approval_observed'] is False
        and result['live_application_qualified'] is False and result['within_budget'] is True,'IR-workflow001 did not complete honestly')
    process=outer['process'];require(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
        and process['log_truncated'] is False and outer['source_current'] is True,'outer IR-workflow001 failed')
    expected=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/qualify_review_export.py'),
        '--receipt',str(RECEIPT),'--render','--output',str(BASE),'--run-native']
    require(process['argv']==expected and process['cwd']==str(OUTER) and process['log']==str(OUTER/'command.log'),'outer command identity differs')
    require(result['tools']==outer['tools'] and result['controller_sha256']==outer['controller_sha256']==p.sha(ROOT/'scripts/qualify_review_export.py'),'workflow producer binding differs')
    require(len(result['cases'])==len(result['protocol_cases'])==1,'not the one selected IR workflow')
    case=result['cases'][0];pin=result['protocol_cases'][0];folder=BASE/'retained'
    require(case['name']==pin['name']=='retained' and case['passed'] is True and pin['render'] is True and pin['schema']==1
        and pin['receipt']==str(RECEIPT) and pin['receipt_sha256']==p.sha(RECEIPT),'retained routing receipt differs')
    route=f.read_json(RECEIPT);review=f.read_json(folder/'review/review.json');accepted=f.read_json(folder/'intent/choice.json');rejected=f.read_json(folder/'rejection/choice.json');exported=f.read_json(folder/'export/export.json')
    witnesses={str(path):e.witness(path) for path in (BASE,OUTER,RECEIPT.parent,Path(route['source']).parent)}
    filepins={str(path):p.sha(path) for path in (Path(__file__),BASE/'result.json',BASE/'protocol.json',OUTER/'execution.json',RECEIPT)}
    runtime=p.tool_manifest();require(all(runtime[k]==v for k,v in outer['tools'].items() if k!='git_head'),'current helper/native bytes differ')
    OUTPUT.mkdir();owner={};h.capture_destination(owner,OUTPUT)
    record=dict(schema=1,kind='pure-IR-IR-workflow001-readback',accepted=False,status='incomplete',controls_passed=False,
        new_native_execution=False,new_engine_execution=False,prior_workflows_replayed=False,
        human_pcb_approval_observed=False,live_application_qualified=False,reader_sha256=p.sha(Path(__file__)),
        workflow_result_sha256=p.sha(BASE/'result.json'),workflow_outer_sha256=p.sha(OUTER/'execution.json'),
        original_native_workflow_cost={k:outer[k] for k in ('wall_seconds','full_cpu_seconds')},reader_cap_seconds=CAP)
    def remaining():return CAP-max(time.monotonic()-START,cpu()-CPU0)
    def stable():
        require(p.tool_manifest()==runtime,'reader runtime changed')  # tools before every material witness
        h.owned_destination(owner)
        for name,pin in filepins.items():require(p.sha(Path(name))==pin,'bound workflow/source/reader receipt changed')
        for name,witness in witnesses.items():require(e.witness(Path(name))==witness,'workflow/source evidence changed')
        require(remaining()>0,'pure workflow readback budget exhausted')
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
        if record['status']!='completed' or remaining()<=0:record['controls_passed']=False
    try:
        with p.validation_readback_session():
            stable()
            checked=e.check_export(folder/'export/export.json')  # existing complete Native/refill/class/PRL/source/choice proof reader
            require(checked['current'] is True and checked['export_accepted'] is True and checked['fresh_native_run_performed_by_check'] is False,'fresh export proof rejected')
            require(case['review_sha256']==p.sha(folder/'review/review.json') and case['choice_sha256']==p.sha(folder/'intent/choice.json')
                and case['rejection_sha256']==p.sha(folder/'rejection/choice.json') and case['export_sha256']==p.sha(folder/'export/export.json'),'case receipt hashes differ')
            require(exported['candidate_sha256']==case['candidate_sha256']==checked['candidate_sha256']
                and exported['native_report_sha256']==case['final_native_report_sha256'] and exported['metrics']==case['metrics'],'final candidate/report/metrics binding differs')
            require(tuple(exported['native'][k] for k in ('opens','blocking','warnings','exclusions'))==(0,0,42,0)
                and exported['native']['ignored_checks']==route['native']['ignored_checks']
                and [x for x in exported['native']['findings'] if x['severity']=='warning']==[x for x in route['native']['findings'] if x['severity']=='warning'],'original warning/ignore identity differs')
            require(accepted['choice']=='accept' and rejected['choice']=='reject' and rejected['status']=='disposition_recorded'
                and rejected['choice_recorded'] is True and rejected['within_budget'] is True,'accept/reject test intents incomplete')
            for key in ('routing_accepted','applied','native_validation_performed','human_pcb_approval_observed'):
                require(accepted[key] is False and rejected[key] is False,'test intent was relabelled approval/application')
            for key in ('review','review_sha256','receipt','receipt_sha256','validated_candidate','validated_candidate_sha256',
                        'original_source_hashes','routing_evidence_hashes','observed_review_project_hashes','saved_native_findings','saved_metrics'):
                require(rejected[key]==accepted[key],'rejection intent targets another reviewed board')
            preview=review['preview'];require(preview['layers']==['F.Cu','B.Cu'] and len(preview['steps'])==4
                and preview['native_validation_performed'] is False and preview['zone_refill_performed'] is False,'preview changed into Native acceptance')
            plotroot=folder/'review/plot-work';plots=[]
            for layer in preview['layers']:
                for label in ('before','after'):
                    name=label+'-'+layer;target=plotroot/'native-plots'/(name+'.svg');work=plotroot/(name+'-input')
                    source=(folder/'review'/('before' if label=='before' else 'project')/Path(route['source']).name)
                    binding=f.read_json(plotroot/(name+'-input-binding.json'))
                    require(binding['source']==str(source) and binding['input']==str(work/source.name) and binding['saved'] is False
                        and binding['before']==e.witness(source.parent,project=True)['files'] and binding['after']==e.witness(work,project=True)['files'],'plot copied-input binding differs')
                    p.check_drc_project(binding['before'],binding['after'],source.name)
                    argv=[*f.SANDBOX,str(c.CLI),'pcb','export','svg','--mode-single','--layers',layer+',Edge.Cuts',
                        '--fit-page-to-board','--exclude-drawing-sheet','--output',str(target),str(work/source.name)]
                    worker=f.process_check(plotroot,preview,name,argv);ls.check_event(plotroot,binding,worker)
                    require(view.display_svg(view.svg_bytes(target))==(plotroot/'plots'/target.name).read_bytes(),'display SVG differs from exact retained Native bytes')
                    plots.append(dict(name=name,process_sha256=p.sha(plotroot/(name+'-process.json')),native_svg_sha256=p.sha(target)))
            require({Path(n).name for n in e.witness(plotroot)['files'] if n.endswith('-process.json')}=={x['name']+'-process.json' for x in plots},'plot process census differs')
            record.update(status='completed',controls_passed=True,checked_export=checked,four_native_plot_workers=plots,
                exported_candidate_sha256=exported['candidate_sha256'],fresh_native_report_sha256=exported['native_report_sha256'],native_counts={k:exported['native'][k] for k in ('opens','blocking','warnings','exclusions')},
                preserved_original_warnings_and_ignored_checks=True,metrics=exported['metrics'],accept_test_intent=True,reject_test_intent=True,
                source_and_candidate_prl_proof='Existing complete export/normal-policy and actual plot guard readers; no new Native execution.',
                claims_limit='Software workflow qualification only; no GUI action, live application, human review, electrical/manufacturing or comparative quality claim.')
            stable()
    except BaseException as exc:record.update(status='failed',controls_passed=False,initial_failure=type(exc).__name__+': '+str(exc))
    f.publish(OUTPUT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    published=OUTPUT/'result.json'
    require(f.canonical(f.read_json(published))==f.canonical(record),'published workflow reader receipt differs')
    receipt_pin=p.sha(published)
    stable()
    require(p.sha(published)==receipt_pin,'workflow reader receipt changed during final callbacks')
    p.save_json(OUTPUT/'execution.json',dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,result_sha256=receipt_pin,small_publication_allowance_seconds=2))
    output_witness=e.witness(OUTPUT)
    stable()
    require(e.witness(OUTPUT)==output_witness,'workflow reader output changed during final callback')
    return record


if __name__=='__main__':
    result=check();print(f.canonical({k:result.get(k) for k in ('status','controls_passed','initial_failure')}));raise SystemExit(0 if result['status']=='completed' and result['controls_passed'] else 2)
