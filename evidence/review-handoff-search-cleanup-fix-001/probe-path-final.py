"""Post-fix ownership guards, including normal and over-budget finalization."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/handoff.py').is_file());sys.path.insert(0,str(ROOT))
from autorouter import handoff as h,placement_clearance as pc
HERE=Path(__file__).resolve().parent
def main():
    source_sha=hashlib.sha256((ROOT/'autorouter/handoff.py').read_bytes()).hexdigest();rows=[]
    for replacement in ('symlink','real-directory'):
        root=HERE/('path-final-'+replacement);root.mkdir();preexisting=root/'preexisting-owned';preexisting.mkdir()
        h.save_json(preexisting/'review.json',{'status':'preexisting-owned-sentinel','must_preserve':True});(preexisting/'preview.html').write_text('preexisting-owned-preview')
        pre_before=pc.inventory(preexisting,with_directories=True)
        destination=root/'new-created-output';destination.mkdir();record={'schema':1,'status':'ready_for_manual_review','native_validation_performed':False};h.save_json(destination/'review.json',record)
        lifecycle={'completed':True,'record':record,'name':'review.json'};h.capture_destination(lifecycle,destination)
        destination.rename(root/'retained-created-output')
        if replacement=='symlink':destination.symlink_to(preexisting,target_is_directory=True);current=preexisting
        else:
            destination.mkdir();h.save_json(destination/'review.json',{'status':'new-directory-owned-sentinel','must_preserve':True});(destination/'preview.html').write_text('new-directory-owned-preview');current=destination
        current_before=pc.inventory(current,with_directories=True)
        for operation in ('failed-session','finish-within-cap','finish-over-cap'):
            caught=None
            try:
                if operation=='failed-session':h.failed_session(lifecycle,KeyboardInterrupt('owned path replacement control'))
                else:h.finish_session(record,destination,h.time.monotonic()-(31 if operation=='finish-over-cap' else 0),h.cpu_seconds(),'review.json',lifecycle)
            except BaseException as exc:caught=type(exc).__name__+': '+str(exc)
            rows.append({'replacement':replacement,'operation':operation,'raised':caught,
                         'preexisting_complete_inventory_unchanged':pc.inventory(preexisting,with_directories=True)==pre_before,
                         'replacement_complete_inventory_unchanged':pc.inventory(current,with_directories=True)==current_before,
                         'preview_preserved':(current/'preview.html').is_file(),'archives_in_replacement':len(list(current.glob('invalidated-*')))})
    assert source_sha==hashlib.sha256((ROOT/'autorouter/handoff.py').read_bytes()).hexdigest()
    assert all(x['raised'] is not None and x['preexisting_complete_inventory_unchanged'] and x['replacement_complete_inventory_unchanged'] and x['preview_preserved'] and x['archives_in_replacement']==0 for x in rows)
    result={'schema':1,'handoff_sha256':source_sha,'source_sha_stable_before_after':True,'controls':rows,'native_executed':False,'subprocess_executed':False,
            'scope':'Direct private lifecycle seams; only review-owned scratch touched; unchanged original source/raw receipt. Guard verification is finite sampling, not atomic protection against hostile concurrent filesystem writers.'}
    (HERE/'probe-path-final.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
