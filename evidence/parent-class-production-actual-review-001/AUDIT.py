"""Read only the fixed completed CLI integration; no native or Git calls."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[2];OWN=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,floor_route as f,sexpr as sx,placement_clearance as io,handoff as h
from experiments.netclass_parent_transport_v1 import fixture
BASE=ROOT/'.runs/parent-class-production-native-001'

def witness(path):
    files,dirs=io.inventory(path,max_bytes=40*1024**2,max_files=2048,max_entries=4096,with_directories=True)
    return {'files':files,'directories':list(dirs)}
def canonical_digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def main():
    started=time.monotonic();cpu0=h.cpu_seconds();before=witness(BASE)
    execution=f.read_json(BASE/'execution.json')
    current={str(x.relative_to(ROOT)):p.sha(x) for x in sorted((ROOT/'autorouter').glob('*.py'))}
    assert current==execution['tools']['implementation_sha256']
    assert execution['tools']['git_head']=='c16d02efedc4e88cf297fa623f01d2ac3451806a'
    assert execution['accepted'] is False and execution['production_cli_qualified'] is True and execution['status']=='qualified'
    cases=[];total_steps=0
    with mock.patch.object(subprocess,'run',side_effect=AssertionError('No subprocess permitted')),mock.patch.object(subprocess,'Popen',side_effect=AssertionError('No subprocess permitted')):
        for name,partial in [('whole_unprotected',False),('partial_protected',True)]:
            directory=BASE/name;receipt=directory/'result.json';data=f.read_json(receipt)
            checked=p.check_result(receipt)
            assert checked['current'] is True and checked['applied'] is False
            source=Path(data['source']);candidate=Path(data['candidate']);original=sx.read(source)
            source_before=witness(source.parent)
            expected,recipe=fixture.prepare(protected=partial)
            assert io.inventory(source.parent,contents=True)==expected
            assert p.tree_hash(source.parent)==data['source_hashes']==execution['sources_before_after'][name]
            protected=p.protected_for_record(data,original)
            assert len(protected)==int(partial)
            assert data['scope']==('partial_completion' if partial else 'whole_board_unlocked_routing')
            assert data['accepted'] is True and data['netclass_policy']['mode']=='native-parent-dimensions-v1'
            assert data['schematic_parity']=='unavailable: no native schematic in source project'
            assert data['baseline']=='completion_only_probe' and data['adapter']=='both' and data['engine_profile']=='completion-only'
            assert p.sha(receipt)==execution['results'][name]['result_sha256']
            assert data['candidate_sha256']==p.sha(candidate)==execution['results'][name]['candidate_sha256']
            assert data['native']==execution['results'][name]['native'] and data['metrics']==execution['results'][name]['metrics']
            p.check_resource_accounting(data)
            assert [x['name'] for x in data['steps']]==['source-drc','export','obstacles','engine','import','refill-drc','final-netclasses','final-drc','metrics']
            total_steps+=len(data['steps'])
            for stage,action,target,args in [
                ('export','export',directory/'task.dsn',[directory/'export-netclasses.json']),
                ('obstacles','obstacles',directory/'obstacles.json',[]),
                ('import','import',directory/'imported.kicad_pcb',[directory/'routes.ses']),
                ('final-netclasses','netclasses',directory/'final-netclasses.json',[]),
                ('metrics','metrics',directory/'metrics.json',[])]:
                f.process_check(directory,data,stage,[str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),action,str(candidate),str(target),*[str(x) for x in args]])
            f.process_check(directory,data,'engine',p.engine_argv(directory,data['engine_budget']['argv']))
            # Shared checker already validates final mode/DSN/process lineage;
            # these explicit shared checks also bind original and saved refill.
            source_native=f.check_drc_stage(directory,data,'source-drc',directory/'snapshot'/source.name,directory/'source-drc-input'/source.name,False,data['source_hashes'],sandboxed=False)
            assert source_native==data['source_drc'] and source_native['opens']==3 and source_native['blocking']==0 and source_native['exclusions']==0
            if partial:
                warnings=[x for x in source_native['findings'] if x['severity']=='warning']
                assert source_native['warnings']==1 and len(warnings)==1 and warnings[0]['type']=='track_dangling'
                assert warnings[0]['items'][0]['uuid']==recipe['protected_route']['uuid']
            else:assert source_native['warnings']==0
            import_audit={};before_refill=p.transplant_routes(original,sx.read(directory/'imported.kicad_pcb'),protected=protected,audit=import_audit,policy='exact_non_uuid_lock_position_v2')
            before_refill_hash=dict(data['source_hashes']);before_refill_hash[source.name]=hashlib.sha256((sx.dump(before_refill)+'\n').encode()).hexdigest()
            refill=directory/'refill'/source.name
            refill_native=f.check_drc_stage(directory,data,'refill-drc',refill,refill,True,before_refill_hash,sandboxed=False)
            rebuilt=p.transplant_fill(before_refill,sx.read(refill))
            assert (sx.dump(rebuilt)+'\n').encode()==io.read_bytes(candidate)
            assert p.immutable(sx.read(candidate))==p.immutable(original)
            if partial:
                expected_import={'imported_sha256':p.sha(directory/'imported.kicad_pcb'),**import_audit}
                assert data['protected_route_import']==expected_import
                assert protected[0] in p.routes(sx.read(candidate))
            dimensions=p.audit_route_dimensions(sx.read(candidate),protected,f.read_json(directory/'final-netclasses.json'))
            assert dimensions==f.read_json(directory/'final-netclass-audit.json')['route_dimensions']
            assert len(data['netclass_export_audit']['classes'])==len(data['netclass_task_audit']['classes'])==3
            assert data['netclass_export_audit']['membership']==data['netclass_task_audit']['membership']
            assert p.native_accepted(refill_native) and refill_native['warnings']==0
            assert all(data['native'][k]==0 for k in ['opens','blocking','warnings','exclusions'])
            assert witness(source.parent)==source_before
            rows=[]
            for command in execution['commands']:
                if not command['name'].startswith(name+'-'):continue
                stored=f.read_json(BASE/(command['name']+'-process.json'))
                assert stored==command and command['status']=='success' and command['exit_code']==0 and command['cleanup_complete'] is True
                assert command['cwd']==str(BASE) and command['log']==str(BASE/(command['name']+'.log'))
                assert command['log_truncated'] is False and len(io.read_bytes(Path(command['log'])))==command['log_bytes']
                prefix=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B','-m','autorouter']
                expected_argv=(prefix+['route',str(source),'--output',str(directory),'--seconds','120','--adapter','both','--profile','completion-only']+(['--keep-existing'] if partial else [])) if command['name'].endswith('-route') else prefix+['check-result',str(receipt)]
                assert command['argv']==expected_argv
                rows.append({'name':command['name'],'wall_seconds':command['wall_seconds'],'cpu_seconds':command['cpu_seconds'],'argv':command['argv']})
            assert len(rows)==2
            cases.append({'case':name,'central_check':checked,'source_hashes':data['source_hashes'],'source_native':source_native,
                'native':data['native'],'metrics':data['metrics'],'route_dimensions':dimensions,'protected_import':data.get('protected_route_import'),
                'netclass_policy':data['netclass_policy'],'export_classes':data['netclass_export_audit']['classes'],
                'candidate_sha256':p.sha(candidate),'receipt_sha256':p.sha(receipt),'native_report_sha256':p.sha(directory/'final-drc.json'),
                'receipt_wall_seconds':data['wall_seconds'],'receipt_full_cpu_seconds':data['total_cpu_seconds'],
                'stage_count':len(data['steps']),'cli_commands':rows})
    assert total_steps==18 and len(execution['commands'])==4
    assert sum(x['wall_seconds'] for x in execution['commands'])<=execution['charged_wall_seconds']<=180
    assert sum(x['cpu_seconds'] for x in execution['commands'])<=execution['lifetime_full_cpu_seconds']<=180
    assert witness(BASE)==before
    assert {str(x.relative_to(ROOT)):p.sha(x) for x in sorted((ROOT/'autorouter').glob('*.py'))}==current
    result={'schema':1,'status':'passed','native_executed_by_reviewer':False,'git_or_network_calls':False,
        'actual_head':execution['tools']['git_head'],'core_sha256':current,'cases':cases,'total_retained_route_stages':total_steps,
        'outer_charged_wall_seconds':execution['charged_wall_seconds'],'outer_lifetime_full_cpu_seconds':execution['lifetime_full_cpu_seconds'],
        'source_and_result_trees_unchanged':True,'complete_input_witness':before,'input_witness_sha256':canonical_digest(before),
        'execution_sha256':p.sha(BASE/'execution.json'),'review_wall_seconds':time.monotonic()-started,'review_full_cpu_seconds':h.cpu_seconds()-cpu0,
        'limitations':['one exposed owned diagnostic geometry; two routing scopes, not independent families','no schematic exists; parity unavailable','no parent C/baseline comparative gain, selected multiclass, GUI, human or physical qualification']}
    (OWN/'actual-readback-002.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','total_retained_route_stages','outer_charged_wall_seconds','outer_lifetime_full_cpu_seconds','review_wall_seconds','review_full_cpu_seconds']}))

if __name__=='__main__':main()
