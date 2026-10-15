"""Generic frozen native chain-ablation matrix readback. No Native/JVM/engine calls or pcbnew import."""
from pathlib import Path
import time
START=time.monotonic()
CPU0=time.process_time()
import sys
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT))
import copy
import hashlib
from autorouter import pipeline as p, floor_route as f, placement_clearance as pc
from autorouter import config as c, handoff as h, sexpr as sx, local_settings as ls
from experiments.native_paired_v1 import readback as shared
from scripts import experiment_paired as paired, experiment_quality as q
CPU0+=f.child_cpu()
CONTINUATION=ROOT/'.runs/arcdice-chain-native300-readback002-protocol.json'
ARMS=['B0','B1','B2_portfolio','C_feedback','C_chains']
CHAIN_ARM=paired.CHAIN_ARM
CAP=90.;DELIVERED=300.;STARTUP=1.;PUBLICATION=2.
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


def check_observations(directory,data,authoritative,raw):
    """Replay all semantic fields exactly; a final-only sample precedes enclosing checks.
    Its time is an upper bound on route completion, not the final delivered cost.
    Frozen paired summary/invocation/outer inventories separately bind its literal bytes.
    True pruning checkpoints have exact replay, including their original times/hashes.
    """
    replay=dict(authoritative,accepted=raw['accepted']);bounds=None
    saved=raw.get('observations',[])
    if authoritative['operation'] not in ('prune','placement_prune') and authoritative['accepted_in_receipt']:
        require(type(saved) is list and len(saved)==1 and type(saved[0]) is dict,'final-only observation population differs')
        sample=saved[0];bounds={}
        for observed,receipt,enclosing in (('elapsed_seconds','wall_seconds','invocation_wall_seconds'),('observed_cpu_seconds','total_cpu_seconds','invocation_cpu_seconds')):
            low=number(data[receipt]);value=number(sample.get(observed));high=number(raw[enclosing])
            require(low<=value<=high,'final-only observation is outside receipt/enclosing costs: '+observed)
            replay[enclosing]=value
            bounds[observed]=dict(receipt_lower_bound=low,saved_sample=value,enclosing_upper_bound=high)
    expected=q.observations(directory,data,replay)
    require(f.canonical(saved)==f.canonical(expected),'raw observations differ from exact checkpoints/receipt semantic replay')
    return bounds


def matrix_material(base):
    files,directories=pc.inventory(base,max_bytes=128*1024**2,max_files=10000,max_entries=20000,with_directories=True)
    return ({n:v for n,v in files.items() if n!='execution.json'},directories)


def comparisons(rows):
    return paired.comparisons(rows)


def canonical_run_path(value, *, existing=True):
    path=h.real_path(value,existing=existing)
    require(Path(value).is_absolute() and str(path)==str(value) and ROOT/'.runs' in path.parents,'evidence path is outside canonical .runs or not canonical')
    return path


def inventory_digest(path):
    return hashlib.sha256(f.canonical(inventory(path)).encode()).hexdigest()


