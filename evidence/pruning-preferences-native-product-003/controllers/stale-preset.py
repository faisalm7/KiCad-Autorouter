"""Actual native incumbent plus explicit preset-edit fault injection; no routing mock."""
import time,resource
START=time.monotonic();u=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN);CPU0=u.ru_utime+u.ru_stime+ch.ru_utime+ch.ru_stime
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import strategy as s,pipeline as p,preferences as pref,floor_route as f
from scripts import experiment_quality as q
from experiments.native_paired_v1.readback import pruning_incumbent_readback
out=ROOT/'.runs/native-pruning-preset-stale-002';out.mkdir();board=q.selected_source('push-button-led')[0];source=p.tree_hash(board.parent)
preset=out/'settings.json';config=dict(pref.DEFAULTS);config.update(adapter='both',profile='tuned',seconds=120,scoring_preference='via_high');p.save_json(preset,config)
original=p.route;events=[]
def after_actual_route(*args,**kwargs):
    result=original(*args,**kwargs)
    events.append(dict(phase='after_actual_incumbent_return',status=result['status'],accepted=result['accepted'],receipt=str(Path(args[1])/'result.json'),preset_before_sha256=p.sha(preset)))
    changed=dict(config,seconds=121);p.save_json(preset,changed);events[-1]['preset_after_sha256']=p.sha(preset)
    return result
p.route=after_actual_route
try:result=s.prune(board,out/'run',settings_path=preset,proposal_policy='feedback')
finally:p.route=original
assert p.tree_hash(board.parent)==source and result['accepted'] is False
assert len(events)==1 and events[0]['accepted'] is True and 'preferences changed' in result['reason']
assert not (out/'run/candidate').exists()
with p.validation_readback_session():
    inc,checked=pruning_incumbent_readback(out/'run',result,board,p.preflight(board),source)
assert checked['native_counts']['opens']==checked['native_counts']['blocking']==0
u=resource.getrusage(resource.RUSAGE_SELF);ch=resource.getrusage(resource.RUSAGE_CHILDREN)
record=dict(schema=1,passed=True,accepted=False,events=events,status=result['status'],reason=result['reason'],actual_incumbent_native=checked,source_hashes=source,
    controller_sha256=p.sha(Path(__file__)),result_sha256=p.sha(out/'run/result.json'),wall_seconds=time.monotonic()-START,full_cpu_seconds=u.ru_utime+u.ru_stime+ch.ru_utime+ch.ru_stime-CPU0,
    scope='Delegates to actual unchanged pipeline.route/native workers, then deliberately edits one owned externalpreset after real validated incumbent. No routing/validation/result mocks. Production pruning must reject and emit no finalcandidate. Complete source remains immutable; no comparative routing/physical claim.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k]for k in ('passed','status','reason','wall_seconds','full_cpu_seconds')}))
