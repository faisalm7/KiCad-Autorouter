"""Prepared pure DS18B20 temperature interface matrix readback. No Native/JVM/engine calls or pcbnew import."""
from pathlib import Path
import time
START=time.monotonic()
CPU0=time.process_time()
import sys
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT))
import copy
import math
import signal
from autorouter import pipeline as p, floor_route as f, placement_clearance as pc
from autorouter import config as c, handoff as h, sexpr as sx, local_settings as ls
from experiments.native_paired_v1 import readback as shared
from scripts import experiment_paired as paired, experiment_quality as q
CPU0+=f.child_cpu()
ARMS=['B0','B1','B2_portfolio','C_feedback']
CAP=45.;STARTUP=1.;PUBLICATION=2.
LIMIT=512*1024**2


from experiments.native_paired_v1.observations import require,number,inventory,workers,candidate,resource_failure

def bind_row(raw,authoritative):
    """Raw status can lower eligibility; it cannot invent checked evidence."""
    require(type(raw.get('accepted')) is bool,'raw acceptance is not boolean')
    require(not raw['accepted'] or authoritative['accepted'] is True,'raw row accepted an unqualified receipt')
    invocation_error=raw.get('status')=='invocation_error'
    require(not invocation_error or raw['accepted'] is False,'invocation failure was accepted')
    for key,value in authoritative.items():
        if key=='accepted' or (invocation_error and key in ('status','reason')):continue
        if invocation_error and key not in raw:continue
        require(key in raw and f.canonical(raw[key])==f.canonical(value),'raw comparison field differs: '+key)
    return authoritative


