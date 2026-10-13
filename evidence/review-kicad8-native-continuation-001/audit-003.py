"""Read-only audit of actual continuation; no subprocess/native execution."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
import hashlib,json,math,sys,time
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx,floor_route as f,placement_clearance as pc
from experiments.kicad8_native_compat_continuation_v1 import driver as d
HERE=Path(__file__).resolve().parent;OUT=ROOT/'.runs/kicad8-native-compat-continuation-001';RUN=OUT/'run';CASE=RUN/'ideal_diode'
guards=[]
def guard(test,name):
    if test is not True:raise AssertionError(name)
    guards.append(name)
def sha(path):return hashlib.sha256(pc.read_bytes(path,512*1024**2)).hexdigest()
def tree(path):return pc.inventory(path,max_bytes=512*1024**2,max_files=16000,max_entries=32000,with_directories=True)
def ast_sha(value):return hashlib.sha256((sx.dump(value)+'\n').encode()).hexdigest()
def route_map(board):
    nodes=p.routes(board);result={};order=[]
    for index,node in enumerate(nodes):
        identifiers=sx.children(node,'uuid');guard(len(identifiers)==1 and len(identifiers[0])==2,'route'+str(index)+' exactly one UUID')
        identifier=sx.unquote(identifiers[0][1]);guard(bool(identifier) and identifier not in result,'route'+str(index)+' unique nonempty UUID')
        guard(node[0] in {'segment','via'},'route'+str(index)+' observed route type')
        result[identifier]=node;order.append(identifier)
    return result,order
def main():
    begin=time.monotonic();cpu=time.process_time();before=tree(OUT);summary=f.read_json(RUN/'summary.json');execution=f.read_json(OUT/'execution.json');row=f.read_json(CASE/'case.json')
    protocol=f.read_json(RUN/'code/experiments/kicad8_native_compat_continuation_v1/PROTOCOL.json');source=ROOT/protocol['source'];source_before=tree(source.parent)
    with patch.object(p.subprocess,'run',side_effect=AssertionError('subprocess execution forbidden')):
        guard(summary['status']=='failed' and summary['observations_complete'] is False and summary['original_inputs_unchanged'] is None,'original failed controller unchanged')
        guard(summary['error']=='Rejected: native saved/reloaded non-fill geometry or routes differ','exact frozen failure reason')
        guard(row==summary['case'] and row['status']=='failed' and row['observations_complete'] is False,'stored case exact failed summary binding')
        for key in d.FALSE_FLAGS:guard(summary[key] is False and row[key] is False,'unqualified '+key)
        guard(p.sha(RUN/'code/experiments/kicad8_native_compat_continuation_v1/PROTOCOL.json')==summary['protocol_sha256'],'protocol hash bound')
        guard(d.inventory(RUN/'code')==summary['code_inventory'],'complete retained code inventory')
        for name,value in summary['runtime_sources'].items():
            guard(sha(ROOT/name)==value and sha(RUN/'code'/name)==value,'runtime/snapshot '+name)
        guard(summary['tools']['git_head']==execution['git_head']=='3f757c032beb4c9ff36c21e70ad2f657771da445','recorded checkpoint binding no new Git verification')
        for path,value in summary['tools']['files'].items():guard(sha(Path(path))==value,'actual installed tool hash '+Path(path).name)
        for name,value in summary['tools']['implementation_sha256'].items():guard(summary['runtime_sources'][name]==value,'implementation provenance '+name)
        prefix=d.prefix_readback(protocol);guard(prefix==summary['prefix'],'fully pinned old13 process/control readback')
        for rel,expected in protocol['original_trees'].items():guard(d.inventory(ROOT/rel)==expected,'complete original/notices '+rel)
        receipt=f.read_json(ROOT/protocol['acquisition_receipt']);guard(sha(ROOT/protocol['acquisition_receipt'])==protocol['acquisition_receipt_sha256'],'acquisition receipt pin')
        acquired=[x for x in receipt['files'] if x['repository']=='sparkfun/SparkFun_Ideal_Diode_Breakout'];guard(len(acquired)==6,'exact six acquired source/notice blobs')
        for entry in acquired:
            raw=pc.read_bytes(ROOT/entry['local_path']);blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            guard(len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'] and blob==entry['git_blob_sha1'] and entry['commit']==protocol['source_revision'],'acquired blob '+entry['local_path'])
        hashes=d.inventory(source.parent);guard(hashes==row['source_hashes'] and sha(source)==row['source_sha256'],'source complete recorded inventory exact')
        guard(not source.with_suffix('.kicad_prl').exists(),'original has no preexisting PRL')
        try:p.preflight(source)
        except p.Rejected as exc:guard(str(exc)==summary['original_preflight_rejection']=='unsupported: unqualified board format version','production format guard retained')
        else:raise AssertionError('production preflight unexpectedly accepts')
        original=sx.read(source);candidate=CASE/'candidate'/source.name;saved=CASE/'refill'/source.name
        guard(d.inventory(CASE/'observe-input')==hashes,'original observation copy exact')
        guard(p.immutable(sx.read(candidate))==p.immutable(original),'candidate every non-route/non-fill source AST preserved')
        guard(p.routes(sx.read(candidate))==p.routes(original),'candidate original ordered full route AST preserved')
        guard((sx.dump(d.prior.old_shell(original,sx.read(saved)))+'\n').encode()==pc.read_bytes(candidate),'candidate exact original-shell derived-fill reconstruction')
        candidate_sha=sha(candidate);p.verify_candidate_files(candidate,hashes,candidate_sha);guard(True,'candidate complete project original rules/nets/files except derived-fill hash')
        guard(summary['steps']==row['steps'] and [s['name'] for s in row['steps']]==list(d.STAGES) and len(row['steps'])==8,'exact eight new processes once in both histories')
        raw_processes=[];contexts=[]
        for name,board in [('original-context',CASE/'observe-input'/source.name),('saved-context',saved),('shell-context',candidate)]:
            context=f.read_json(CASE/(name+'-context.json'));f.context_binding(context,board,d.inventory(board.parent),'final',None)
            f.process_check(CASE,row,name,f.context_argv('final',board,CASE/(name+'-context.json')))
            guard(context['native_version']=='10.0.0' and context['routing_accepted'] is False and context['board_saved'] is False,'bound unchanged final native context '+name)
            guard(pc.read_bytes(CASE/(name+'.log'))==b'','actual via context warning log empty '+name)
            contexts.append(d.prior.geometry(context))
        for name,board in [('original-native',CASE/'observe-input'/source.name),('saved-native',saved),('shell-native',candidate)]:
            f.process_check(CASE,row,name,[*f.SANDBOX,str(d.prior.c.PYTHON),str(ROOT/'autorouter/native.py'),'roundtrip',str(board),str(CASE/(name+'.kicad_pcb'))]);guard(True,'actual roundtrip process/emission binding '+name)
        final=f.check_drc_stage(CASE,row,'final-drc',candidate,CASE/'final-drc-input'/source.name,False,{**hashes,source.name:candidate_sha})
        saved_drc=f.check_drc_stage(CASE,row,'refill-drc',saved,saved,True,hashes)
        for name,key,native in [('refill-drc','saved_drc',saved_drc),('final-drc','final_drc',final)]:
            guard(row[key]['native']==native and row[key]['report_sha256']==sha(CASE/(name+'.json')) and row[key]['binding_sha256']==sha(CASE/(name+'-binding.json')),'actual original-rule DRC native/report/process/input '+name)
        guard(saved_drc==final,'all saved/final findings severities exclusions/ignored checks exact')
        guard({k:final[k] for k in ('opens','blocking','warnings','exclusions')}=={'opens':0,'blocking':3,'warnings':0,'exclusions':0},'actual native counts not an accepted routing result')
        guard(p.native_accepted(final) is False,'native 3blocking reject remains visible')
        guard(all(x['type']=='courtyards_overlap' and x['severity']=='error' for x in final['findings']),'all exact blocking type/severity retained')
        for step in row['steps']:
            raw=f.read_json(CASE/(step['name']+'-process.json'));guard(all(step.get(k)==v for k,v in raw.items()),'raw process equals history '+step['name'])
            guard(step['cleanup_complete'] is True and step['cwd']==str(CASE),'bounded process cleanup/cwd '+step['name'])
            guard(step.get('log_truncated') is False and Path(step['log'])==CASE/(step['name']+'.log') and len(pc.read_bytes(Path(step['log'])))==step['log_bytes'],'exact actual log bytes '+step['name'])
            raw_processes.append({'name':step['name'],'status':step['status'],'exit_code':step['exit_code'],'wall_seconds':step['wall_seconds'],'cpu_seconds':step['cpu_seconds'],'process_sha256':sha(CASE/(step['name']+'-process.json')),'log_sha256':sha(CASE/(step['name']+'.log'))})
        native_trees={key:sx.read(CASE/(key+'-native.kicad_pcb')) for key in ('original','saved','shell')};maps={};orders={}
        for key,board in native_trees.items():maps[key],orders[key]=route_map(board);guard(len(maps[key])==113 and Counter(x[0] for x in maps[key].values())=={'segment':101,'via':12},key+' complete113 original route types')
        proof=[]
        for index,uid in enumerate(orders['original']):
            guard(uid in maps['saved'] and uid in maps['shell'],'original route UUID retained '+uid)
            guard(maps['original'][uid]==maps['saved'][uid]==maps['shell'][uid],'full exact perUUID route AST '+uid)
            proof.append({'uuid':uid,'type':maps['original'][uid][0],'full_ast_sha256':ast_sha(maps['original'][uid]),'original_index':index,'saved_index':orders['saved'].index(uid),'shell_index':orders['shell'].index(uid),'full_ast_equal':True})
        guard(p.immutable(native_trees['original'])==p.immutable(native_trees['saved'])==p.immutable(native_trees['shell']),'all current-native complete nonfill ASTs exactly equal')
        guard(orders['original']!=orders['saved'] and orders['original']==orders['shell'],'only saved emission route order differs; original-shell exact list unchanged')
        guard(contexts[0]==contexts[1]==contexts[2],'all final-mode actual native contexts exactly equal no differing keys')
        census=d.footprint_census(original)
        for key,board in native_trees.items():guard(d.footprint_census(board)==census,'all37 full footprint UUID/ref/padcount/attributes retained '+key)
        guard(census==row['original_native_footprint_census'] and d.duplicate_references(census)==row['original_duplicate_references'] and d.digest(f.canonical(census).encode())==row['original_native_footprint_census_sha256'],'actual census/duplicate refs raw binding')
        vias=[x for x in contexts[0]['routes'] if x['kind']=='via'];source_vias={sx.unquote(sx.one(node,'uuid')[1]):node for node in p.routes(original) if node[0]=='via'}
        guard(len(vias)==len(source_vias)==12 and all(x['width_nm']==int(Decimal(sx.one(source_vias[x['uuid']],'size')[1])*Decimal(1000000)) for x in vias),'actual explicit-layer via diameters equal each original declared diameter')
        outer=execution['process'];guard(outer['status']=='nonzero_exit' and outer['exit_code']==2 and outer['cleanup_complete'] is True,'failed actual outer process disposition')
        guard(outer['argv']==[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'experiments/kicad8_native_compat_continuation_v1/driver.py'),'--output',str(RUN),'--run-native'] and outer['cwd']==str(OUT),'exact actual outer command/cwd')
        guard(sha(OUT/'command.log')==execution['log_sha256'] and outer['log_bytes']==len(pc.read_bytes(OUT/'command.log')) and outer['log_truncated'] is False,'full outer log hash/bytes')
        for key in ('wall_seconds','full_cpu_seconds','cumulative_wall_seconds','cumulative_full_cpu_seconds'):guard(type(execution[key]) in (int,float) and math.isfinite(execution[key]) and execution[key]>=0,'finite exact outer resource '+key)
        guard(execution['cumulative_wall_seconds']==execution['wall_seconds']+prefix['prior_outer_wall_seconds'] and execution['cumulative_full_cpu_seconds']==execution['full_cpu_seconds']+prefix['prior_outer_full_cpu_seconds'],'entire failed prefix+continuation outer costs charged')
        guard(execution['cumulative_wall_seconds']<=90 and execution['cumulative_full_cpu_seconds']<=90,'actual cumulative observed90caps met without acceptance')
        guard(summary['new_wall_seconds']<=execution['wall_seconds'] and summary['new_full_cpu_seconds']<=execution['full_cpu_seconds'] and sum(x['cpu_seconds'] for x in row['steps'])<=summary['new_full_cpu_seconds'],'stored prepublication/child costs dominated by full outer accounting')
        guard(outer['sampled_peak_workdir_bytes']<=20*1024**2 and outer['resource_guards']['max_workdir_bytes']==20*1024**2 and outer['resource_guards']['os_enforced'] is False,'actual sampled20MiB guard no OS quota claim')
        guard(not any(name.endswith('.dsn') for name in d.inventory(CASE)),'no DSN request/retry output')
        guard(tree(source.parent)==source_before and tree(OUT)==before,'originals and complete actual evidence unchanged after audit')
    first=next(i for i,(a,b) in enumerate(zip(orders['original'],orders['saved'])) if a!=b)
    cleanup=f.read_json(ROOT/'.runs/review-handoff-search-cleanup-fix-001/manifest.json')
    result={'schema':1,'status':'audit_passed_original_controller_failed','native_executed':False,'subprocess_executed':False,'guard_count':len(guards),'guards':guards,
            'summary_sha256':sha(RUN/'summary.json'),'execution_sha256':sha(OUT/'execution.json'),'recorded_checkpoint':execution['git_head'],'prefix_readback':{'status':prefix['status'],'actual_native_processes':13,'summary_sha256':prefix['summary_sha256'],'execution_sha256':prefix['execution_sha256']},
            'actual_new_processes':raw_processes,'all_unique_actual_processes_with_prefix':21,'posthoc_original_complete_inventory_exact':True,'controller_original_inputs_unchanged':None,
            'native_drc_counts':{k:final[k] for k in ('opens','blocking','warnings','exclusions')},'native_drc_types':[{'type':x['type'],'severity':x['severity'],'uuid':sorted(i['uuid'] for i in x['items'])} for x in final['findings']],
            'native_ignored_check_keys':[x['key'] for x in final['ignored_checks']],'saved_final_native_exact_equal':True,
            'diagnosis':{'complete_native_nonfill_AST_exact_equal':True,'full_exact_route_ASTs_by_unique_UUID_equal':True,'source_original_route_records_retained':113,'types':{'segment':101,'via':12},'all_final_mode_contexts_exact_equal':True,
                         'original_shell_emission_order_exact_equal':True,'saved_native_list_order_exact_equal':False,'first_order_difference_index':first,'first_order_original_UUID':orders['original'][first],'first_order_saved_UUID':orders['saved'][first],
                         'routes_moved_in_list':sum(x['original_index']!=x['saved_index'] for x in proof),'per_UUID_route_proof':proof,'full_native_nonfill_AST_sha256':ast_sha(p.immutable(native_trees['original'])),
                         'native_context_geometry_sha256':d.digest(f.canonical(contexts[0]).encode()),'source_candidate_route_list_exact_equal':True,'actual_footprint_count':len(census),'duplicate_padless_reference_groups':sorted(row['original_duplicate_references']),
                         'via_uniform_diameter_nm':vias[0]['width_nm'],'via_count':12,'assert_warning_logs_empty_all_three_contexts':True},
            'costs':{k:execution[k] for k in ('wall_seconds','full_cpu_seconds','cumulative_wall_seconds','cumulative_full_cpu_seconds')},'summed_new_worker_cpu_seconds':sum(s['cpu_seconds'] for s in row['steps']),
            'retained_cleanup_fixture_symlinks':{str(ROOT/'.runs/review-handoff-search-cleanup-fix-001'/name):target for name,target in cleanup['symlinks'].items()},
            'audit_wall_seconds':time.monotonic()-begin,'audit_parent_cpu_seconds':time.process_time()-cpu,
            'scope':'No frozen failure normalization, routing/format/SES admission, native reexecution or raw board geometry publication. UUID/type/full-record hashes establish ordering-only comparison failure; full route payloads remain in original local run.'}
    (HERE/'audit-003.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('guards','diagnosis','actual_new_processes')},indent=2))
if __name__=='__main__':main()