def check_source(spec,board,hashes):
    """Reuse the pinned original/source projection proof before a new matrix. Read-only."""
    gate=spec['source_gate'];source_receipt=canonical_run_path(gate['receipt']);source_review=canonical_run_path(gate['readback']);origin=source_receipt.parent
    pins=spec['pins'];require(type(pins) is dict and pins,'frozen original source proof pins required')
    required={source_receipt,source_review,ROOT/'experiments/original_project_native_v1/driver.py'}
    checked=set()
    for name,pin in pins.items():
        path=h.real_path(Path(name) if Path(name).is_absolute() else ROOT/name)
        require(ROOT in path.parents and p.sha(path)==pin,'frozen original qualification material changed: '+name)
        checked.add(path)
    require(required<=checked,'original receipt/readback/live proof helper pins absent')
    require(inventory_digest(origin)==gate['inventory_sha256'],'original qualification folder inventory differs')
    record=f.read_json(source_receipt);review=f.read_json(source_review)
    original_files=p.tree_hash(origin/'original');projection=gate['projection']
    require(type(projection) is dict and set(projection)==set(hashes)
        and len(projection.values())==len(set(projection.values()))
        and set(projection.values())==set(original_files),'native/original source projection is not a complete bijection')
    require(all(type(k) is str and type(v) is str and Path(k).as_posix()==k and Path(v).as_posix()==v
        and not Path(k).is_absolute() and not Path(v).is_absolute() and '..' not in Path(k).parts and '..' not in Path(v).parts
        and hashes[k]==original_files[v] for k,v in projection.items()),'native/original source projection bytes differ')
    require(record['project']==spec['project'] and record['original_hashes']==original_files
        and all(record.get(k) is True for k in ('original_shell_nonfill_ast_equal','all_original_route_records_exact','original_preserved')),'original source/shell proof differs')
    mini=dict(spec,limits=spec['claims_limits'])
    contract=shared.source_evidence_contract(mini,record,review,p.sha(source_receipt),p.sha(source_review),original_files,hashes)
    original_report=spec['original_native_report'];native=contract['native']
    require(record['parity_native']==native==original_report['summary']
        and record['final_native_report_sha256']==original_report['sha256']
        and Path(original_report['path'])==origin/'job/original-final.json','original raw Native baseline differs')
    require(review.get('native_reexecuted') is False and review.get('engine_executed') is False
        and review['actual_native_record_sha256']==p.sha(source_receipt)
        and review['candidate_sha256']==record['final_candidate_sha256']
        and review['native_report_sha256']==original_report['sha256'],'original readback/report binding differs')
    # Reuse the original saved-refill/full-schematic checks and exact shell
    # comparison; do not infer electrical or production admission from them.
    from experiments.original_project_native_v1.driver import route_records
    source=origin/'original'/projection[board.name];tree=sx.read(source)
    final=origin/'candidate'/board.name;saved=origin/'saved'/board.name;job=origin/'job'
    require(record['final_candidate']==str(final) and p.sha(final)==record['final_candidate_sha256'],'original final path/hash differs')
    require(p.immutable(sx.read(final))==p.immutable(tree) and route_records(sx.read(final))==route_records(tree),'original shell/route records differ')
    p.verify_candidate_files(final,p.tree_hash(source.parent),record['final_candidate_sha256'])
    for name,native_board,saved_flag,key in (('original-refill',saved,True,'original_native'),('original-final',final,False,'parity_native')):
        binding=f.read_json(job/(name+'-binding.json'))
        observed=f.check_drc_stage(job,record,name,native_board,native_board if saved_flag else job/(name+'-input')/board.name,
            saved_flag,binding['before'],schematic_parity=not saved_flag)
        require(observed==record[key],'original retained Native stage differs')
    declared=set()
    for step in record['steps']:
        name=step['name'];require(Path(name).name==name and name not in declared,'unsafe/duplicate original worker')
        declared.add(name);f.process_check(job,record,name,step['argv'],allowed=(0,5))
    actual={Path(n).name[:-len('-process.json')] for n in inventory(origin)[0] if n.endswith('-process.json')}
    require(actual==declared and inventory_digest(origin)==gate['inventory_sha256'],'original worker population/material differs')
    return contract


