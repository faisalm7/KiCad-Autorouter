"""Actual retained-schema5 handoff + cleanup fault controls; no native/Git/network."""
from pathlib import Path
import ast,contextlib,hashlib,inspect,json,signal,sys,time
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/handoff.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import handoff as h,pipeline as p,placement_clearance as pc
HERE=Path(__file__).resolve().parent
RECEIPT=ROOT/'.runs/placement-pruning-controls-004/run/C/result.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    before=pc.inventory(RECEIPT.parent,with_directories=True,max_bytes=512*1024**2,max_files=16000,max_entries=32000)
    data=h.f.read_json(RECEIPT)
    source=Path(data['source']);source_before=pc.inventory(source.parent,with_directories=True)
    # Only the Git lookup in the exact current tool_manifest body is replaced.
    # All actual installed tool hashes, source/core hashes and lock checks run.
    # The historical receipt HEAD is a static control identity, NOT a current
    # Git verification; this review never launches Git or any native worker.
    node=ast.parse(inspect.getsource(p.tool_manifest));replacements=0
    for statement in node.body[0].body:
        if isinstance(statement,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='git_head' for t in statement.targets):
            statement.value=ast.Constant(data['tools']['git_head']);replacements+=1
    assert replacements==1
    namespace=dict(vars(p));exec(compile(ast.fix_missing_locations(node),'<tool-manifest-static-head-control>','exec'),namespace)
    static_manifest=namespace['tool_manifest'];old_session=h.validation_readback_session
    output=[]
    with patch.object(p,'tool_manifest',static_manifest),patch.object(p.subprocess,'run',side_effect=AssertionError('all subprocesses forbidden')):
        normal=h.review_copy(RECEIPT,HERE/'normal-review')
        selected=h.review_choice(HERE/'normal-review/review.json',HERE/'normal-choice','accept')
        output.append({'case':'actual_schema5_normal_control','ready':normal['status'],'disposition':selected['status'],'choice_recorded':selected['choice_recorded'],
                       'native_validation_performed':selected['native_validation_performed'],'routing_accepted':selected['routing_accepted'],'applied':selected['applied']})
        for kind,exception in [('keyboard_interrupt',KeyboardInterrupt),('rejected',p.Rejected)]:
            @contextlib.contextmanager
            def cleanup_fault():
                with old_session():yield
                raise exception('injected cache cleanup failure')
            target=HERE/('review-cleanup-'+kind);caught=None
            with patch.object(h,'validation_readback_session',cleanup_fault):
                try:h.review_copy(RECEIPT,target)
                except BaseException as exc:caught=type(exc).__name__+': '+str(exc)
            raw=h.f.read_json(target/'review.json')
            output.append({'case':'review_cleanup_'+kind,'raised':caught,'canonical_status':raw.get('status'),'native_validation_performed':raw.get('native_validation_performed'),
                           'invalidated_files':len(list(target.glob('invalidated-*')))})
            target=HERE/('choice-cleanup-'+kind);caught=None
            with patch.object(h,'validation_readback_session',cleanup_fault):
                try:h.review_choice(HERE/'normal-review/review.json',target,'accept')
                except BaseException as exc:caught=type(exc).__name__+': '+str(exc)
            raw=h.f.read_json(target/'choice.json')
            output.append({'case':'choice_cleanup_'+kind,'raised':caught,'canonical_status':raw.get('status'),'canonical_choice_recorded':raw.get('choice_recorded'),
                           'routing_accepted':raw.get('routing_accepted'),'native_validation_performed':raw.get('native_validation_performed'),
                           'invalidated_files':len(list(target.glob('invalidated-*')))})
    assert pc.inventory(RECEIPT.parent,with_directories=True,max_bytes=512*1024**2,max_files=16000,max_entries=32000)==before
    assert pc.inventory(source.parent,with_directories=True)==source_before
    result={'schema':1,'handoff_sha256':sha(ROOT/'autorouter/handoff.py'),'receipt':str(RECEIPT.relative_to(ROOT)),'receipt_sha256':sha(RECEIPT),
            'controls':output,'source_and_retained_evidence_unchanged':True,'native_executed':False,'subprocess_executed':False,
            'head_scope':'Only exact current manifest Git lookup replaced with historical receipt HEAD; actual tool/core/lock hashes checked; no current HEAD verification or native approval claim.'}
    (HERE/'probe-cleanup.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
