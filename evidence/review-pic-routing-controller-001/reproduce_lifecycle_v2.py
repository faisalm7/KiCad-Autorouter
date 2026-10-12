"""Run exact driver closures over actual files, with all native work mocked."""
import ast
import copy
import json
import shutil
import sys
from contextlib import nullcontext
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, sexpr as sx
from experiments.pic_mixed_transport_probe_v1 import driver


def callbacks(source,out):
    # Execute the actual small closure definitions; do not duplicate their logic
    # or invoke the controller, compiler, Git/native dispatch or engine.
    tree=ast.parse(source.read_text());function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='experiment')
    definitions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='pending_candidate']+[x for x in function.body if isinstance(x,ast.FunctionDef) and x.name in ('capture','stable','pending_candidate')]
    ns=dict(driver.__dict__,out=out,before=None,frozen={},mutable_files=set(),remaining=lambda:180)
    exec(compile(ast.fix_missing_locations(ast.Module(body=definitions,type_ignores=[])),str(source),'exec'),ns)
    return ns


def run(out,driver_source,use_pending,change_refill,after_seal=False):
    out.mkdir();source_dir=out/'source';source_dir.mkdir()
    original_path=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
    source=source_dir/original_path.name
    shutil.copyfile(original_path,source);shutil.copyfile(original_path.with_suffix('.kicad_pro'),source.with_suffix('.kicad_pro'))
    original=sx.read(source);source_hashes=p.tree_hash(source.parent)
    jobdir=out/'routing-native';jobdir.mkdir()
    cb=callbacks(driver_source,out);cb['capture']()
    candidate=jobdir/'candidate'/source.name;stages=[];error=None
    class Job:
        out=jobdir
        def drc(self,name,board,save=False):
            cb['stable']();stages.append(name)
            if save and change_refill:
                tree=sx.read(board);sx.children(tree,'zone')[0].append(['filled_polygon',['layer','"B.Cu"'],['pts',['xy','100','100'],['xy','101','100'],['xy','100','101']]])
                sx.write(board,tree)
            cb['capture']()
            return {'opens':0,'blocking':0,'warnings':0,'exclusions':0,'findings':[],'ignored_checks':[]}
        def native(self,name,*args):
            cb['stable']();stages.append(name)
            raise RuntimeError('next native stage reached without native execution')
    try:
        with cb['pending_candidate'](out,candidate,cb['frozen'],cb['mutable_files'],cb['capture']) if use_pending else nullcontext():
            shutil.copytree(source_dir,candidate.parent)
            task=copy.deepcopy(original);task[:]=[n for n in task if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
            for z in sx.children(task,'zone'):z[:]=[n for n in z if not isinstance(n,list) or not n or n[0] not in p.DERIVED_ZONE]
            sx.write(candidate,task);cb['capture']()
            p.validate_candidate(Job(),original,candidate,source_hashes,())
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    sealed=str(candidate.relative_to(out)) in cb['frozen']
    late=None
    if after_seal and candidate.exists():
        tree=sx.read(candidate);tree.append(['segment',['start','100','100'],['end','101','100'],['width','0.8'],['layer','"F.Cu"'],['net','"VCC"']]);sx.write(candidate,tree)
        try:cb['stable']();late='accepted'
        except Exception as exc:late=type(exc).__name__+': '+str(exc)
    return {'stages':stages,'error':error,'candidate_sealed':sealed,'after_seal_mutation':late,
            'immutable_equal':candidate.exists() and p.immutable(sx.read(candidate))==p.immutable(original),
            'source_unchanged':p.tree_hash(source.parent)==source_hashes}


def main():
    out=Path(sys.argv[1]).resolve();out.mkdir()
    old=Path(__file__).parent/'snapshot-001/driver.py';new=ROOT/'experiments/pic_mixed_transport_probe_v1/driver.py'
    before=p.sha(new)
    result={'schema':1,'source_sha256':before,'native_executed':False,'jvm_executed':False,
      'old_unchanged':run(out/'old-unchanged',old,False,False),
      'old_changed_refill':run(out/'old-changed',old,False,True),
      'fixed_changed_refill':run(out/'fixed-changed',new,True,True,True)}
    result['source_unchanged_during_test']=p.sha(new)==before
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