def audit(prospective,output):
    prospective=canonical_run_path(prospective);output=canonical_run_path(output,existing=False)
    spec=f.read_json(prospective);base=canonical_run_path(spec['output']);run=base/'run'
    require(type(spec.get('schema')) is int and spec['schema']==1 and spec['status']=='frozen'
        and type(spec['project']) is str and spec['arm_order']==ARMS,'prospective five-arm identity differs')
    require(spec['limits']==dict(reader=90,delivered=300,inner=120,outer=800,output=128*1024**2),'prospective limits differ')
    continuation=f.read_json(CONTINUATION)
    require(continuation['status']=='frozen' and continuation['old_protocol_sha256']==p.sha(prospective)
        and continuation['reader_source']==str(Path(__file__).resolve()) and continuation['reader_sha256']==p.sha(Path(__file__))
        and p.sha(Path(spec['reader_source']))==spec['reader_sha256'],'explicit missing-only reader continuation differs')
    require(p.sha(base/'execution.json')==continuation['outer_sha256'],'completed Native enclosure changed')
    dependencies=spec['reader_dependencies_sha256']
    require(type(dependencies) is dict and set(dependencies)=={'experiments/native_paired_v1/readback.py','experiments/native_paired_v1/observations.py'}
        and all(type(v) is str and len(v)==64 and all(ch in '0123456789abcdef' for ch in v) for v in dependencies.values()),'reader dependency pins differ')
    common=spec['shared_original_qualification_cost']
    prep=spec['source_preparation_cost']
    require(type(prep.get('scope')) is str and prep['scope'],'source preparation cost scope missing')
    common_wall=number(common['wall_seconds'])+number(prep['wall_seconds']);common_cpu=number(common['full_cpu_seconds'])+number(prep['full_cpu_seconds'])
    common_wall+=number(continuation['failed_reader_charge']['wall_seconds'])+number(continuation['repair_preparation_cost']['wall_seconds'])
    common_cpu+=number(continuation['failed_reader_charge']['full_cpu_seconds'])+number(continuation['repair_preparation_cost']['full_cpu_seconds'])
    gate=spec['source_gate'];source_receipt=canonical_run_path(gate['receipt']);source_review=canonical_run_path(gate['readback'])
    origin=source_receipt.parent
    require(output!=base and base not in output.parents and output not in base.parents
        and origin not in output.parents and output not in origin.parents,'reader destination overlaps source qualification or matrix')
    board,family=q.selected_source(spec['project']);board=h.real_path(board)
    require(board.parent not in output.parents and output not in board.parents,'reader destination overlaps live source')
    original=p.preflight(board);hashes=p.tree_hash(board.parent)
    require(spec['source']==str(board) and spec['family']==family and spec['source_hashes']==hashes,'source identity differs')
    def prerequisites():
        return check_source(spec,board,hashes)
    source_contract=prerequisites()
    require(output!=source_review.parent and source_review.parent not in output.parents and output not in source_review.parents,'reader output overlaps original readback')
    outer=f.read_json(base/'execution.json');summary=f.read_json(run/'paired-summary.json');protocol=f.read_json(run/'protocol.json')
    rows=summary['results']
    require(spec['freeze']==protocol['freeze'] and spec['tools']==protocol['freeze']['tools']
        and spec['git_head']==spec['tools']['git_head'],'freeze/tools differ')
    require(protocol['source']==str(board) and protocol['family']==family and protocol['arm_order']==ARMS and protocol['paired_system']=='native-all'
        and protocol['include_chain_ablation'] is True and protocol['system_contracts']==[paired.C_ARM,CHAIN_ARM]
        and protocol['external_reserve_seconds']==0 and protocol['wall_budget_per_arm_seconds']==protocol['cpu_budget_per_arm_seconds']==120
        and 60<=number(protocol['inner_allowance_seconds'])<=120,'paired contract differs')
    require(type(spec.get('include_chain_ablation')) is bool and spec['include_chain_ablation'] is True,'prospective chain ablation was not explicit')
    require(summary['protocol_sha256']==p.sha(run/'protocol.json') and [r['id'] for r in rows]==ARMS,'five-arm population differs')
    for key,path in (('protocol_sha256',prospective),('paired_summary_sha256',run/'paired-summary.json'),('paired_protocol_sha256',run/'protocol.json')):
        require(outer[key]==p.sha(path),'outer witness differs: '+key)
    require(outer['tools']==spec['tools'] and outer['git_head']==spec['git_head'],'outer tools/HEAD differ')
    for kind in ('reader','controller'):
        require(outer[kind+'_sha256']==spec[kind+'_sha256'] and p.sha(canonical_run_path(spec[kind+'_source']))==spec[kind+'_sha256'],'frozen '+kind+' differs')
    process=outer['process'];require(process['cleanup_complete'] is True and process.get('log_truncated') is False,'outer cleanup/log unconfirmed')
    expected_argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/experiment_paired.py'),'--project',spec['project'],
        '--system','native-all','--chain-ablation','--external-reserve-seconds','0','--output',str(run)]
    require(process['argv']==expected_argv and process['cwd']==str(base) and process['log']==str(base/'command.log'),'outer invocation identity differs')
    pc.read_bytes(base/'command.log',256*1024)
    require(f.canonical(outer['material'])==f.canonical(matrix_material(base)),'outer material witness differs')
    output.mkdir();owner={};h.capture_destination(owner,output)
    original_report=spec['original_native_report'];report_path=Path(original_report['path'])
    require(p.sha(report_path)==original_report['sha256'],'original baseline report changed')
    # Preserve the exact original full-schematic raw report and all findings/ignored checks.
    raw_report_copy=output/'original-native-raw.json'
    with raw_report_copy.open('xb') as stream:stream.write(pc.read_bytes(report_path,16*1024**2))
    require(p.sha(raw_report_copy)==original_report['sha256'],'raw original report copy differs')
    baseline=p.parse_report(raw_report_copy,board.name)
    raw_summary=original_report['summary']
    require(baseline==raw_summary,'original baseline raw native summary differs')
    source_witness=inventory(board.parent);material=matrix_material(base);pins={str(prospective):p.sha(prospective),str(Path(__file__).resolve()):p.sha(Path(__file__)),str(report_path):p.sha(report_path),str(raw_report_copy):original_report['sha256']}
    result=dict(schema=1,kind='native-chain-ablation-delivered300-readback-v1',accepted=False,status='incomplete',
        comparison_eligible=False,readback_failures=[],new_native_execution=False,new_engine_execution=False,source=str(board),source_hashes=hashes,
        shared_original_qualification_cost=copy.deepcopy(common),source_evidence_contract=source_contract,delivered_wall_full_cpu_budget_per_arm_seconds=300,
        prospective_protocol_sha256=p.sha(prospective),continuation_protocol_sha256=p.sha(CONTINUATION),failed_reader_charge=continuation['failed_reader_charge'],repair_preparation_cost=continuation['repair_preparation_cost'],reader_sha256=p.sha(Path(__file__)),original_native_report=original_report,
        reader_dependencies_sha256=dependencies,outer_status=copy.deepcopy(process),raw_paired_status=summary['status'],results=[],final_candidates=[],workers=[],
        project=spec['project'],family=family,claims_limits=spec['claims_limits'],
        common_interchange_safety=protocol.get('common_interchange_safety'),raw_comparisons=summary.get('comparisons',[]),
        charge_policy='Replace paired shared charge with complete enclosing overhead across all five raw invocations; charge full overhead, declared original qualification, actual reader, startup1, outer publication2 and reader publication2 to EACH arm. Frozen source acquisition/development scope is separately disclosed; no all-development-compute claim.',source_preparation_cost=copy.deepcopy(prep))
    def elapsed():return time.monotonic()-START,time.process_time()+f.child_cpu()-CPU0
    def remaining():return CAP-max(elapsed())
    result_pin=execution_pin=None
    def stable():
        # Large tool files are hashed by the shared tool verifier FIRST, never read through64MiB pc.read_bytes.
        require(p.sha(CONTINUATION)==result['continuation_protocol_sha256'],'reader continuation changed')
        for name,pin in continuation['pins'].items():require(p.sha(ROOT/name)==pin,'reader continuation bound material changed')
        require(p.tool_manifest()==spec['tools'],'current tools/implementation differ')
        q.verify_freeze(protocol['freeze'],board)
        require(prerequisites()==source_contract,'original source qualification changed')
        for name,pin in dependencies.items():
            require(p.sha(ROOT/name)==pin and p.sha(base/'reader-dependencies'/name.removeprefix('experiments/'))==pin,'shared live/captured reader dependency changed')
        require(p.sha(base/'reader.py')==spec['reader_sha256'] and p.sha(base/'controller.py')==spec['controller_sha256']
            and p.sha(base/'prospective-protocol.json')==p.sha(prospective),'captured controllers/protocol changed')
        for kind in ('reader','controller'):
            require(p.sha(canonical_run_path(spec[kind+'_source']))==spec[kind+'_sha256'],'frozen '+kind+' changed')
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
        require(remaining()>0,'reader90-second wall/fullCPU allowance exceeded')
    def account():
        wall,cpu=elapsed();total_wall=number(outer['wall_seconds']);total_cpu=number(outer['full_cpu_seconds'])
        require(sum(number(r['invocation_wall_seconds']) for r in rows)<=total_wall
            and sum(number(r['invocation_cpu_seconds']) for r in rows)<=total_cpu,'sequential invocation sums exceed enclosing costs')
        overhead_wall=max(0.,total_wall-sum(number(r['invocation_wall_seconds']) for r in rows))
        overhead_cpu=max(0.,total_cpu-sum(number(r['invocation_cpu_seconds']) for r in rows))
        valid=(result['status']=='completed' and not result.get('readback_failures') and remaining()>0 and summary['status']=='completed'
            and outer.get('source_current') is True and outer.get('clean_before') is True
            and outer.get('clean_after') is True and outer.get('passed') is True
            and max(number(outer['wall_seconds']),number(outer['full_cpu_seconds']))+PUBLICATION<=800
            and not any(k in outer for k in ('reason','final_check_error','material_error'))
            and result.get('portfolio_all_variants_attempted') is True
            and process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0)
        for row in result['results']:
            row.update(charged_wall_seconds=row['invocation_wall_seconds']+common_wall+overhead_wall+PUBLICATION+wall+STARTUP+PUBLICATION,
                charged_cpu_seconds=row['invocation_cpu_seconds']+common_cpu+overhead_cpu+PUBLICATION+cpu+STARTUP+PUBLICATION)
            within=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=DELIVERED
            row.update(within_equal300_wall_full_cpu_caps=within,accepted=valid and row['raw_paired_accepted'] and within)
            for observation in row.get('observations',[]):observation['final_delivery_accepted']=row['accepted']
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
            paths=[]
            for raw in rows:
                require(number(raw['assigned_seconds'])==number(protocol['inner_allowance_seconds']),'arm assigned allowance differs')
                require(number(raw['invocation_wall_seconds'])<=number(outer['wall_seconds']) and number(raw['invocation_cpu_seconds'])<=number(outer['full_cpu_seconds']),'arm costs exceed whole invocation')
                row=copy.deepcopy(raw);row['raw_paired_accepted']=raw['accepted'];row['accepted']=False
                if raw['id']=='B2_portfolio' and portfolio is None:require(raw['accepted'] is False,'accepted B2 has no receipt')
                result['results'].append(row)
                if raw['id']=='B2_portfolio':
                    for trial in (portfolio or {}).get('trials',[]):
                        if trial.get('result'):paths.append((f"B2/{trial['id']}",Path(trial['result']),None))
                else:
                    path=run/raw['id']/'result.json'
                    if path.exists():
                        arm=CHAIN_ARM if raw['id']=='C_chains' else paired.C_ARM if raw['id']=='C_feedback' else dict(id=raw['id'],adapter='none' if raw['id']=='B0' else 'both',engine_profile='standard',operation='route')
                        authoritative=q.summarize(arm,path.parent,f.read_json(path),raw['invocation_wall_seconds'],raw['invocation_cpu_seconds'])
                        if authoritative['accepted_in_receipt']:require(authoritative['receipt_verified'] is True,'accepted receipt failed shared readback')
                        bind_row(raw,authoritative);row['checked_receipt_summary']=authoritative
                        observation_bounds=check_observations(path.parent,f.read_json(path),authoritative,raw)
                        if observation_bounds is not None:row['final_result_observation_bounds']=observation_bounds
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
    # a fixed90s reader reservation below conservatively covers all later callbacks.
    def final_bound():
        stable()
        for row in result['results']:
            wall=number(row['invocation_wall_seconds'])+common_wall+result['replacement_shared_wall_seconds']+PUBLICATION+CAP+STARTUP+PUBLICATION
            cpu=number(row['invocation_cpu_seconds'])+common_cpu+result['replacement_shared_full_cpu_seconds']+PUBLICATION+CAP+STARTUP+PUBLICATION
            require(not row['accepted'] or max(wall,cpu)<=DELIVERED,'reader publication could exceed per-arm300')
    f.publish(output,result,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_bound)
    require(f.canonical(f.read_json(output/'result.json'))==f.canonical(result),'published reader receipt differs')
    result_pin=p.sha(output/'result.json')
    stable()
    wall,cpu=elapsed();final_rows=copy.deepcopy(result['results'])
    for row in final_rows:
        row['charged_wall_seconds']=row['invocation_wall_seconds']+common_wall+result['replacement_shared_wall_seconds']+PUBLICATION+wall+STARTUP+PUBLICATION
        row['charged_cpu_seconds']=row['invocation_cpu_seconds']+common_cpu+result['replacement_shared_full_cpu_seconds']+PUBLICATION+cpu+STARTUP+PUBLICATION
        row['within_equal300_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_cpu_seconds'])<=DELIVERED
        row['accepted']=row['accepted'] and row['within_equal300_wall_full_cpu_caps']
        for observation in row.get('observations',[]):observation['final_delivery_accepted']=row['accepted']
    p.save_json(output/'execution.json',dict(wall_seconds=wall,full_cpu_seconds=cpu,result_sha256=result_pin,
        final_charged_results=final_rows,comparisons=comparisons(final_rows) if result['comparison_eligible'] else [],
        comparison_eligible=result['comparison_eligible'],

        reader_cap_wall_full_cpu_seconds=CAP,startup_allowance_seconds=STARTUP,outer_publication_allowance_seconds=PUBLICATION,
        complete_cost_scope='Before imports through reader publication; interpreter startup separately charged1. Last small execution receipt and final proof covered by remaining90s reservation.'))
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
