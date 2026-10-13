"""Actual-schema5 cleanup fix controls; all subprocess/native execution forbidden."""
from pathlib import Path
import ast,contextlib,copy,hashlib,inspect,json,signal,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/handoff.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import handoff as h,pipeline as p,placement_clearance as pc
HERE=Path(__file__).resolve().parent/'second-run';RECEIPT=ROOT/'.runs/placement-pruning-controls-004/run/C/result.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    source_sha_before=sha(ROOT/'autorouter/handoff.py')
    before=pc.inventory(RECEIPT.parent,with_directories=True,max_bytes=512*1024**2,max_files=16000,max_entries=32000)
    data=h.f.read_json(RECEIPT);source=Path(data['source']);source_before=pc.inventory(source.parent,with_directories=True)
    node=ast.parse(inspect.getsource(p.tool_manifest));replaced=0
    for statement in node.body[0].body:
        if isinstance(statement,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='git_head' for t in statement.targets):statement.value=ast.Constant(data['tools']['git_head']);replaced+=1
    assert replaced==1
    namespace=dict(vars(p));exec(compile(ast.fix_missing_locations(node),'<tool-manifest-static-head-control>','exec'),namespace)
    static_manifest=namespace['tool_manifest'];old_session=h.validation_readback_session;save=h.save_json;finish=h.finish_session;controls=[]
    signal_before={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
    def invoke(kind,target):
        return h.review_copy(RECEIPT,target) if kind=='review' else h.review_choice(HERE/'normal-review/review.json',target,'accept')
    def observe(kind,target,case,call):
        caught=None
        try:call()
        except BaseException as exc:caught=type(exc).__name__+': '+str(exc)
        path=target/('review.json' if kind=='review' else 'choice.json');raw=h.f.read_json(path) if path.exists() else {}
        controls.append({'case':case,'raised':caught,'current_exists':path.exists(),'canonical_status':raw.get('status'),'canonical_choice_recorded':raw.get('choice_recorded'),
                         'native_validation_performed':raw.get('native_validation_performed'),'routing_accepted':raw.get('routing_accepted'),
                         'invalidated_files':len(list(target.glob('invalidated-*'))),'handlers_restored':signal_before=={s:signal.getsignal(s) for s in signal_before}})
    with patch.object(p,'tool_manifest',static_manifest),patch.object(p.subprocess,'run',side_effect=AssertionError('all subprocesses forbidden')):
        normal=h.review_copy(RECEIPT,HERE/'normal-review');chosen=h.review_choice(HERE/'normal-review/review.json',HERE/'normal-choice','accept')
        controls.append({'case':'normal_actual_schema5','ready':normal['status'],'disposition':chosen['status'],'native_validation_performed':chosen['native_validation_performed'],'routing_accepted':chosen['routing_accepted'],'applied':chosen['applied']})
        for kind in ('review','choice'):
            for exception in (KeyboardInterrupt,p.Rejected):
                @contextlib.contextmanager
                def fault():
                    with old_session():yield
                    raise exception('injected cache cleanup failure')
                target=HERE/(kind+'-'+exception.__name__)
                with patch.object(h,'validation_readback_session',fault):observe(kind,target,kind+'_cleanup_'+exception.__name__,lambda:invoke(kind,target))
            target=HERE/(kind+'-existing');target.mkdir();(target/'keep').write_text('untouched');save(target/('review.json' if kind=='review' else 'choice.json'),{'status':'preexisting-owned-sentinel'})
            existing=pc.inventory(target,with_directories=True)
            observe(kind,target,kind+'_preexisting_preserved',lambda:invoke(kind,target))
            controls[-1]['complete_preexisting_inventory_unchanged']=existing==pc.inventory(target,with_directories=True)
            @contextlib.contextmanager
            def failure():
                with old_session():yield
                raise KeyboardInterrupt('injected cleanup cancellation')
            target=HERE/(kind+'-corrective-fails');positive=[None]
            def writing(path,record):
                if record.get('status') in ('ready_for_manual_review','disposition_recorded'):
                    positive[0]=copy.deepcopy(record);save(path,record)
                else:
                    # Strong negative: corrective writer republishes the old
                    # successful object, then fails; no current positive may survive.
                    save(path,positive[0]);save(path.with_name(path.name+'.partial'),positive[0]);raise OSError('injected corrective write failure')
            with patch.object(h,'validation_readback_session',failure),patch.object(h,'save_json',writing):
                observe(kind,target,kind+'_cleanup_corrective_write_failure',lambda:invoke(kind,target))
            controls[-1]['no_canonical_or_partial']=not any((target/name).exists() for name in (('review.json','review.json.partial') if kind=='review' else ('choice.json','choice.json.partial')))
            target=HERE/(kind+'-budget-corrective-fails');positive=[None]
            def overbudget(record,output,start,cpu_start,name):return finish(record,output,start-31,cpu_start,name)
            with patch.object(h,'finish_session',overbudget),patch.object(h,'save_json',writing):
                observe(kind,target,kind+'_budget_corrective_write_failure',lambda:invoke(kind,target))
            controls[-1]['no_canonical_or_partial']=not any((target/name).exists() for name in (('review.json','review.json.partial') if kind=='review' else ('choice.json','choice.json.partial')))
    assert pc.inventory(RECEIPT.parent,with_directories=True,max_bytes=512*1024**2,max_files=16000,max_entries=32000)==before
    assert pc.inventory(source.parent,with_directories=True)==source_before
    assert sha(ROOT/'autorouter/handoff.py')==source_sha_before, 'source changed during final review'
    result={'schema':1,'handoff_sha256':source_sha_before,'source_sha_stable_before_after':True,'receipt_sha256':sha(RECEIPT),'controls':controls,
            'source_and_retained_evidence_unchanged':True,'native_executed':False,'subprocess_executed':False,
            'head_scope':'Exact current tool_manifest body with only Git lookup replaced by stored historical receipt HEAD. Actual tools/core/lock hashed. No current HEAD verification or native approval claim.'}
    (HERE/'probe-001.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
