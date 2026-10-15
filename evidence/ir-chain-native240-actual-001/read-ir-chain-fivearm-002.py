"""Prepared pure IR five-arm matrix readback. No Native/JVM/engine calls or pcbnew import."""
from pathlib import Path
import time
START=time.monotonic()
CPU0=time.process_time()
import sys
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT))
# Draft preparation: first clock2026-10-15 12:48:29UTC; through final source review12:52:55UTC=266s.
# Excludes dispatch/final notification; full controller/model CPU unavailable. No execution or tests by preparer.
import copy
import hashlib
import math
import signal
from autorouter import pipeline as p, floor_route as f, placement_clearance as pc
from autorouter import config as c, handoff as h, sexpr as sx, local_settings as ls
from experiments.native_paired_v1 import readback as shared
from scripts import experiment_paired as paired, experiment_quality as q
CPU0+=f.child_cpu()
CONTINUATION=ROOT/'.runs/ir-chain-fivearm-readback002-protocol.json'
BASE_ARMS=['B0','B1','B2_portfolio','C_feedback']
ARMS=[*BASE_ARMS,'C_chains']
CHAIN_ARM=dict(id='C_chains',adapter='both',engine_profile='tuned',operation='prune',proposal_policy='chains')
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


def bind_returned_paired(returned,saved):
    """Only the two monotone, common post-publication charge changes are allowed.
    Every invocation cost, candidate, native observation and eligibility remains exact.
    Final accounting replaces BOTH common charges with actual whole-five-arm overhead.
    """
    require(len(returned)==len(saved)==4,'returned/stored fourarm population differs')
    changed=('charged_wall_seconds','charged_cpu_seconds');deltas=[]
    for left,right in zip(returned,saved):
        require(set(left)==set(right) and {k:v for k,v in left.items() if k not in changed}
            =={k:v for k,v in right.items() if k not in changed},'returned paired noncharge metadata differs')
        delta=[number(left[key])-number(right[key]) for key in changed]
        require(min(delta)>=0,'returned paired common charges decreased')
        deltas.append(delta)
    require(all(abs(delta[i]-deltas[0][i])<=1e-9 for delta in deltas for i in range(2)),'returned paired charge increments differ among arms')
    return dict(zip(changed,deltas[0]))


def matrix_material(base):
    files,directories=pc.inventory(base,max_bytes=44*1024**2,max_files=10000,max_entries=20000,with_directories=True)
    return ({n:v for n,v in files.items() if n!='execution.json'},directories)


def comparisons(rows):
    answer=[]
    for system in ('C_feedback','C_chains'):
        mapped=[dict(row,id='C_feedback') if row['id']==system else copy.deepcopy(row)
                for row in rows if row['id'] in ('B0','B1','B2_portfolio',system)]
        for item in paired.comparisons(mapped):
            item['system']=system;answer.append(item)
    return answer


