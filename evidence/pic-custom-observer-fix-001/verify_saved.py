"""Read-only actual-evidence reproduction; emits only into this ignored folder."""
import hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE));sys.dont_write_bytecode=True
import driver as d
import mapping as fixed
from autorouter import placement_clearance as io

def load_old():
    spec=importlib.util.spec_from_file_location('original_pic_mapping',HERE/'original/mapping.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def inventories(paths):
    return {name:io.inventory(Path(path),max_bytes=32*1024**2,max_files=2000,max_entries=4000) for name,path in paths.items()}
def main():
    binding=json.loads((HERE/'bindings-before.json').read_text())
    before=inventories(binding['paths']);assert before==binding['inventories']
    run=ROOT/'.runs/pic-custom-observation-001';public=ROOT/'evidence/pic-custom-observation-001'
    raw=io.read_bytes(run/'native.dsn');native=d.read(run/'observation.json');custom=d.read(run/'custom-pads.json')
    evidence={name:hashlib.sha256(io.read_bytes(run/name)).hexdigest() for name in ('native.dsn','observation.json','custom-pads.json')}
    assert all(io.read_bytes(public/name)==io.read_bytes(run/name) for name in evidence)
    old=load_old();old_error=None
    try:old.dsn_correspondence(raw,native,custom['observation_before_export']['pads'])
    except ValueError as exc:old_error=str(exc)
    assert old_error=='invalid S-expression token'
    notes=fixed.source_notes(d.sx.read(d.SOURCE),d.read(d.SOURCE.with_suffix('.kicad_pro')))
    fixed.floor_identity(native,notes,d.read(d.SOURCE.with_suffix('.kicad_pro')))
    pads=fixed.custom_identity(custom,native,notes)
    result=fixed.dsn_correspondence(raw,native,pads)
    assert result['terminal_count']==236 and len(result['custom_pads'])==2
    assert result['geometry_qualified'] is False and result['routing_accepted'] is False
    after=inventories(binding['paths']);assert after==before
    summary={'passed':True,'scope':'Offline reanalysis of frozen native001 artifacts, not fresh native execution or geometry/routing qualification',
        'native_executed':False,'old_error':old_error,'cause':'Native bare quote declaration was fed to the board S-expression parser.',
        'dsn_bytes':len(raw),'evidence_sha256':evidence,'current_mapping_sha256':hashlib.sha256((HERE/'mapping.py').read_bytes()).hexdigest(),
        'before_after_original_inventories_equal':True,'terminal_count':result['terminal_count'],'custom_pad_count':len(result['custom_pads']),
        'native_pad_count':len(native['pads']),'native_route_count':len(native['routes']),'correspondence':result,
        'input_paths':binding['paths'],'input_inventories':before}
    (HERE/'saved-evidence-reproduction.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ('passed','native_executed','old_error','terminal_count','custom_pad_count','before_after_original_inventories_equal')}))
if __name__=='__main__':main()
