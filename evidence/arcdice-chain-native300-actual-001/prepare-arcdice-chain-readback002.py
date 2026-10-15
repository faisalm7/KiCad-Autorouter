"""Missing-only reader continuation; completed Native work and failed reader stay immutable."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,ast,copy,importlib.util,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
old=R/'.runs/read-native-chain-ablation-001.py';new=R/'.runs/read-native-chain-ablation-002.py'
proto=R/'.runs/arcdice-chain-native300-readback002-protocol.json'
prior=R/'.runs/arcdice-chain-native300-002-protocol.json'
base=R/'.runs/arcdice-chain-native300-002'
failedout=R/'.runs/arcdice-chain-native300-readback-001'
failedouter=R/'.runs/arcdice-chain-native300-readback-execution-001'
s=old.read_text();s=s.replace("ARMS=['B0'", "CONTINUATION=ROOT/'.runs/arcdice-chain-native300-readback002-protocol.json'\nARMS=['B0'",1)
needle="    require(str(Path(__file__).resolve())==spec['reader_source'] and p.sha(Path(__file__))==spec['reader_sha256'],'reader source differs')"
assert s.count(needle)==1
s=s.replace(needle,"""    continuation=f.read_json(CONTINUATION)
    require(continuation['status']=='frozen' and continuation['old_protocol_sha256']==p.sha(prospective)
        and continuation['reader_source']==str(Path(__file__).resolve()) and continuation['reader_sha256']==p.sha(Path(__file__))
        and p.sha(Path(spec['reader_source']))==spec['reader_sha256'],'explicit missing-only reader continuation differs')
    require(p.sha(base/'execution.json')==continuation['outer_sha256'],'completed Native enclosure changed')""")
needle="    common_wall=number(common['wall_seconds'])+number(prep['wall_seconds']);common_cpu=number(common['full_cpu_seconds'])+number(prep['full_cpu_seconds'])"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n    common_wall+=number(continuation['failed_reader_charge']['wall_seconds'])+number(continuation['repair_preparation_cost']['wall_seconds'])\n    common_cpu+=number(continuation['failed_reader_charge']['full_cpu_seconds'])+number(continuation['repair_preparation_cost']['full_cpu_seconds'])")
s=s.replace("        prospective_protocol_sha256=p.sha(prospective),reader_sha256=p.sha(Path(__file__)),original_native_report=original_report,", "        prospective_protocol_sha256=p.sha(prospective),continuation_protocol_sha256=p.sha(CONTINUATION),failed_reader_charge=continuation['failed_reader_charge'],repair_preparation_cost=continuation['repair_preparation_cost'],reader_sha256=p.sha(Path(__file__)),original_native_report=original_report,")
s=s.replace("        require(p.tool_manifest()==spec['tools'],'current tools/implementation differ')", "        require(p.sha(CONTINUATION)==result['continuation_protocol_sha256'],'reader continuation changed')\n        for name,pin in continuation['pins'].items():require(p.sha(ROOT/name)==pin,'reader continuation bound material changed')\n        require(p.tool_manifest()==spec['tools'],'current tools/implementation differ')")
needle="""                        expected_observations=q.observations(path.parent,f.read_json(path),dict(authoritative,accepted=raw['accepted']))
                        require(f.canonical(raw.get('observations',[]))==f.canonical(expected_observations),'raw observations differ from bound checkpoints/receipt')"""
assert s.count(needle)==1
s=s.replace(needle,"                        observation_bounds=check_observations(path.parent,f.read_json(path),authoritative,raw)\n                        if observation_bounds is not None:row['final_result_observation_bounds']=observation_bounds")
helper='''def check_observations(directory,data,authoritative,raw):
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


'''
s=s.replace('def matrix_material(base):',helper+'def matrix_material(base):',1)
ast.parse(s);assert not new.exists();new.write_text(s)
launcher=(R/'.runs/run-native-chain-ablation-readback-001.py').read_text()
launcher=launcher.replace("READER=Path(spec['reader_source']);pin=p.sha(PROTOCOL)","CONT=R/'.runs/arcdice-chain-native300-readback002-protocol.json';continuation=f.read_json(CONT);contpin=p.sha(CONT)\nREADER=Path(continuation['reader_source']);pin=p.sha(PROTOCOL)")
launcher=launcher.replace("p.sha(READER)==spec['reader_sha256']","p.sha(READER)==continuation['reader_sha256']")
launcher=launcher.replace("require(p.tool_manifest()==spec['tools'],'current tools differ');q.verify_freeze(spec['freeze'],Path(spec['source']))","require(p.sha(CONT)==contpin and p.sha(Path(__file__))==continuation['controller_sha256'],'continuation source differs')\n require(p.tool_manifest()==spec['tools'],'current tools differ');q.verify_freeze(spec['freeze'],Path(spec['source']))")
launcher=launcher.replace("for name,digest in spec['pins'].items()","for name,digest in {**spec['pins'],**continuation['pins']}.items()")
launcher=launcher.replace("reader_sha256=spec['reader_sha256']","reader_sha256=continuation['reader_sha256'],continuation_protocol_sha256=contpin")
launcher=launcher.replace("protocol_sha256=pin,publication_allowance_seconds=2)","protocol_sha256=pin,continuation_protocol_sha256=contpin,publication_allowance_seconds=2)")
launcher=launcher.replace("+common['wall_seconds']+prep['wall_seconds']","+common['wall_seconds']+prep['wall_seconds']+continuation['failed_reader_charge']['wall_seconds']+continuation['repair_preparation_cost']['wall_seconds']")
launcher=launcher.replace("+common['full_cpu_seconds']+prep['full_cpu_seconds']","+common['full_cpu_seconds']+prep['full_cpu_seconds']+continuation['failed_reader_charge']['full_cpu_seconds']+continuation['repair_preparation_cost']['full_cpu_seconds']")
control=R/'.runs/run-native-chain-ablation-readback-002.py';ast.parse(launcher);assert not control.exists();control.write_text(launcher)
# Actual-record authority controls. Overall matrix pins also disallow even within-range sample edits.
ms=importlib.util.spec_from_file_location('arc_chain_observation002',new);m=importlib.util.module_from_spec(ms);ms.loader.exec_module(m)
summary=f.read_json(base/'run/paired-summary.json');raw=next(x for x in summary['results'] if x['id']=='B1');directory=base/'run/B1';data=f.read_json(directory/'result.json')
authority=dict(raw,operation='route',accepted_in_receipt=True)
bounds=m.check_observations(directory,data,authority,raw);checks={}
for mode in ('metrics','kind','acceptance','meaning','extra_field','below_receipt_wall','above_invocation_cpu','nonfinite','missing_observation'):
    changed=copy.deepcopy(raw);ob=changed['observations'][0]
    if mode=='metrics':ob['metrics']['vias']+=1
    elif mode=='kind':ob['kind']='incumbent_validated'
    elif mode=='acceptance':ob['final_delivery_accepted']=False
    elif mode=='meaning':ob['meaning']='exact native success time'
    elif mode=='extra_field':ob['other']=True
    elif mode=='below_receipt_wall':ob['elapsed_seconds']=data['wall_seconds']-1
    elif mode=='above_invocation_cpu':ob['observed_cpu_seconds']=raw['invocation_cpu_seconds']+1
    elif mode=='nonfinite':ob['elapsed_seconds']=float('nan')
    else:changed['observations']=[]
    try:m.check_observations(directory,data,authority,changed)
    except p.Rejected as exc:checks[mode]=str(exc)
    else:raise AssertionError('observation authority mutation accepted: '+mode)
for arm in ('B0','C_feedback','C_chains'):
    rawarm=next(x for x in summary['results'] if x['id']==arm);folder=base/'run'/arm;record=f.read_json(folder/'result.json')
    m.check_observations(folder,record,dict(rawarm,operation='prune' if arm.startswith('C_') else 'route',accepted_in_receipt=record['accepted']),rawarm)
    if arm.startswith('C_'):
        changed=copy.deepcopy(rawarm);changed['observations'][0]['elapsed_seconds']+=.001
        try:m.check_observations(folder,record,dict(rawarm,operation='prune',accepted_in_receipt=True),changed)
        except p.Rejected as exc:checks[arm+'_checkpoint_time']=str(exc)
        else:raise AssertionError('changed exact checkpoint time accepted')
controls=R/'.runs/arcdice-chain-readback002-authority-controls.json'
p.save_json(controls,dict(passed=True,bounds=bounds,rejected_mutations=checks,new_native_execution=False,new_engine_execution=False,scope='Exact semantic replay and bounds on actual frozen records. Overall raw summary/invocation/outer pins additionally forbid all sample byte changes, even inside these numeric bounds.'))
failed=f.read_json(failedouter/'execution.json');assert failed['passed'] is False
names=[old,Path(__file__),R/'.runs/run-native-chain-ablation-readback-001.py',failedouter/'execution.json',failedouter/'command.log',failedout/'result.json',failedout/'execution.json',controls,base/'run/paired-summary.json',base/'run/B1-invocation.json']
assert not proto.exists()
p.save_json(proto,dict(schema=1,status='frozen',kind='missing-only-Arc-fivearm-observation-time-reader',old_protocol_sha256=p.sha(prior),outer_sha256=p.sha(base/'execution.json'),reader_source=str(new),reader_sha256=p.sha(new),controller_source=str(control),controller_sha256=p.sha(control),pins={str(x.relative_to(R)):p.sha(x) for x in names},failed_reader_charge=dict(wall_seconds=failed['wall_seconds']+3,full_cpu_seconds=failed['full_cpu_seconds']+3,scope='Whole failed001 enclosure plus startup1/publication2, charged to EACH method; no Native rerun.'),repair_preparation_cost=dict(wall_seconds=time.monotonic()-START+3,full_cpu_seconds=cpu()-CPU0+3,scope='Whole missing-reader preparation before imports through controls and freeze, plus startup1/publication2 each method; source-repair development and read-only research separately disclosed.'),fix='Only final_result_only saved sample times are replayed inside exact receipt<=sample<=enclosing bounds. All semantic fields and true checkpoint times/hash bytes remain exact. Frozen original matrix/source/controllers/Native evidence unchanged.'))
print(json.dumps(dict(protocol_sha256=p.sha(proto),controls=len(checks),reader_sha256=p.sha(new),controller_sha256=p.sha(control))))