def audit(prospective,output):
    prospective=Path(prospective).resolve(strict=True);output=Path(output).absolute()
    base=ROOT/'.runs/ir-chain-fivearm-001';run=base/'run';spec=f.read_json(prospective)
    require(prospective==ROOT/'.runs/ir-chain-fivearm-001-protocol.json','wrong prospective protocol')
    require(type(spec.get('schema')) is int and spec['schema']==1 and spec['status']=='frozen'
        and spec['project']=='ir-obstacle' and spec['arm_order']==ARMS,'prospective five-arm identity differs')
    require(spec['limits']==dict(reader=45,delivered=240,inner=120,outer=800,output=44*1024**2),'prospective limits differ')
    continuation=f.read_json(CONTINUATION)
    require(continuation['status']=='frozen' and continuation['old_protocol_sha256']==p.sha(prospective)
        and continuation['reader_source']==str(Path(__file__).resolve()) and continuation['reader_sha256']==p.sha(Path(__file__))
        and p.sha(Path(spec['reader_source']))==spec['reader_sha256'],'explicit missing-readback continuation source differs')
    require(p.sha(base/'execution.json')==continuation['outer_sha256'],'completed Native enclosure changed')
    dependencies=spec['reader_dependencies_sha256']
    require(type(dependencies) is dict and set(dependencies)=={'experiments/native_paired_v1/readback.py','experiments/native_paired_v1/observations.py'}
        and all(type(v) is str and len(v)==64 and all(ch in '0123456789abcdef' for ch in v) for v in dependencies.values()),'reader dependency pins differ')
    common_wall=number(continuation['failed_reader_charge']['wall_seconds'])
    common_cpu=number(continuation['failed_reader_charge']['full_cpu_seconds'])
    def prerequisites():
        pins={**spec['pins'],**continuation['pins']};require(type(pins) is dict and pins,'frozen original source proof pins required')
        gate_name='.runs/ir-obstacle-original-field-gate-003/result.json'
        old_name='.runs/ir-obstacle-corrected300-003-protocol.json'
        original_name='.runs/ir-obstacle-original-native-001/result.json';review_name='.runs/ir-obstacle-original-native-readback-001/result.json'
        require({gate_name,old_name,original_name,review_name}<=set(pins),'existing original field gate/IR300 proof absent')
        for name,pin in pins.items():
            path=Path(name) if Path(name).is_absolute() else ROOT/name
            require(path.is_relative_to(ROOT) and not path.is_symlink() and '..' not in path.parts
                and p.sha(path)==pin,'frozen original qualification material changed: '+name)
        gate=f.read_json(ROOT/gate_name);prior=f.read_json(ROOT/old_name)
        require(gate['passed'] is True and gate['source_current'] is True and gate['original_unchanged'] is True
            and gate['new_native_execution'] is False,'retained corrected original gate differs')
        original_report=spec['original_native_report']
        require(original_report['path']==prior['raw_baseline'] and original_report['sha256']==prior['raw_baseline_sha256']
            and original_report['summary']==prior['raw_baseline_summary']
            and gate['native_report_sha256']==original_report['sha256'],'retained full42-warning original baseline differs')
        require(prior['field_gate']==gate_name and original_report['summary']['warnings']==42
            and len(original_report['summary']['ignored_checks'])==7,'wrong original field gate/baseline')
        from scripts.fetch_led_demo import capture_native_source
        from experiments.original_project_native_v1.driver import completed_evidence
        from autorouter import schematic_field_evidence as fields
        origin=ROOT/'.runs/ir-obstacle-original-native-001';old=f.read_json(ROOT/original_name);review=f.read_json(ROOT/review_name)
        source,files=capture_native_source('ir-obstacle',root=ROOT)
        sourcepins={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}
        require(sourcepins==gate['source_hashes']==old['original_hashes'] and review['passed'] is True
            and review['checks']['consistent'] is True and old['native_routing_scope_accepted'] is False
            and all(old.get(k) is True for k in ('original_shell_nonfill_ast_equal','all_original_route_records_exact','original_preserved')),'retained original source/shell proof differs')
        witness=completed_evidence(origin)
        require(hashlib.sha256(f.canonical(witness).encode()).hexdigest()==old['completed_evidence_sha256']
            and p.sha(origin/'result.json')==gate['prior_original_receipt_sha256']
            and p.sha(ROOT/review_name)==gate['prior_independent_reader_sha256'],'original material/receipt pins differ')
        for name,pin in prior['field_helpers_sha256'].items():require(p.sha(ROOT/name)==pin,'original field-proof helper changed')
        proof=fields.derive(origin/'job','original-final',f.read_json(origin/'job/original-final.json'))
        qualified=copy.deepcopy(old['parity_native']);qualified['field_parity']=proof
        require(proof==gate['field_proof'] and qualified==gate['qualified_native'] and p.native_accepted(qualified)
            and qualified['findings']==original_report['summary']['findings'],'retained full original field qualification differs')
    prerequisites()
    outer=f.read_json(base/'execution.json');summary=f.read_json(run/'paired-summary.json');protocol=f.read_json(run/'protocol.json')
    actor=f.read_json(base/'actor-result.json');chain=f.read_json(base/'chain-invocation.json')
    require(actor['status']=='completed' and actor['arm_order']==ARMS and [r['id'] for r in actor['rows']]==ARMS,'five-arm actor population differs')
    rows=actor['rows']
    returned_cost_delta=bind_returned_paired(rows[:4],summary['results'])
    require(rows[4]==chain and chain['id']=='C_chains','chain row differs from saved invocation')
    board,family=q.selected_source('ir-obstacle');original=p.preflight(board);hashes=p.tree_hash(board.parent)
    require(spec['source']==str(board) and spec['family']==family and spec['source_hashes']==hashes
        and spec['freeze']==protocol['freeze'] and spec['tools']==protocol['freeze']['tools']
        and spec['git_head']==spec['tools']['git_head'],'source or freeze differs')
    require(protocol['source']==str(board) and protocol['arm_order']==BASE_ARMS and protocol['paired_system']=='native-all'
        and protocol['external_reserve_seconds']==0 and protocol['wall_budget_per_arm_seconds']==protocol['cpu_budget_per_arm_seconds']==120,'paired contract differs')
    require(summary['protocol_sha256']==p.sha(run/'protocol.json') and [r['id'] for r in summary['results']]==BASE_ARMS,'four-arm population differs')
    for key,path in (('protocol_sha256',prospective),('paired_summary_sha256',run/'paired-summary.json'),
                     ('paired_protocol_sha256',run/'protocol.json'),('chain_invocation_sha256',base/'chain-invocation.json')):
        require(outer[key]==p.sha(path),'outer witness differs: '+key)
    require(outer['tools']==spec['tools'] and outer['git_head']==spec['git_head']
        and outer['actor_result_sha256']==p.sha(base/'actor-result.json'),'outer tools/HEAD/actor differ')
    for kind in ('reader','actor','controller'):
        require(outer[kind+'_sha256']==spec[kind+'_sha256'] and p.sha(Path(spec[kind+'_source']))==spec[kind+'_sha256'],'frozen '+kind+' differs')
    process=outer['process'];require(process['cleanup_complete'] is True and process.get('log_truncated') is False,'outer cleanup/log unconfirmed')
    require(process['argv']==spec['actor_argv'] and process['cwd']==spec['actor_cwd']==str(base)
        and process['log']==spec['actor_log']==str(base/'command.log')
        and spec['actor_source'] in process['argv'],'outer actor identity differs')
    log=Path(process['log']);require(log.parent==base,'outer log escaped matrix');pc.read_bytes(log,256*1024)
    require(outer['material']==[matrix_material(base)[0],list(matrix_material(base)[1])]
        or outer['material']==matrix_material(base),'outer material witness differs')
    output.mkdir();owner={};h.capture_destination(owner,output)
    original_report=spec['original_native_report'];report_path=Path(original_report['path'])
    require(p.sha(report_path)==original_report['sha256'],'original baseline report changed')
    # Exact raw fullSCH Native bytes retain42warnings/7ignored; original gate is rederived above.
    raw_report_copy=output/'original-native-raw.json'
    with raw_report_copy.open('xb') as stream:stream.write(pc.read_bytes(report_path,16*1024**2))
    require(p.sha(raw_report_copy)==original_report['sha256'],'raw original report copy differs')
    baseline=p.parse_report(raw_report_copy,board.name)
    raw_summary=original_report['summary']
    require(baseline==raw_summary,'original baseline raw native summary differs')
    source_witness=inventory(board.parent);material=matrix_material(base);pins={str(prospective):p.sha(prospective),str(Path(__file__).resolve()):p.sha(Path(__file__)),str(report_path):p.sha(report_path),str(raw_report_copy):original_report['sha256']}
    result=dict(schema=1,kind='IR-normal-five-arm-delivered240-readback-v1',accepted=False,status='incomplete',
        comparison_eligible=False,readback_failures=[],new_native_execution=False,new_engine_execution=False,source=str(board),source_hashes=hashes,
        failed_reader_charge=continuation['failed_reader_charge'],returned_paired_cost_delta=returned_cost_delta,historical_source_costs='separately recorded development/exposed acquisition and source qualification',delivered_wall_full_cpu_budget_per_arm_seconds=240,
        prospective_protocol_sha256=p.sha(prospective),continuation_protocol_sha256=p.sha(CONTINUATION),reader_sha256=p.sha(Path(__file__)),original_native_report=original_report,
        reader_dependencies_sha256=dependencies,outer_status=copy.deepcopy(process),raw_paired_status=summary['status'],results=[],final_candidates=[],workers=[],
        limits='One exposed IR obstacle development family. No independent ancestry, human PCB review, electrical adequacy, untouched holdout or generalized superiority claim.',
        common_interchange_safety=protocol.get('common_interchange_safety'),raw_comparisons=summary.get('comparisons',[]),
        charge_policy='Replace paired shared charge with complete enclosing overhead; full overhead and actual reader plus startup1/publication2 charged to EACH arm. Reader enclosing publication2 and failed001reader actual/startup/publication are charged EACH arm; historical source/development costs are separate. Original receipts unchanged; historical source qualification/acquisition/development costs are separately disclosed, not current routing operation.')
    def elapsed():return time.monotonic()-START,time.process_time()+f.child_cpu()-CPU0
    def remaining():return CAP-max(elapsed())
    result_pin=execution_pin=None
    def stable():
        # Large tool files are hashed by the shared tool verifier FIRST, never read through64MiB pc.read_bytes.
        require(p.sha(CONTINUATION)==result['continuation_protocol_sha256'],'continuation protocol changed')
        require(p.tool_manifest()==spec['tools'],'current tools/implementation differ')
        q.verify_freeze(protocol['freeze'],board)
        prerequisites()
        for name,pin in dependencies.items():
            require(p.sha(ROOT/name)==pin and p.sha(base/'reader-dependencies'/name.removeprefix('experiments/'))==pin,'shared live/captured reader dependency changed')
        require(p.sha(base/'reader.py')==spec['reader_sha256'] and p.sha(base/'actor.py')==spec['actor_sha256']
            and p.sha(base/'controller.py')==spec['controller_sha256'] and p.sha(base/'prospective-protocol.json')==p.sha(prospective),'captured five-arm controllers/protocol changed')
        for kind in ('reader','actor','controller'):
            require(p.sha(Path(spec[kind+'_source']))==spec[kind+'_sha256'],'frozen '+kind+' changed')
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
        require(matrix_material(base)==material and inventory(board.parent)==source_witness,'matrix/source material changed')
        for name,pin in pins.items():require(p.sha(Path(name))==pin,'reader/protocol/baseline pin changed')
        if result_pin is not None:require(p.sha(output/'result.json')==result_pin,'published reader receipt changed during final callbacks')
        if execution_pin is not None:require(p.sha(output/'execution.json')==execution_pin,'reader execution changed during final callbacks')
        require(remaining()>0,'reader45-second wall/fullCPU allowance exceeded')
    def account():
        wall,cpu=elapsed();total_wall=number(outer['wall_seconds']);total_cpu=number(outer['full_cpu_seconds'])
        require(sum(number(r['invocation_wall_seconds']) for r in rows)<=total_wall
            and sum(number(r['invocation_cpu_seconds']) for r in rows)<=total_cpu,'sequential invocation sums exceed enclosing costs')
        overhead_wall=max(0.,total_wall-sum(number(r['invocation_wall_seconds']) for r in rows))
        overhead_cpu=max(0.,total_cpu-sum(number(r['invocation_cpu_seconds']) for r in rows))
        valid=(result['status']=='completed' and not result.get('readback_failures') and remaining()>0 and summary['status']=='completed' and actor['status']=='completed'
            and outer.get('source_current') is True and outer.get('clean_before') is True
            and outer.get('clean_after') is True and outer.get('passed') is True
            and max(number(outer['wall_seconds']),number(outer['full_cpu_seconds']))+PUBLICATION<=800
            and not any(k in outer for k in ('reason','final_check_error','material_error'))
            and result.get('portfolio_all_variants_attempted') is True
            and process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0)
        for row in result['results']:
            row.update(charged_wall_seconds=row['invocation_wall_seconds']+common_wall+overhead_wall+PUBLICATION+wall+STARTUP+PUBLICATION,
                charged_cpu_seconds=row['invocation_cpu_seconds']+common_cpu+overhead_cpu+PUBLICATION+cpu+STARTUP+PUBLICATION)
            within=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=240
            row.update(within_equal240_wall_full_cpu_caps=within,accepted=valid and row['raw_paired_accepted'] and within)
        result.update(observed_reader_wall_seconds=wall,observed_reader_full_cpu_seconds=cpu,
            replacement_shared_wall_seconds=overhead_wall,replacement_shared_full_cpu_seconds=overhead_cpu,
            comparison_eligible=valid,comparisons=comparisons(result['results']) if valid else [])
    try:
        with p.validation_readback_session():
            stable()
            require(sum(number(r['invocation_wall_seconds']) for r in rows)<=number(outer['wall_seconds'])
                and sum(number(r['invocation_cpu_seconds']) for r in rows)<=number(outer['full_cpu_seconds']),'sequential invocation sums exceed enclosing costs')
            require(number(outer['wall_seconds'])>=number(summary['batch_wall_seconds'])
                and number(outer['full_cpu_seconds'])>=number(summary['batch_cpu_seconds']),'outer accounting omits inner costs')
            portfolio=f.read_json(run/'B2_portfolio/portfolio-summary.json') if (run/'B2_portfolio/portfolio-summary.json').exists() else None
            if portfolio is not None:
                portfolio_authoritative=paired.verify_portfolio(run/'B2_portfolio',portfolio,board,protocol['freeze'])
                bind_row(next(r for r in rows if r['id']=='B2_portfolio'),portfolio_authoritative)
                result['portfolio_coverage']={k:portfolio.get(k) for k in ('status','attempted_variants','unattempted_variants','all_variants_attempted','skipped_variants','stop_reason','pareto_frontier','selected')}
                result['portfolio_all_variants_attempted']=portfolio.get('all_variants_attempted') is True and len(portfolio.get('trials',[]))==len(paired.portfolio.VARIANTS)==3
            require(number(chain['assigned_seconds'])==number(protocol['inner_allowance_seconds']),'fifth arm assigned allowance differs')
            paths=[]
            for raw in rows:
                require(number(raw['invocation_wall_seconds'])<=number(outer['wall_seconds']) and number(raw['invocation_cpu_seconds'])<=number(outer['full_cpu_seconds']),'arm costs exceed whole invocation')
                row=copy.deepcopy(raw);row['raw_paired_accepted']=raw['accepted'];row['accepted']=False
                if raw['id']=='B2_portfolio' and portfolio is None:require(raw['accepted'] is False,'accepted B2 has no receipt')
                result['results'].append(row)
                if raw['id']=='B2_portfolio':
                    for trial in (portfolio or {}).get('trials',[]):
                        if trial.get('result'):paths.append((f"B2/{trial['id']}",Path(trial['result']),None))
                else:
                    path=(base if raw['id']=='C_chains' else run)/raw['id']/'result.json'
                    if path.exists():
                        arm=CHAIN_ARM if raw['id']=='C_chains' else paired.C_ARM if raw['id']=='C_feedback' else dict(id=raw['id'],adapter='none' if raw['id']=='B0' else 'both',engine_profile='standard',operation='route')
                        authoritative=q.summarize(arm,path.parent,f.read_json(path),raw['invocation_wall_seconds'],raw['invocation_cpu_seconds'])
                        if authoritative['accepted_in_receipt']:require(authoritative['receipt_verified'] is True,'accepted receipt failed shared readback')
                        bind_row(raw,authoritative);row['checked_receipt_summary']=authoritative
                        paths.append((raw['id'],path,None))
                    else:require(raw['accepted'] is False,'accepted arm has no receipt')
            for label,path,parent in paths:
                require(base in path.parents and path.name=='result.json','receipt escaped this matrix')
                data=f.read_json(path);folder=path.parent
                require(data['tools']==protocol['freeze']['tools'] and data['source_hashes']==hashes and data['source']==str(board),'candidate source/tools differ')
                if data.get('accepted') is True:p.check_result(path)
                elif not (data.get('candidate_sha256') and data.get('native_report_sha256')):
                    result.setdefault('unqualified_receipts',[]).append(dict(id=label,status=data['status'],reason='incomplete final candidate; raw workers and completed Native observations retained'))
                result['workers'].extend(workers(folder,data,board,hashes,original))
                if label=='C_chains':
                    from autorouter.strategy import check_chain_context
                    if data.get('accepted') is True or data.get('candidate_sha256') or 'chain_pad_context' in data or (folder/'chain-context').exists():
                        check_chain_context(folder,data)
                    else:
                        require(data.get('accepted') is False,'chains outcome without context was accepted')
                        result.setdefault('unqualified_receipts',[]).append(dict(id=label,status=data['status'],reason='stopped before chain context/final candidate; actual failed workers retained'))
                resource_error=resource_failure(folder,data)
                if resource_error:result.setdefault('unqualified_receipts',[]).append(dict(id=label,status=data['status'],reason=resource_error))
                if data.get('candidate_sha256') and data.get('native_report_sha256'):
                    result['final_candidates'].append(dict(id=label,status=data['status'],**candidate(folder,data,board,original,hashes,baseline,resource_error=resource_error)))
                if label in ('C_feedback','C_chains') and data.get('incumbent'):
                    inc_folder=folder/'incumbent';inc=f.read_json(inc_folder/'result.json');marker=data['incumbent']
                    require(marker['receipt']==str(inc_folder/'result.json') and all(marker.get(k)==inc.get(k) for k in ('status','accepted','metrics','wall_seconds')),'C incumbent marker differs')
                    require(all(inc.get(k)==data.get(k) for k in ('source','source_hashes','tools'))
                        and [dict(step,phase='incumbent') for step in inc.get('steps',[])]==[step for step in data['steps'] if step.get('phase')=='incumbent'],'C own incumbent lineage differs')
                    inc_resource=resource_failure(inc_folder,inc)
                    if inc.get('candidate_sha256') and inc.get('native_report_sha256'):
                        if resource_error is None and inc_resource is None:
                            shared.pruning_incumbent_readback(folder,data,board,original,hashes)
                        result['final_candidates'].append(dict(id=label+'/incumbent',status=inc['status'],**candidate(inc_folder,inc,board,original,hashes,baseline,resource_error=inc_resource)))
                    else:result.setdefault('unqualified_receipts',[]).append(dict(id=label+'/incumbent',status=inc['status'],reason='incomplete final candidate; raw worker observations retained'))
                    for trial in data.get('trials',[]):
                        child=folder/'trials'/trial['id'];record=f.read_json(child/'result.json')
                        require(trial['receipt']==str(child/'result.json') and all(trial[k]==record[k] for k in ('id','status','accepted')),'pruning trial escaped or differs from parent')
                        trial_resource=resource_failure(child,record,data)
                        if record.get('candidate_sha256') and record.get('native_report_sha256'):
                            result['final_candidates'].append(dict(id=label+'/'+trial['id'],status=record['status'],**candidate(child,record,board,original,hashes,baseline,parent=data,resource_error=trial_resource)))
                        else:result.setdefault('unqualified_receipts',[]).append(dict(id=label+'/'+trial['id'],status=record['status'],reason='incomplete final candidate; raw worker observations retained'))
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
        final_charged_results=final_rows,comparisons=comparisons(final_rows) if result['comparison_eligible'] else [],
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
    raise SystemExit(0 if result['status']=='completed' and result['comparison_eligible'] is True else 2)
