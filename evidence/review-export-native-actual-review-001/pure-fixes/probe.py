"""Bounded pure lifecycle probes, no native/Git/subprocess execution."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'scripts/qualify_review_export.py').is_file());sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h,review_export as e
from scripts import qualify_review_export as q
def rejected_intent(output,choice):
    output.mkdir();p.save_json(output/'choice.json',{'choice':choice})
    if choice=='reject':raise p.Rejected('deliberate rejection-intent persistence failure')
    return {'choice':choice,'routing_accepted':False}
def main():
    bindings={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('scripts/qualify_review_export.py','autorouter/floor_route.py','autorouter/review_export.py')};rows=[]
    project=HERE/'controller-seam-project';(project/'.runs/receipt').mkdir(parents=True);(project/'source').mkdir();(project/'source/board.kicad_pcb').write_text('(owned-source)')
    p.save_json(project/'.runs/receipt/result.json',{'schema':1,'source':str(project/'source/board.kicad_pcb'),'candidate_sha256':'seam-candidate-hash'})
    def review(receipt,output,render=False):output.mkdir();p.save_json(output/'review.json',{'status':'owned-pure-review'});return {'status':'owned-pure-review'}
    def choice(review,output,value):return rejected_intent(output,value)
    def export(choice,output,seconds):
        output.mkdir();p.save_json(output/'export.json',{'owned_mocked_export':True})
        return {'export_accepted':True,'project_file':str(output/'candidate.kicad_pro'),'candidate_sha256':'seam-candidate-hash','native_report_sha256':'seam-report-hash','native':{'opens':0,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':[]},'metrics':{},'steps':[]}
    controller=(ROOT/'scripts/qualify_review_export.py').read_bytes()
    with patch.object(c,'ROOT',project),patch.object(q,'CASES',(('owned_case','.runs/receipt/result.json',1,False),)),patch.object(p,'check_storage'),patch.object(p,'tool_manifest',return_value={'git_head':'a'*40}),patch.object(q.subprocess,'run',return_value=SimpleNamespace(stdout=controller)),patch.object(p,'check_result',return_value={'current':True}),patch.object(h,'review_copy',review),patch.object(h,'review_choice',choice),patch.object(e,'export',export),patch.object(e,'check_export',return_value={'current':True}):
        result=q.qualify(project/'.runs/qualification',run_native=True)
    rows.append({'case':'required_rejection_intent_failure','controller_status':result['status'],'controls_passed':result['controls_passed'],'entry_passed':result['cases'][0]['passed'],'entry_error':result['cases'][0].get('error'),
                 'scope':'Controller APIs and commit check explicitly mocked; one-case seam only, no native qualification or real report claim.'})
    root=HERE/'publisher-ownership';root.mkdir();out=root/'owned';out.mkdir();replacement=root/'preexisting';replacement.mkdir()
    (out/'result.json').write_text('owned-current');(out/'result.json.partial').write_text('owned-partial');(replacement/'result.json.partial').write_text('preexisting-must-preserve')
    before=e.witness(replacement);owner={};h.capture_destination(owner,out);rename=Path.rename;fired=False
    def swapped(path,target):
        nonlocal fired
        value=rename(path,target)
        if path==out/'result.json' and not fired:
            fired=True;rename(out,root/'retained-owned');rename(replacement,out)
        return value
    caught=None
    with patch.object(Path,'rename',swapped):
        try:f.publish(out,{'accepted':False},lambda:(_ for _ in ()).throw(p.Rejected('deliberate publication failure')),lambda:None,lambda:10,owned=lambda:h.owned_destination(owner))
        except BaseException as exc:caught=type(exc).__name__+': '+str(exc)
    rows.append({'case':'publisher_replacement_between_archival_renames','raised':caught,'replacement_inventory_unchanged':e.witness(out)==before,'replacement_current_partial_exists':(out/'result.json.partial').exists(),
                 'replacement_files':sorted(x.name for x in out.iterdir()),'scope':'Only owned regular scratch directories swapped; no live symlinks or original project files touched.'})
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in bindings.items())
    record={'schema':1,'sources':bindings,'source_stable_before_after':True,'controls':rows,'native_subprocess_JVM_Git_network_executed':False,'live_symlinks':False}
    (HERE/'probe.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