def audit(prospective,output):
    prospective=Path(prospective).resolve(strict=True);output=Path(output).absolute()
    spec=f.read_json(prospective);base=ROOT/'.runs/ds18b20-native-paired240-001';run=base/'run'
    require(spec['status']=='frozen' and spec['reader_wall_full_cpu_cap_seconds']==CAP
        and spec['reader_startup_allowance_seconds']==STARTUP and spec['outer_publication_allowance_seconds']==PUBLICATION,'prospective reader limits differ')
    common=spec['common_prerequisites']
    def prerequisites():
        if common.get('source_gate_costs_complete') is not True or common.get('reader_startup_allowance_seconds')!=1:
            raise p.Rejected('complete actual source/control-gate costs required before launch')
        wall=cpu=1.;seen=set()
        for item in common['stages']:
            name=item['path'];path=ROOT/name
            if name in seen or not name.startswith('.runs/') or '..' in Path(name).parts or path.is_symlink() or p.sha(path)!=item['sha256']:
                raise p.Rejected('prerequisite receipt pin/path differs')
            seen.add(name);record=f.read_json(path)
            if record.get('passed') is not True or record.get('publication_allowance_seconds')!=2 or not (record.get('source_current') is True or record.get('protocol_and_source_current') is True):
                raise p.Rejected('prerequisite process did not qualify')
            for key in ('wall_seconds','full_cpu_seconds'):
                value=record[key]
                if not q.finite_nonnegative(value) or value!=item[key]:raise p.Rejected('prerequisite cost differs')
            if {k:v for k,v in record['tools'].items() if k!='git_head'}!={k:v for k,v in spec['tools'].items() if k!='git_head'}:
                raise p.Rejected('retained prerequisite actual tool/core bytes differ; historical HEAD remains literal')
            wall+=record['wall_seconds']+2;cpu+=record['full_cpu_seconds']+2
        required={'.runs/ds18b20-fetch-execution-001/execution.json','.runs/ds18b20-original-native-execution-001/execution.json','.runs/ds18b20-original-native-readback-execution-001/execution.json'}
        if required!=seen or wall!=common['wall_seconds'] or cpu!=common['full_cpu_seconds'] or max(wall,cpu)+180>240:
            raise p.Rejected('prerequisite240 reserve or complete cost differs')
        gate=spec['qualified_source_gate'];path=ROOT/gate['path'];review=f.read_json(path);native=f.read_json(ROOT/gate['original_receipt'])
        if gate.get('original_native_readback_passed') is not True or p.sha(path)!=gate['sha256'] or review.get('passed') is not True or review['checks']['consistent'] is not True:
            raise p.Rejected('qualified retained original Native readback required')
        if (native['project']!='ds18b20' or native['status']!='observed' or native['accepted'] is not False or native['production_support_qualified'] is not False or native['serialization_equivalence_qualified'] is not False
                or native['protect_local_settings'] is not True or native['original_hashes']!=spec['complete_native_packet_sha256'] or native['source_file_count']!=6 or native['source_bytes']!=124777
                or review['checks']['receipt_sha256']!=p.sha(ROOT/gate['original_receipt']) or native['final_native_report_sha256']!=spec['original_native_report']['sha256']
                or not p.native_accepted(native['parity_native']) or (native['parity_native']['warnings'],len(native['parity_native']['ignored_checks']))!=(11,7)):
            raise p.Rejected('original source/native/PRL/11warning/7ignored metadata differs')
        for name,pin in native['additional_implementation_sha256'].items():
            if p.sha(ROOT/name)!=pin:raise p.Rejected('original source/helper implementation changed: '+name)
        for name,pin in common['pins'].items():
            if p.sha(ROOT/name)!=pin:raise p.Rejected('source/control qualification material changed')
        return wall,cpu
    common_wall,common_cpu=prerequisites()
    require(spec['delivered_wall_full_cpu_budget_per_arm_seconds']==240,'delivered240 contract differs')
    dependencies=spec['reader_dependencies_sha256']
    require(type(dependencies) is dict and set(dependencies)=={'experiments/native_paired_v1/readback.py','experiments/native_paired_v1/observations.py'}
        and all(type(v) is str and len(v)==64 and all(ch in '0123456789abcdef' for ch in v) for v in dependencies.values()),'reader dependency pins differ')
    require(str(Path(__file__).resolve())==spec['reader_source'] and p.sha(Path(__file__))==spec['reader_sha256'],'reader source differs')
    outer=f.read_json(base/'execution.json');summary=f.read_json(run/'paired-summary.json');protocol=f.read_json(run/'protocol.json')
    board,family=q.selected_source('ds18b20');original=p.preflight(board);hashes=p.tree_hash(board.parent)
    require(spec['source']==str(board) and spec['family']==family and spec['original_source_sha256']==hashes
        and len(hashes)==6 and spec['freeze']==protocol['freeze'] and spec['tools']==protocol['freeze']['tools'],'original six-file root/notice source/freeze differs')
    require(protocol['source']==str(board) and protocol['arm_order']==ARMS and protocol['paired_system']=='native-all'
        and protocol['external_reserve_seconds']==0 and protocol['wall_budget_per_arm_seconds']==protocol['cpu_budget_per_arm_seconds']==120,'paired contract differs')
    require(summary['protocol_sha256']==p.sha(run/'protocol.json') and [r['id'] for r in summary['results']]==ARMS,'four-arm population differs')
    require(outer['prospective_protocol_sha256']==p.sha(prospective)
        and outer['paired_summary_sha256']==p.sha(run/'paired-summary.json')
        and outer['paired_protocol_sha256']==p.sha(run/'protocol.json') and outer['tools']==spec['tools']
        and outer['git_head']==spec['tools']['git_head'] and outer['wrapper_sha256']==spec['wrapper_sha256'],'outer witness differs')
    require(outer['common_prerequisites']==common and outer['qualified_source_gate']==spec['qualified_source_gate'],'outer prerequisite witness differs')
    process=outer['process'];require(process['cleanup_complete'] is True,'outer cleanup unconfirmed')
    expected_argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/experiment_paired.py'),
        '--project','ds18b20','--system','native-all','--external-reserve-seconds','0','--output',str(run)]
    require(process['argv']==expected_argv and process['cwd']==str(base) and process['log']==str(base/'command.log')
        and process.get('log_truncated') is False,'outer process identity/log differs')
    pc.read_bytes(base/'command.log',256*1024)
    require(outer['log_sha256']==p.sha(base/'command.log') and outer['paired_material']==inventory(run)[0], 'outer log/material witness differs')
    expected_population=[dict(id=arm,raw_row_indices=[i for i,row in enumerate(summary['results']) if row['id']==arm],disposition='retained') for arm in ARMS]
    require(outer['arm_population']==expected_population and outer['paired_status']==summary['status'],'outer population/status differs')
    require(outer['qualified'] is False and outer['accepted'] is False and outer['production_qualified'] is False,'outer launcher claimed qualification')
    require(p.sha(base/'wrapper.py')==spec['wrapper_sha256'] and p.sha(base/'prospective-protocol.json')==p.sha(prospective),'retained launcher/protocol differs')
    output.mkdir();owner={};h.capture_destination(owner,output)
    original_report=spec['original_native_report'];report_path=Path(original_report['path'])
    require(p.sha(report_path)==original_report['sha256'],'original baseline report changed')
    # Exact raw fullSCH Native bytes retain11warnings/7ignored. No field-sidecar patch or borrowed source gate.
    raw_report_copy=output/'original-native-raw.json'
    with raw_report_copy.open('xb') as stream:stream.write(pc.read_bytes(report_path,16*1024**2))
    require(p.sha(raw_report_copy)==original_report['sha256'],'raw original report copy differs')
    baseline=p.parse_report(raw_report_copy,board.name)
    raw_summary=original_report['summary']
    require(baseline==raw_summary,'original baseline raw native summary differs')
    source_witness=inventory(board.parent);material=inventory(base);pins={str(prospective):p.sha(prospective),str(Path(__file__).resolve()):p.sha(Path(__file__)),str(report_path):p.sha(report_path),str(raw_report_copy):original_report['sha256']}
    result=dict(schema=1,kind='DS18B20-normal-four-arm-delivered240-independent-readback-v1',accepted=False,status='incomplete',
        comparison_eligible=False,readback_failures=[],new_native_execution=False,new_engine_execution=False,source=str(board),source_hashes=hashes,
        common_prerequisites=common,qualified_source_gate=spec['qualified_source_gate'],delivered_wall_full_cpu_budget_per_arm_seconds=240,
        prospective_protocol_sha256=p.sha(prospective),reader_sha256=p.sha(Path(__file__)),original_native_report=original_report,
        reader_dependencies_sha256=dependencies,outer_status=copy.deepcopy(process),raw_paired_status=summary['status'],results=[],final_candidates=[],workers=[],
        limits='One exposed DS18B20 development family. No independent ancestry, human PCB review, electrical adequacy, untouched holdout or generalized superiority claim.',
        common_interchange_safety=protocol.get('common_interchange_safety'),raw_comparisons=summary.get('comparisons',[]),
        charge_policy='Replace paired shared charge with complete enclosing overhead; full overhead and actual reader plus startup1/publication2 charged to EACH arm. Common acquisition/original/source-gate costs and reader enclosing publication2 also charged EACH arm. Original receipts unchanged.')
    def elapsed():return time.monotonic()-START,time.process_time()+f.child_cpu()-CPU0
    def remaining():return CAP-max(elapsed())
    result_pin=execution_pin=None
    def stable():
        # Large tool files are hashed by the shared tool verifier FIRST, never read through64MiB pc.read_bytes.
        require(p.tool_manifest()==spec['tools'],'current tools/implementation differ')
        q.verify_freeze(protocol['freeze'],board)
        prerequisites()
        for name,pin in spec['complete_source_files_sha256'].items():require(p.sha(ROOT/name)==pin,'complete DS18B20 source packet changed')
        for name,pin in dependencies.items():
            require(p.sha(ROOT/name)==pin and p.sha(base/'reader-dependencies'/name.removeprefix('experiments/'))==pin,'shared reader live/captured dependency changed')
        require(p.sha(base/'reader.py')==spec['reader_sha256'],'captured reader differs')
        h.owned_destination(owner)
        # Reuse the strict Native event replay AFTER all tool/freeze callbacks.
        # Byte inventories alone do not witness flags or hard-link counts.
        for worker in result['workers']:
            cwd=Path(worker['cwd']);name=worker['name'];process=f.read_json(cwd/(name+'-process.json'))
            argv=process['argv'];command=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
            if command[:3]==[str(c.CLI),'pcb','drc']:
                binding=f.read_json(cwd/(name+'-binding.json'))
                failed=process['status']!='success' and not (process['status']=='nonzero_exit' and process.get('exit_code')==5)
                ls.check_event(cwd,binding,process,allow_worker_failure=failed)
        require(inventory(base)==material and inventory(board.parent)==source_witness,'matrix/source material changed')
        for name,pin in pins.items():require(p.sha(Path(name))==pin,'reader/protocol/baseline pin changed')
        if result_pin is not None:require(p.sha(output/'result.json')==result_pin,'published reader receipt changed during final callbacks')
        if execution_pin is not None:require(p.sha(output/'execution.json')==execution_pin,'reader execution changed during final callbacks')
        require(remaining()>0,'reader45-second wall/fullCPU allowance exceeded')
    def account():
        wall,cpu=elapsed();total_wall=number(outer['wall_seconds']);total_cpu=number(outer['full_cpu_seconds'])
        require(sum(number(r['invocation_wall_seconds']) for r in summary['results'])<=total_wall
            and sum(number(r['invocation_cpu_seconds']) for r in summary['results'])<=total_cpu,'sequential invocation sums exceed enclosing costs')
        overhead_wall=max(0.,total_wall-sum(number(r['invocation_wall_seconds']) for r in summary['results']))
        overhead_cpu=max(0.,total_cpu-sum(number(r['invocation_cpu_seconds']) for r in summary['results']))
        valid=(result['status']=='completed' and not result.get('readback_failures') and remaining()>0 and summary['status']=='completed'
            and outer.get('source_current') is True and outer.get('clean_checkpoint_before') is True
            and outer.get('clean_checkpoint_after') is True and outer.get('whole_delivery_within_budget') is True
            and not any(k in outer for k in ('reason','final_check_error','material_error'))
            and process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0)
        for row in result['results']:
            row.update(charged_wall_seconds=row['invocation_wall_seconds']+common_wall+overhead_wall+PUBLICATION+wall+STARTUP+PUBLICATION,
                charged_cpu_seconds=row['invocation_cpu_seconds']+common_cpu+overhead_cpu+PUBLICATION+cpu+STARTUP+PUBLICATION)
            within=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=240
            row.update(within_equal240_wall_full_cpu_caps=within,accepted=valid and row['raw_paired_accepted'] and within)
        result.update(observed_reader_wall_seconds=wall,observed_reader_full_cpu_seconds=cpu,
            replacement_shared_wall_seconds=overhead_wall,replacement_shared_full_cpu_seconds=overhead_cpu,
            comparison_eligible=valid,comparisons=paired.comparisons(result['results']) if valid else [])
    try:
        with p.validation_readback_session():
            stable()
            require(sum(number(r['invocation_wall_seconds']) for r in summary['results'])<=number(outer['wall_seconds'])
                and sum(number(r['invocation_cpu_seconds']) for r in summary['results'])<=number(outer['full_cpu_seconds']),'sequential invocation sums exceed enclosing costs')
            require(number(outer['wall_seconds'])>=number(summary['batch_wall_seconds'])
                and number(outer['full_cpu_seconds'])>=number(summary['batch_cpu_seconds']),'outer accounting omits inner costs')
            portfolio=f.read_json(run/'B2_portfolio/portfolio-summary.json') if (run/'B2_portfolio/portfolio-summary.json').exists() else None
            if portfolio is not None:
                portfolio_authoritative=paired.verify_portfolio(run/'B2_portfolio',portfolio,board,protocol['freeze'])
                bind_row(next(r for r in summary['results'] if r['id']=='B2_portfolio'),portfolio_authoritative)
                result['portfolio_coverage']={k:portfolio.get(k) for k in ('status','attempted_variants','unattempted_variants','all_variants_attempted','skipped_variants','stop_reason','pareto_frontier','selected')}
            paths=[]
            for raw in summary['results']:
                row=copy.deepcopy(raw);row['raw_paired_accepted']=raw['accepted'];row['accepted']=False
                if raw['id']=='B2_portfolio' and portfolio is None:require(raw['accepted'] is False,'accepted B2 has no receipt')
                result['results'].append(row)
                if raw['id']=='B2_portfolio':
                    for trial in (portfolio or {}).get('trials',[]):
                        if trial.get('result'):paths.append((f"B2/{trial['id']}",Path(trial['result']),None))
                else:
                    path=run/raw['id']/'result.json'
                    if path.exists():
                        arm=paired.C_ARM if raw['id']=='C_feedback' else dict(id=raw['id'],adapter='none' if raw['id']=='B0' else 'both',engine_profile='standard',operation='route')
                        authoritative=q.summarize(arm,path.parent,f.read_json(path),raw['invocation_wall_seconds'],raw['invocation_cpu_seconds'])
                        if authoritative['accepted_in_receipt']:require(authoritative['receipt_verified'] is True,'accepted receipt failed shared readback')
                        bind_row(raw,authoritative);row['checked_receipt_summary']=authoritative
                        paths.append((raw['id'],path,None))
                    else:require(raw['accepted'] is False,'accepted arm has no receipt')
            for label,path,parent in paths:
                require(run in path.parents and path.name=='result.json','receipt escaped this matrix')
                data=f.read_json(path);folder=path.parent
                require(data['tools']==protocol['freeze']['tools'] and data['source_hashes']==hashes and data['source']==str(board),'candidate source/tools differ')
                if data.get('accepted') is True:p.check_result(path)
                elif not (data.get('candidate_sha256') and data.get('native_report_sha256')):
                    result.setdefault('unqualified_receipts',[]).append(dict(id=label,status=data['status'],reason='incomplete final candidate; raw workers and completed Native observations retained'))
                result['workers'].extend(workers(folder,data,board,hashes,original))
                resource_error=resource_failure(folder,data)
                if resource_error:result.setdefault('unqualified_receipts',[]).append(dict(id=label,status=data['status'],reason=resource_error))
                if data.get('candidate_sha256') and data.get('native_report_sha256'):
                    result['final_candidates'].append(dict(id=label,status=data['status'],**candidate(folder,data,board,original,hashes,baseline,resource_error=resource_error)))
                if label=='C_feedback' and data.get('incumbent'):
                    inc_folder=folder/'incumbent';inc=f.read_json(inc_folder/'result.json');marker=data['incumbent']
                    require(marker['receipt']==str(inc_folder/'result.json') and all(marker.get(k)==inc.get(k) for k in ('status','accepted','metrics','wall_seconds')),'C incumbent marker differs')
                    require(all(inc.get(k)==data.get(k) for k in ('source','source_hashes','tools'))
                        and [dict(step,phase='incumbent') for step in inc.get('steps',[])]==[step for step in data['steps'] if step.get('phase')=='incumbent'],'C own incumbent lineage differs')
                    inc_resource=resource_failure(inc_folder,inc)
                    if inc.get('candidate_sha256') and inc.get('native_report_sha256'):
                        if resource_error is None and inc_resource is None:
                            shared.pruning_incumbent_readback(folder,data,board,original,hashes)
                        result['final_candidates'].append(dict(id='C/incumbent',status=inc['status'],**candidate(inc_folder,inc,board,original,hashes,baseline,resource_error=inc_resource)))
                    else:result.setdefault('unqualified_receipts',[]).append(dict(id='C/incumbent',status=inc['status'],reason='incomplete final candidate; raw worker observations retained'))
                    for trial in data.get('trials',[]):
                        child=folder/'trials'/trial['id'];record=f.read_json(child/'result.json')
                        require(trial['receipt']==str(child/'result.json') and all(trial[k]==record[k] for k in ('id','status','accepted')),'pruning trial escaped or differs from parent')
                        trial_resource=resource_failure(child,record,data)
                        if record.get('candidate_sha256') and record.get('native_report_sha256'):
                            result['final_candidates'].append(dict(id='C/'+trial['id'],status=record['status'],**candidate(child,record,board,original,hashes,baseline,parent=data,resource_error=trial_resource)))
                        else:result.setdefault('unqualified_receipts',[]).append(dict(id='C/'+trial['id'],status=record['status'],reason='incomplete final candidate; raw worker observations retained'))
            result['status']='completed'
    except (Exception,KeyboardInterrupt) as exc:
        result.update(status='failed',initial_failure=type(exc).__name__+': '+str(exc))
    # Stable callback always rechecks tools first. Account immediately before write;
    # a fixed45s reader reservation below conservatively covers all later callbacks.
    def final_bound():
        stable()
        for row in result['results']:
            wall=number(row['invocation_wall_seconds'])+common_wall+result['replacement_shared_wall_seconds']+PUBLICATION+CAP+STARTUP+PUBLICATION
            cpu=number(row['invocation_cpu_seconds'])+common_cpu+result['replacement_shared_full_cpu_seconds']+PUBLICATION+CAP+STARTUP+PUBLICATION
            require(not row['accepted'] or max(wall,cpu)<=240,'reader publication could exceed per-arm240')
    f.publish(output,result,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_bound)
    require(f.canonical(f.read_json(output/'result.json'))==f.canonical(result),'published reader receipt differs')
    result_pin=p.sha(output/'result.json')
    stable()
    wall,cpu=elapsed();final_rows=copy.deepcopy(result['results'])
    for row in final_rows:
        row['charged_wall_seconds']=row['invocation_wall_seconds']+common_wall+result['replacement_shared_wall_seconds']+PUBLICATION+wall+STARTUP+PUBLICATION
        row['charged_cpu_seconds']=row['invocation_cpu_seconds']+common_cpu+result['replacement_shared_full_cpu_seconds']+PUBLICATION+cpu+STARTUP+PUBLICATION
        row['within_equal240_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=240
        row['accepted']=row['accepted'] and row['within_equal240_wall_full_cpu_caps']
    p.save_json(output/'execution.json',dict(wall_seconds=wall,full_cpu_seconds=cpu,result_sha256=result_pin,
        final_charged_results=final_rows,comparisons=paired.comparisons(final_rows) if result['comparison_eligible'] else [],
        comparison_eligible=result['comparison_eligible'],

        reader_cap_wall_full_cpu_seconds=CAP,startup_allowance_seconds=STARTUP,outer_publication_allowance_seconds=PUBLICATION,
        complete_cost_scope='Before imports through reader publication; interpreter startup separately charged1. Last small execution receipt and final proof covered by remaining45s reservation.'))
    execution_pin=p.sha(output/'execution.json')
    stable()
    require(p.sha(output/'result.json')==result_pin and p.sha(output/'execution.json')==execution_pin,'final reader receipts changed')
    require(f.read_json(output/'execution.json')['result_sha256']==result_pin,'final reader receipt differs')
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prospective',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.prospective,args.output)
    print(f.canonical({k:result.get(k) for k in ('status','comparison_eligible','initial_failure')}))
    raise SystemExit(0 if result['status']=='completed' else 2)
