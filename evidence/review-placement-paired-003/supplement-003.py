"""Small actual warning/process/effective-rule supplement; reuses frozen helpers."""
from pathlib import Path
from collections import Counter
import hashlib,json,subprocess,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-paired-003/run'
sys.dont_write_bytecode=True;sys.path.insert(0,str(HERE/'frozen-import'))
from autorouter import config as c
c.ROOT=ROOT;c.JAR=ROOT/'.tools/freerouting-2.5.0.jar'
from autorouter import floor_route as f,pipeline as p,placement_clearance as pc
def forbidden(*a,**kw):raise AssertionError('no subprocess/native/Git/network')
def main():
    before=pc.inventory(RUN,max_bytes=512*1024**2,max_files=16000,max_entries=32000,with_directories=True)
    prior=f.read_json(HERE/'findings.json');rows={x['id']:x for x in prior['arms']};records={}
    with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
        for name,path in [('B0','B0'),('B1','B1'),('B2_portfolio','B2_portfolio/01-via_default'),('C_feedback','C_feedback')]:records[name]=f.read_json(RUN/path/'result.json')
        cf=records['C_feedback'];base=Counter(f.canonical(x) for x in cf['native']['findings']);warning_equal={}
        for name in ('B1','B2_portfolio'):
            other=records[name]['native'];equal=base==Counter(f.canonical(x) for x in other['findings']) and {k:v for k,v in other.items() if k!='findings'}=={k:v for k,v in cf['native'].items() if k!='findings'}
            assert equal;warning_equal[name]=equal
        floors={};effective={}
        for name,path in [('B1','B1'),('B2_portfolio','B2_portfolio/01-via_default'),('C_incumbent','C_feedback/incumbent')]:
            native=f.read_json(RUN/path/'floor-export-context.json');floors[name]=native['floors_nm']
            effective[name]={x['name']:{k:v for k,v in x.items() if k not in ('name','netcode')} for x in native['nets']}
        assert floors['B1']==floors['B2_portfolio']==floors['C_incumbent'] and effective['B1']==effective['B2_portfolio']==effective['C_incumbent']
        processes={}
        for record in records.values():
            for step in record['steps']:
                key=(step['cwd'],step['name']);assert key not in processes;processes[key]=step
        engine=[x for x in processes.values() if x['name']=='engine'];assert len(engine)==4
        def tool(step):
            argv=step['argv'];command=argv[len(f.SANDBOX):] if argv[:len(f.SANDBOX)]==f.SANDBOX else argv
            if command[0]==str(c.JAVA):assert '-jar' in command and str(c.JAR) in command;return 'freerouting_java'
            if command[0]==str(c.PYTHON):return 'pinned_native_python'
            if command[0]==str(c.CLI):return 'pinned_kicad_cli'
            raise AssertionError('unrecognized actual worker')
        tools=Counter(tool(x) for x in processes.values());assert sum(tools.values())==43
        b2=f.read_json(RUN/'B2_portfolio/portfolio-summary.json');bp=f.read_json(RUN/'B2_portfolio/protocol.json')
        assert len(b2['trials'])==1 and b2['trials'][0]['id']=='via_default' and b2['stop_reason']=='insufficient remaining budget for another attempt and reserves'
        assert cf['reference_routes_used_for_selection'] is False and cf['novel_routing_algorithm_claim'] is False
        assert pc.inventory(RUN,max_bytes=512*1024**2,max_files=16000,max_entries=32000,with_directories=True)==before
    result={'schema':1,'status':'supplement_passed','native_executed':False,'subprocesses_executed':False,
        'exact_complete_finding_multiset_and_all_other_native_fields_equal_to_C':warning_equal,
        'all_native_effective_floor_fields_equal':True,'all_per_net_effective_class_fields_equal':True,
        'effective_rule_observation_sha256':hashlib.sha256(f.canonical({'floors':floors['B1'],'nets':effective['B1']}).encode()).hexdigest(),
        'actual_unique_worker_count':len(processes),'actual_worker_types':dict(tools),'fresh_engine_workers':len(engine),'C_reference_routes_used_for_selection':False,'C_novel_routing_algorithm_claim':False,
        'model_compute_scope':'All retained actual workers are pinned Java Freerouting or native KiCad CLI/Python; no model/API worker appears. No claim about agent inference locality or subscription-free development.',
        'B2_executed_variants':[x['id'] for x in b2['trials']],'B2_declared_variants':bp['variants'],'B2_fixed_order':bp['fixed_order'],'B2_stop_reason':b2['stop_reason'],
        'actual_run_files_and_directories_unchanged':True,'full_tree_witness_sha256':hashlib.sha256(f.canonical(before).encode()).hexdigest(),
        'scope':'One exposed multichannel source, same120wall/fullCPU cap; exact warnings and effective source rules unchanged. This readback is neither native reexecution nor independent-family evidence.'}
    (HERE/'supplement-003.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
