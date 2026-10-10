"""Offline semantic tamper controls using copies of actual native evidence.

Relocated process metadata is explicitly synthetic relocation, never a new
native execution, and all original report/board/native bytes are retained.
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys,time
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT/'experiments/placement_diagnostic_v1'),str(ROOT)]
import diagnostic_route as d
p=d.p;f=d.f;g=d.g;sx=d.sx
ORIGINAL=ROOT/'.runs/placement-routing-fixture-002'


def datafiles(path):return {name:(path/name).read_bytes()for name in p.tree_hash(path)}


def rebase(value,old,new):
    if isinstance(value,str):return value.replace(str(old),str(new))
    if isinstance(value,list):return [rebase(x,old,new)for x in value]
    if isinstance(value,dict):return {rebase(k,old,new):rebase(v,old,new)for k,v in value.items()}
    return value


def execute(attempt_name):
    start=time.monotonic();cpu0=time.process_time();out=HERE/attempt_name
    if out.exists() or not attempt_name.startswith('attempt-') or '/'in attempt_name:raise ValueError('fresh owned attempt required')
    out.mkdir();work=out/'work';source=out/'source-project';cases=out/'cases';cases.mkdir()
    def bound():
        if time.monotonic()-start>60 or time.process_time()-cpu0>60:raise ValueError('offline control budget exceeded')
        total=sum(x.stat().st_size for x in HERE.rglob('*')if x.is_file())
        if total>10*1024**2:raise ValueError('10MiB review evidence ceiling')
        return total
    receipt=f.read_json(ORIGINAL/'result.json');original_source=Path(receipt['source']).parent
    before={'original_run':p.tree_hash(ORIGINAL),'original_source':p.tree_hash(original_source),'tools_and_code':p.tool_manifest(),
            'helpers':{str(x.relative_to(ROOT)):p.sha(x)for x in (ROOT/'experiments/placement_diagnostic_v1').glob('*.py')}}
    p.save_json(out/'original-bindings.json',before)
    original_verdict=d.check_result(ORIGINAL/'result.json');assert original_verdict['routing_accepted']
    shutil.copytree(ORIGINAL,work);shutil.copytree(original_source,source)
    # Only top-level process/context/receipt JSON path metadata is rebased.
    # Files inside complete project copies and frozen code remain byte exact.
    for path in work.glob('*.json'):
        if path.name in {'source-drc.json','refill-drc.json','final-drc.json','metrics.json'}:continue
        value=f.read_json(path);value=rebase(value,ORIGINAL,work)
        if path.name=='result.json':value['source']=str(source/Path(receipt['source']).name)
        p.save_json(path,value)
    record=f.read_json(work/'result.json');board_name=Path(record['source']).name
    task=sx.read(work/'floor-export-input'/board_name);native=f.read_json(work/'floor-export-context.json');raw=(work/'native.dsn').read_bytes()
    guided,contract=f.policy_contract(raw,native,(source/board_name).with_suffix('.kicad_pro').read_bytes(),task,record['source_hashes'])
    if guided!=(work/'floor-guided.dsn').read_bytes():raise ValueError('relocation changed guidance geometry')
    p.save_json(work/'floor-policy.json',contract)
    corrected,removal=d.placement.transform(d.files(work/'snapshot'),d.files(work/'floor-export-input'),board_name,f.read_json(work/'area-context.json'),raw,guided)
    if corrected!=(work/'pre-adapter.dsn').read_bytes():raise ValueError('relocation changed placement output')
    p.save_json(work/'placement-transform.json',removal)
    audit=f.read_json(work/'floor-final-audit.json');audit['native_context_sha256']=p.sha(work/'floor-final-context.json');p.save_json(work/'floor-final-audit.json',audit)
    _,_,record['chain']=d.derive(work,record['source_hashes'],record['policy'])
    record['evidence_hashes']=f.evidence_inventory(work);p.save_json(work/'result.json',record)
    positive=d.check_result(work/'result.json')
    if not positive['routing_accepted']:raise ValueError('relocated positive failed')
    baseline=datafiles(work);baseline_source=datafiles(source)
    p.save_json(out/'positive.json',{'scope':'offline rebasing of historical process/context path metadata; no new native execution','origin_receipt_sha256':p.sha(ORIGINAL/'result.json'),'relocated_receipt_sha256':p.sha(work/'result.json'),'verdict':positive,'relocated_evidence':p.tree_hash(work),'source':p.tree_hash(source)})
    results=[]
    def mutate_json(path,fn):
        value=f.read_json(path);fn(value);p.save_json(path,value)
    def step_edit(record,name,fn):
        process_path=work/(name+'-process.json');process=f.read_json(process_path);fn(process);p.save_json(process_path,process)
        row=next(x for x in record['steps']if x['name']==name)
        # Only values also in process; preserve added DRC input binding fields.
        for key,value in process.items():row[key]=value
    def stale_source(record):
        with (source/board_name).open('a')as handle:handle.write('\n; stale disposable source\n')
    def rule_severity(record):
        mutate_json(work/'candidate'/Path(board_name).with_suffix('.kicad_pro'),lambda x:x['board']['design_settings']['rule_severities'].update(track_width='warning'))
    def reidentified_rules(record):
        for directory in (source,work/'snapshot',work/'candidate'):
            mutate_json(directory/Path(board_name).with_suffix('.kicad_pro'),lambda x:x['board']['design_settings']['rule_severities'].update(track_width='warning'))
        record['source_hashes']=p.tree_hash(source)
    def placement_provenance(record):mutate_json(work/'placement-transform.json',lambda x:x.update(removed_count=0))
    def wrong_floor(record):
        (work/'floor-guided.dsn').write_bytes(raw)
        record['chain']['floor_guided_sha256']=p.sha(work/'floor-guided.dsn')
    def observer_preference(record):
        mutate_json(work/'floor-export-context.json',lambda x:x['nets'][0].update(width_nm=100000))
        record['chain']['floor_context_sha256']=p.sha(work/'floor-export-context.json')
    def observer_flags(record):
        mutate_json(work/'area-context.json',lambda x:x['zones'][0]['disallow'].update(tracks=True))
        record['chain']['area_context_sha256']=p.sha(work/'area-context.json')
    def observer_snapshot(record):
        with (work/'code/native_combined.py').open('a')as handle:handle.write('\n# tampered disposable executed snapshot\n')
        record['observer_sha256']=p.sha(work/'code/native_combined.py')
    def observer_process(record):step_edit(record,'floor-area-export',lambda x:x['argv'].__setitem__(-1,str(work/'unbound.dsn')))
    def report_change(record):
        violation={'type':'track_width','severity':'error','description':'deliberate offline semantic corruption control','items':[{'uuid':sx.unquote(sx.one(sx.children(sx.read(work/'candidate'/board_name),'segment')[0],'uuid')[1]),'description':'synthetic tamper target, not a new native finding','pos':{'x':0,'y':0}}]}
        mutate_json(work/'final-drc.json',lambda x:x['violations'].append(violation))
        record['native_report_sha256']=p.sha(work/'final-drc.json');record['native']=p.parse_report(work/'final-drc.json',board_name)
        step_edit(record,'final-drc',lambda x:x.update(exit_code=5,status='nonzero_exit'))
    def candidate_route(record):
        board=work/'candidate'/board_name;tree=sx.read(board);sx.one(sx.children(tree,'segment')[0],'width')[1]='0.2';sx.write(board,tree);record['candidate_sha256']=p.sha(board)
    def immutable_pad(record):
        board=work/'candidate'/board_name;tree=sx.read(board);sx.one(sx.children(sx.children(tree,'footprint')[0],'pad')[0],'size')[1]='2.1';sx.write(board,tree);record['candidate_sha256']=p.sha(board)
    def original_ignored_check(record):
        mutate_json(work/'final-drc.json',lambda x:x['ignored_checks'].append({'key':'clearance','description':'deliberate disabled critical check'}))
        record['native_report_sha256']=p.sha(work/'final-drc.json')
    def unsupported_engine_flag(record):step_edit(record,'engine',lambda x:x['argv'].append('--router.automatic_neckdown=true'))
    mutations=[('stale_source',stale_source),('candidate_rule_severity',rule_severity),('reidentified_original_rules',reidentified_rules),
               ('placement_removal_provenance',placement_provenance),('weaker_floor_guidance',wrong_floor),('rehashed_observer_preference',observer_preference),
               ('rehashed_observer_flags',observer_flags),('rehashed_observer_snapshot',observer_snapshot),('matched_observer_process_and_step',observer_process),
               ('rehashed_report_and_process',report_change),('rehashed_candidate_route',candidate_route),('rehashed_immutable_pad',immutable_pad),
               ('original_ignored_checks',original_ignored_check),('matched_engine_process_and_step',unsupported_engine_flag)]
    for name,mutate in mutations:
        bound()
        for relative,value in baseline.items():(work/relative).write_bytes(value)
        for relative,value in baseline_source.items():(source/relative).write_bytes(value)
        current=f.read_json(work/'result.json');mutate(current)
        current['evidence_hashes']=f.evidence_inventory(work);p.save_json(work/'result.json',current)
        destination=cases/name;destination.mkdir();changed={}
        for label,directory,original_files in [('evidence',work,baseline),('source',source,baseline_source)]:
            for relative,value in datafiles(directory).items():
                if original_files.get(relative)!=value:
                    target=destination/label/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(value);changed[label+'/'+relative]=hashlib.sha256(value).hexdigest()
        result={'case':name,'outer_inventory_rehashed':True,'changed_files_sha256':changed,'expected':'semantic rejection','native_executed':False}
        try:result.update(actual='accepted',verdict=d.check_result(work/'result.json'))
        except Exception as exc:result.update(actual='rejected',exception=type(exc).__name__,reason=str(exc))
        result['passed']=result['actual']=='rejected' and result.get('reason')!='completed diagnostic evidence changed'
        p.save_json(destination/'outcome.json',result);results.append(result)
    # Restore the one working copy to its verified positive state. All negative
    # deltas/receipts remain saved per case and can be reapplied to this baseline.
    for relative,value in baseline.items():(work/relative).write_bytes(value)
    for relative,value in baseline_source.items():(source/relative).write_bytes(value)
    restored=d.check_result(work/'result.json')
    after={'original_run':p.tree_hash(ORIGINAL),'original_source':p.tree_hash(original_source),'tools_and_code':p.tool_manifest(),
           'helpers':{str(x.relative_to(ROOT)):p.sha(x)for x in (ROOT/'experiments/placement_diagnostic_v1').glob('*.py')}}
    size=bound();summary={'status':'passed'if all(x['passed']for x in results)and before==after and restored==positive else'failed',
        'scope':'actual native receipt consistency controls with offline relocation/tampering; no authentication or new native qualification',
        'native_jobs':0,'engine_jobs':0,'positive_original':original_verdict,'positive_relocated':positive,'positive_restored':restored,
        'originals_code_tools_unchanged':before==after,'cases':results,'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu0,
        'stored_bytes':size,'byte_ceiling':10*1024**2,'time_ceiling_seconds':60,'origin_receipt_sha256':p.sha(ORIGINAL/'result.json')}
    p.save_json(out/'audit.json',summary);print(json.dumps({'status':summary['status'],'cases':len(results),'bytes':size,'wall_seconds':summary['wall_seconds']}))
    return summary

if __name__=='__main__':
    if len(sys.argv)!=3 or sys.argv[1]!='--run-controls':raise SystemExit('usage: controls.py --run-controls attempt-001')
    raise SystemExit(0 if execute(sys.argv[2])['status']=='passed' else 1)
