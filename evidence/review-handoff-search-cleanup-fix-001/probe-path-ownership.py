"""Pure lifecycle directory replacement counterexample; owned scratch only."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/handoff.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import handoff as h,placement_clearance as pc
HERE=Path(__file__).resolve().parent
def main():
    start=hashlib.sha256((ROOT/'autorouter/handoff.py').read_bytes()).hexdigest()
    root=HERE/'path-ownership';root.mkdir();sentinel=root/'preexisting-owned';sentinel.mkdir()
    h.save_json(sentinel/'review.json',{'status':'preexisting-owned-sentinel','must_preserve':True});(sentinel/'preview.html').write_text('preexisting-owned-preview')
    before=pc.inventory(sentinel,with_directories=True)
    destination=root/'new-created-output';destination.mkdir();record={'schema':1,'status':'ready_for_manual_review','native_validation_performed':False};h.save_json(destination/'review.json',record)
    lifecycle={'created':True,'completed':True,'destination':destination,'record':record,'name':'review.json'}
    destination.rename(root/'retained-created-output');destination.symlink_to(sentinel,target_is_directory=True)
    caught=None
    try:h.failed_session(lifecycle,KeyboardInterrupt('owned path replacement control'))
    except BaseException as exc:caught=type(exc).__name__+': '+str(exc)
    after=pc.inventory(sentinel,with_directories=True)
    result={'schema':1,'handoff_sha256':start,'source_sha_stable_before_after':start==hashlib.sha256((ROOT/'autorouter/handoff.py').read_bytes()).hexdigest(),
            'case':'created_lifecycle_path_replaced_with_symlink_to_preexisting_owned_directory','raised':caught,
            'preexisting_complete_inventory_unchanged':before==after,'preexisting_current_record':h.f.read_json(sentinel/'review.json') if (sentinel/'review.json').exists() else None,
            'preexisting_preview_current_exists':(sentinel/'preview.html').exists(),'archives_in_preexisting_directory':sorted(x.name for x in sentinel.glob('invalidated-*')),
            'native_executed':False,'subprocess_executed':False,'scope':'Only review-owned scratch touched; original source/raw receipts untouched. Direct private lifecycle seam, not a full invocation/native result.'}
    (HERE/'probe-path-ownership.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
